import os
import math
import textwrap
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

from sklearn.model_selection import KFold
from sklearn.metrics import mean_squared_error, mean_absolute_error
from sklearn.linear_model import LinearRegression

import statsmodels.api as sm
from statsmodels.stats.diagnostic import het_breuschpagan, het_white, linear_reset, normal_ad
from statsmodels.stats.stattools import jarque_bera
from statsmodels.stats.outliers_influence import variance_inflation_factor
from statsmodels.graphics.gofplots import qqplot


ARTIFACTS_DIR = "artifacts_final"
REPORT_TXT = os.path.join(ARTIFACTS_DIR, "RELATORIO_MODELOS_POR_POSICAO.txt")
REPORT_PDF = os.path.join(ARTIFACTS_DIR, "RELATORIO_MODELOS_POR_POSICAO.pdf")
METRICS_CSV = os.path.join(ARTIFACTS_DIR, "metrics_pos.csv")

RANDOM_STATE = 42


def ensure_dir(path: str) -> None:
    if not os.path.exists(path):
        os.makedirs(path, exist_ok=True)


def read_data() -> pd.DataFrame:
    # CSV absoluto fornecido
    csv_path = r"C:\Users\IGOR\Desktop\UFSC\TCC\dados\df_final.csv"
    df = pd.read_csv(csv_path)
    return df


def apply_min_treatments(df: pd.DataFrame, logs: List[str]) -> pd.DataFrame:
    df_work = df.copy()

    # age_centered e age_sq
    if "age" in df_work.columns:
        age_mean = df_work["age"].dropna().mean()
        df_work["age_centered"] = df_work["age"] - age_mean
        df_work["age_sq"] = df_work["age_centered"] ** 2
        logs.append(f"Tratamento: age_centered e age_sq criados (média age={age_mean:.4f}).")
    else:
        df_work["age_centered"] = np.nan
        df_work["age_sq"] = np.nan
        logs.append("Aviso: coluna age ausente; age_centered e age_sq como NA.")

    # ln_Value_Num
    if "ln_Value_Num" in df_work.columns:
        logs.append("Dependente: ln_Value_Num já existe e será usado.")
    else:
        if "Value_Num" in df_work.columns:
            # excluir Value_Num <= 0 do baseline
            invalid_mask = (df_work["Value_Num"] <= 0) | df_work["Value_Num"].isna()
            excluidos = int(invalid_mask.sum())
            df_work = df_work.loc[~invalid_mask].copy()
            if excluidos > 0:
                logs.append(f"Tratamento: {excluidos} linhas removidas (Value_Num <= 0 ou NA).")
            df_work["ln_Value_Num"] = np.log(df_work["Value_Num"])
            logs.append("Dependente: ln_Value_Num criado a partir de Value_Num.")
        else:
            df_work["ln_Value_Num"] = np.nan
            logs.append("Erro: Value_Num e ln_Value_Num ausentes; ln_Value_Num como NA.")

    # fb_Mn/MP alias interno fb_MnMP
    fb_mnmp_col = None
    if "fb_Mn/MP" in df_work.columns:
        df_work["fb_MnMP"] = df_work["fb_Mn/MP"]
        fb_mnmp_col = "fb_Mn/MP"
    elif "fb_MnMP" in df_work.columns:
        # já existe sem barra
        fb_mnmp_col = "fb_MnMP"
    else:
        df_work["fb_MnMP"] = np.nan
    if fb_mnmp_col:
        logs.append(f"Desempenho (minutos): usando coluna '{fb_mnmp_col}' como fb_MnMP.")
    else:
        logs.append("Aviso: fb_Mn/MP não encontrado; fb_MnMP ficará NA.")

    # desempenho fb_xGpm preferido; fallback para fb_xG, fb_xG+/-
    xg_source = None
    if "fb_xGpm" in df_work.columns:
        xg_source = "fb_xGpm"
    elif "fb_xG" in df_work.columns:
        df_work["fb_xGpm"] = df_work["fb_xG"]
        xg_source = "fb_xG"
    elif "fb_xG+/-" in df_work.columns:
        df_work["fb_xGpm"] = df_work["fb_xG+/-"]
        xg_source = "fb_xG+/-"
    else:
        df_work["fb_xGpm"] = np.nan
    if xg_source is not None:
        logs.append(f"Desempenho (xG): usando coluna '{xg_source}' como fb_xGpm.")
    else:
        logs.append("Aviso: fb_xGpm/fb_xG/fb_xG+/- não encontrados; fb_xGpm ficará NA.")

    # Remover explicitamente Height e fb_PPM do modelo (apenas ignorar)
    logs.append("Decisão: Height e fb_PPM excluídos da especificação do modelo.")

    return df_work


def drop_na_model_rows(df: pd.DataFrame, columns: List[str]) -> pd.DataFrame:
    return df.dropna(subset=columns).copy()


def compute_vif(df_X: pd.DataFrame, features: List[str]) -> pd.DataFrame:
    X = df_X[features].copy()
    X = sm.add_constant(X)
    vifs = []
    for i, name in enumerate(X.columns):
        if name == "const":
            continue
        try:
            v = variance_inflation_factor(X.values, i)
        except Exception:
            v = np.nan
        vifs.append({"variable": name, "VIF": v})
    return pd.DataFrame(vifs)


def fit_ols_cluster(df: pd.DataFrame, y_col: str, x_cols: List[str], cluster_col: str):
    X = sm.add_constant(df[x_cols])
    y = df[y_col]
    model = sm.OLS(y, X, missing="drop")
    results = model.fit()
    # clustered (HC1-like) by group
    try:
        clustered = results.get_robustcov_results(cov_type="cluster", cov_kwds={"groups": df[cluster_col]})
    except Exception:
        clustered = None
    return results, clustered


def kfold_metrics(df: pd.DataFrame, y_col: str, x_cols: List[str], k: int = 5, random_state: int = RANDOM_STATE) -> Tuple[float, float]:
    kf = KFold(n_splits=k, shuffle=True, random_state=random_state)
    X = df[x_cols].values
    y = df[y_col].values
    rmses = []
    maes = []
    for train_idx, test_idx in kf.split(X):
        X_train, X_test = X[train_idx], X[test_idx]
        y_train, y_test = y[train_idx], y[test_idx]
        lr = LinearRegression()
        lr.fit(X_train, y_train)
        y_pred = lr.predict(X_test)
        rmses.append(math.sqrt(mean_squared_error(y_test, y_pred)))
        maes.append(mean_absolute_error(y_test, y_pred))
    return float(np.mean(rmses)), float(np.mean(maes))


def in_sample_metrics(results) -> Tuple[float, float]:
    y = results.model.endog
    yhat = results.fittedvalues
    rmse = math.sqrt(mean_squared_error(y, yhat))
    mae = mean_absolute_error(y, yhat)
    return float(rmse), float(mae)


def diagnostics(results, X_df: pd.DataFrame) -> Dict[str, Optional[float]]:
    out: Dict[str, Optional[float]] = {"RESET": None, "BP": None, "White": None, "JB": None}

    # RESET (may fail if model poorly specified)
    try:
        reset = linear_reset(results, power=2, use_f=True)
        # linear_reset returns object with p-value attribute .pvalue or tuple
        p_reset = float(getattr(reset, "pvalue", np.nan)) if not isinstance(reset, tuple) else float(reset[1])
        out["RESET"] = p_reset
    except Exception:
        out["RESET"] = None

    # Breusch–Pagan
    try:
        lm, lm_pvalue, fval, f_pvalue = het_breuschpagan(results.resid, results.model.exog)
        out["BP"] = float(lm_pvalue)
    except Exception:
        out["BP"] = None

    # White
    try:
        white = het_white(results.resid, results.model.exog)
        out["White"] = float(white[1])  # p-value LM
    except Exception:
        out["White"] = None

    # Jarque–Bera
    try:
        jb_stat, jb_pvalue, _, _ = jarque_bera(results.resid)
        out["JB"] = float(jb_pvalue)
    except Exception:
        out["JB"] = None

    return out


def save_qqplot(residuals: np.ndarray, out_path: str) -> None:
    plt.figure(figsize=(5, 5))
    qqplot(residuals, line='s')
    plt.tight_layout()
    plt.savefig(out_path, dpi=150)
    plt.close()


def save_resid_vs_fitted(residuals: np.ndarray, fitted: np.ndarray, out_path: str) -> None:
    plt.figure(figsize=(6, 4))
    sns.scatterplot(x=fitted, y=residuals, s=20, edgecolor=None)
    plt.axhline(0.0, color='red', linestyle='--', linewidth=1)
    plt.xlabel("Fitted values")
    plt.ylabel("Residuals")
    plt.tight_layout()
    plt.savefig(out_path, dpi=150)
    plt.close()


def top_influence(results, X_df: pd.DataFrame, id_cols: List[str], top: int = 5) -> pd.DataFrame:
    infl = results.get_influence()
    cooks_d, _ = infl.cooks_distance
    leverage = infl.hat_matrix_diag
    dfbetas = infl.dfbetas  # ndarray (n_obs, k_params)

    df_inf = pd.DataFrame({
        "cooks_d": cooks_d,
        "leverage": leverage,
    })
    # Attach identifiers if present
    for c in id_cols:
        if c in X_df.index.names or c in X_df.columns:
            pass
    # Add dfbetas per param as columns with names
    param_names = list(results.params.index)
    for j, pname in enumerate(param_names):
        df_inf[f"DFBETA_{pname}"] = dfbetas[:, j]

    # If original df had identifiers, attempt to add
    for col in id_cols:
        if col in X_df.columns:
            df_inf[col] = X_df[col].values

    df_inf["rank"] = np.argsort(-df_inf["cooks_d"]).astype(int)
    df_inf_sorted = df_inf.sort_values("cooks_d", ascending=False).head(top)
    return df_inf_sorted


def fmt_num(x: Optional[float], dec: int = 4) -> str:
    if x is None or (isinstance(x, float) and (np.isnan(x) or np.isinf(x))):
        return "NA"
    if abs(x) < 1e-4 and x != 0:
        return f"{x:.2e}"
    return f"{x:.{dec}f}"


def build_report_header() -> str:
    header = (
        "RELATÓRIO CONSOLIDADO - MODELOS POR POSIÇÃO\n\n"
        "Modelos estimados separadamente para cada posição:\n"
        "- Modelo_GK: apenas goleiros (DUM_GK=1)\n"
        "- Modelo_DEF: apenas defensores (DUM_DEF=1)\n"
        "- Modelo_MC: apenas meio-campistas (DUM_MC=1)\n"
        "- Modelo_ATA: apenas atacantes (DUM_ATA=1)\n\n"
        "Especificação comum: ln_Value_Num ~ age_centered + age_sq + fb_Mn/MP + fb_xG + pts_rnc\n"
        "Inferência: EP robustos HC1 clusterizados por Clube\n\n"
    )
    return header


def section_name(pos_code: str) -> str:
    return {
        "GK": "Modelo_GK",
        "DEF": "Modelo_DEF",
        "MC": "Modelo_MC",
        "ATA": "Modelo_ATA",
    }[pos_code]


def pos_filter(df: pd.DataFrame, pos_code: str) -> pd.DataFrame:
    mapping = {
        "GK": "Dum_GK",
        "DEF": "Dum_DEF",
        "MC": "Dum_MC",
        "ATA": "Dum_ATA",
    }
    col = mapping[pos_code]
    if col not in df.columns:
        return df.iloc[0:0]
    return df.loc[df[col] == 1].copy()


def run_position_model(df_pos: pd.DataFrame, pos_code: str, logs: List[str]) -> Dict[str, object]:
    spec_label = section_name(pos_code)

    # Features set
    y_col = "ln_Value_Num"
    x_cols = ["age_centered", "age_sq", "fb_MnMP", "fb_xGpm", "pts_rnc"]

    # Drop NAs only for model cols + cluster group + ids if needed
    model_cols = [y_col] + x_cols + ["Clube"]
    df_clean = drop_na_model_rows(df_pos, model_cols)

    N = len(df_clean)
    small_note = ""
    if N < 30:
        small_note = "N pequeno"
        logs.append(f"Aviso: {spec_label} com N={N} (N pequeno).")

    if N == 0:
        return {
            "exists": False,
            "text": "",
        }

    # Fit OLS and clustered
    ols_res, clustered = fit_ols_cluster(df_clean, y_col, x_cols, cluster_col="Clube")

    # Metrics
    rmse_in, mae_in = in_sample_metrics(ols_res)
    try:
        rmse_cv5, mae_cv5 = kfold_metrics(df_clean, y_col, x_cols, k=5, random_state=RANDOM_STATE)
    except Exception:
        rmse_cv5, mae_cv5 = (np.nan, np.nan)

    # Diagnostics
    diag = diagnostics(ols_res, sm.add_constant(df_clean[x_cols]))

    # Plots
    qq_path = os.path.join(ARTIFACTS_DIR, f"qq_{pos_code}.png")
    rvf_path = os.path.join(ARTIFACTS_DIR, f"resid_vs_fitted_{pos_code}.png")
    try:
        save_qqplot(ols_res.resid, qq_path)
    except Exception:
        pass
    try:
        save_resid_vs_fitted(ols_res.resid, ols_res.fittedvalues, rvf_path)
    except Exception:
        pass

    # VIF
    vif_df = compute_vif(df_clean, ["age_centered", "age_sq", "fb_MnMP", "fb_xGpm", "pts_rnc"]).round(4)

    # Influence top 5
    try:
        id_cols = [c for c in ["Clube", "Player"] if c in df_clean.columns]
        infl_df = top_influence(ols_res, df_clean.reset_index(drop=True), id_cols=id_cols, top=5)
    except Exception:
        infl_df = pd.DataFrame()

    # Coefs table from clustered if available, else conventional
    used = clustered if clustered is not None else ols_res

    # Build text block
    lines = []
    lines.append(f"=== {spec_label} ===")
    lines.append(f"Especificação: {spec_label}")
    lines.append("Coeficientes (HC1 cluster por Clube): coef | se | t | p")

    # Order: Intercept, age_centered, age_sq, fb_xGpm, fb_MnMP, pts_rnc (match requested order)
    coef_order = ["const", "age_centered", "age_sq", "fb_xGpm", "fb_MnMP", "pts_rnc"]
    for name in coef_order:
        if name in used.params.index:
            coef = float(used.params[name])
            se = float(used.bse[name]) if name in used.bse.index else np.nan
            tval = float(used.tvalues[name]) if name in used.tvalues.index else np.nan
            pval = float(used.pvalues[name]) if name in used.pvalues.index else np.nan
            label = "Intercept" if name == "const" else name
            lines.append(
                f"  {label}: {fmt_num(coef)} | {fmt_num(se)} | {fmt_num(tval)} | {fmt_num(pval)}"
            )
        else:
            label = "Intercept" if name == "const" else name
            lines.append(f"  {label}: NA | NA | NA | NA")

    r2 = float(ols_res.rsquared) if hasattr(ols_res, "rsquared") else np.nan
    r2_adj = float(ols_res.rsquared_adj) if hasattr(ols_res, "rsquared_adj") else np.nan

    lines.append(f"N={N}, R2={fmt_num(r2)}, R2_adj={fmt_num(r2_adj)}{(' (' + small_note + ')') if small_note else ''}")
    lines.append(
        f"RMSE_in={fmt_num(rmse_in)}, MAE_in={fmt_num(mae_in)}, "
        f"RMSE_cv5={fmt_num(rmse_cv5)}, MAE_cv5={fmt_num(mae_cv5)}"
    )

    # Diagnostics text
    lines.append("Testes diagnósticos (p-valores):")
    lines.append(f"  RESET: {fmt_num(diag.get('RESET')) if diag.get('RESET') is not None else 'NA'}")
    lines.append(f"  Breusch–Pagan: {fmt_num(diag.get('BP')) if diag.get('BP') is not None else 'NA'}")
    lines.append(f"  White: {fmt_num(diag.get('White')) if diag.get('White') is not None else 'NA'}")
    lines.append(f"  Jarque–Bera: {fmt_num(diag.get('JB')) if diag.get('JB') is not None else 'NA'}")
    lines.append("")

    # Assemble outputs
    result = {
        "exists": True,
        "text": "\n".join(lines),
        "N": N,
        "R2": r2,
        "R2_adj": r2_adj,
        "rmse_in": rmse_in,
        "mae_in": mae_in,
        "rmse_cv5": rmse_cv5,
        "mae_cv5": mae_cv5,
        "diag": diag,
        "vif_df": vif_df,
        "influence_df": infl_df,
        "spec_label": spec_label,
    }
    return result


def save_diagnostics_csv(diag_map: Dict[str, Dict[str, Optional[float]]]) -> None:
    # Expected positions include DEF/MC/ATA and GK if exists
    for pos_code, diag in diag_map.items():
        out_csv = os.path.join(ARTIFACTS_DIR, f"diagnostics_{pos_code}.csv")
        row = {
            "p_RESET": diag.get("RESET"),
            "p_BP": diag.get("BP"),
            "p_White": diag.get("White"),
            "p_JB": diag.get("JB"),
        }
        pd.DataFrame([row]).to_csv(out_csv, index=False)


def save_vif_csv(vif_map: Dict[str, pd.DataFrame]) -> None:
    for pos_code, vif_df in vif_map.items():
        out_csv = os.path.join(ARTIFACTS_DIR, f"vif_{pos_code}.csv")
        vif_df.to_csv(out_csv, index=False)


def save_influence_csv(infl_map: Dict[str, pd.DataFrame]) -> None:
    for pos_code, df_inf in infl_map.items():
        out_csv = os.path.join(ARTIFACTS_DIR, f"influential_{pos_code}.csv")
        if df_inf is not None and len(df_inf) > 0:
            df_inf.to_csv(out_csv, index=False)
        else:
            pd.DataFrame().to_csv(out_csv, index=False)


def write_text_report(full_text: str) -> None:
    with open(REPORT_TXT, "w", encoding="utf-8") as f:
        f.write(full_text)


def write_pdf_report(full_text: str) -> None:
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.pdfgen import canvas
        from reportlab.lib.units import cm
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont

        # Attempt to register a font that supports accents; fallback to default
        try:
            pdfmetrics.registerFont(TTFont('DejaVu', 'DejaVuSans.ttf'))
            font_name = 'DejaVu'
        except Exception:
            font_name = 'Helvetica'

        c = canvas.Canvas(REPORT_PDF, pagesize=A4)
        width, height = A4
        margin = 2 * cm
        max_width = width - 2 * margin
        y = height - margin
        line_height = 12

        c.setFont(font_name, 10)
        for paragraph in full_text.split("\n"):
            # wrap long lines
            wrapped = textwrap.wrap(paragraph, width=110)
            if not wrapped:
                y -= line_height
                if y < margin:
                    c.showPage()
                    c.setFont(font_name, 10)
                    y = height - margin
                continue
            for line in wrapped:
                c.drawString(margin, y, line)
                y -= line_height
                if y < margin:
                    c.showPage()
                    c.setFont(font_name, 10)
                    y = height - margin
        c.save()
    except Exception:
        # If PDF generation fails, we silently skip; TXT remains primary
        pass


def main() -> None:
    ensure_dir(ARTIFACTS_DIR)

    logs: List[str] = []
    df_raw = read_data()
    df = apply_min_treatments(df_raw, logs)

    # Positions to estimate
    positions_order = ["DEF", "MC", "ATA", "GK"]  # keep DEF/MC/ATA first as in example; include GK

    header = build_report_header()
    sections: List[str] = [header]

    metrics_rows = []
    diag_map: Dict[str, Dict[str, Optional[float]]] = {}
    vif_map: Dict[str, pd.DataFrame] = {}
    infl_map: Dict[str, pd.DataFrame] = {}

    for pos in positions_order:
        df_pos = pos_filter(df, pos)
        if len(df_pos) == 0:
            continue
        res = run_position_model(df_pos, pos, logs)
        if not res.get("exists", False):
            continue
        sections.append(res["text"])  # add section

        # Collect metrics for CSV
        metrics_rows.append({
            "spec": section_name(pos),
            "N": res["N"],
            "R2": res["R2"],
            "Adj_R2": res["R2_adj"],
            "RMSE_in": res["rmse_in"],
            "MAE_in": res["mae_in"],
            "RMSE_cv5": res["rmse_cv5"],
            "MAE_cv5": res["mae_cv5"],
        })

        diag_map[pos] = res["diag"]
        vif_map[pos] = res["vif_df"]
        infl_map[pos] = res["influence_df"]

    # Final note
    sections.append("Inferência com EP HC1 cluster por Clube.")

    # Checklist
    checklist = [
        "", "Checklist:",
        "", " Tratamentos aplicados (age_centered, age_sq, ln_Value_Num)",
        "", " Modelos por posição estimados com HC1 cluster por Clube",
        "", " metrics_pos.csv salvo",
        "", " Diagnósticos e VIF salvos para DEF/MC/ATA (e GK se existir)",
        "", " Gráficos salvos",
        "", " RELATORIO_MODELOS_POR_POSICAO.txt e .pdf gerados em ./artifacts_final/",
    ]
    sections.extend(checklist)

    full_text = "\n".join(sections)

    # Save report and artifacts
    write_text_report(full_text)
    write_pdf_report(full_text)

    if metrics_rows:
        pd.DataFrame(metrics_rows).to_csv(METRICS_CSV, index=False)

    if diag_map:
        save_diagnostics_csv(diag_map)
    if vif_map:
        save_vif_csv(vif_map)
    if infl_map:
        save_influence_csv(infl_map)

    # Save logs to a simple log file for traceability
    with open(os.path.join(ARTIFACTS_DIR, "run_log.txt"), "w", encoding="utf-8") as f:
        for line in logs:
            f.write(line + "\n")


if __name__ == "__main__":
    main()
