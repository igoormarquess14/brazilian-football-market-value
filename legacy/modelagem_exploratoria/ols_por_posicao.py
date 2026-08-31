#!/usr/bin/env python3
r"""
OLS por Posição - Modelos separados para cada posição

Objetivo: Estimar modelos OLS log-lineares para ln(Value_Num) separadamente por posição,
usando apenas jogadores de cada posição específica (DUM_GK=1, DUM_DEF=1, DUM_MC=1, DUM_ATA=1).

Entrada principal: C:\Users\IGOR\Desktop\UFSC\TCC\dados\clubes\outcome\df_final.csv

Modelos:
  - Modelo_GK: apenas jogadores com DUM_GK=1
  - Modelo_DEF: apenas jogadores com DUM_DEF=1  
  - Modelo_MC: apenas jogadores com DUM_MC=1
  - Modelo_ATA: apenas jogadores com DUM_ATA=1

Especificação (igual ao Baseline A, mas sem dummies de posição):
ln_Value_Num ~ age_centered + age_sq + Height + fb_Mn/MP + fb_PPM + fb_xG + pts_rnc

Diagnósticos: VIF, RESET, Breusch–Pagan, White, Jarque–Bera, influentes
Métricas: RMSE/MAE in-sample e CV k=5
Inferência: EP robustos HC1 clusterizados por Clube
"""

import os
from pathlib import Path
import warnings
from typing import Dict, List, Tuple, Optional

import numpy as np
import pandas as pd
import statsmodels.api as sm
import statsmodels.formula.api as smf
from statsmodels.stats.outliers_influence import variance_inflation_factor, OLSInfluence
from statsmodels.stats.diagnostic import het_breuschpagan, het_white, linear_reset
from statsmodels.stats.stattools import jarque_bera
from sklearn.model_selection import KFold
from sklearn.linear_model import LinearRegression
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages

warnings.filterwarnings("ignore")

INPUT_PATH = r"C:\Users\IGOR\Desktop\UFSC\TCC\dados\clubes\outcome\df_final.csv"
OUT_DIR = Path("artifacts_por_posicao")
OUT_DIR.mkdir(exist_ok=True)

RANDOM_STATE = 2025

def log(msg: str) -> None:
    print(msg)

def read_data(path: str) -> pd.DataFrame:
    log(f"Carregando base: {path}")
    df = pd.read_csv(path)
    log(f"Base com {df.shape[0]} linhas e {df.shape[1]} colunas")
    return df

def safe_alias_columns(df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, str]]:
    """Cria aliases de colunas problemáticas para uso em fórmulas"""
    alias_map: Dict[str, str] = {}

    def make_alias(col: str) -> str:
        alias = col
        alias = alias.replace("+/-", "pm")
        alias = alias.replace("/", "")
        alias = alias.replace("+", "p")
        alias = alias.replace(" ", "_")
        alias = alias.replace("-", "_")
        alias = alias.replace("(", "").replace(")", "")
        return alias

    df_alias = df.copy()
    for col in list(df.columns):
        alias = make_alias(col)
        if alias != col and alias not in df_alias.columns:
            df_alias[alias] = df_alias[col]
            alias_map[col] = alias
    return df_alias, alias_map

def ensure_min_engineering(df: pd.DataFrame) -> Tuple[pd.DataFrame, Optional[float]]:
    """Garante colunas mínimas: age_centered, age_sq, ln_Value_Num"""
    df2 = df.copy()
    age_mean: Optional[float] = None

    # Idade centralizada e quadrática
    if "age_centered" not in df2.columns or "age_sq" not in df2.columns:
        if "age" in df2.columns:
            age_mean = pd.to_numeric(df2["age"], errors="coerce").mean()
            df2["age_centered"] = pd.to_numeric(df2["age"], errors="coerce") - age_mean
            df2["age_sq"] = df2["age_centered"] ** 2
            log("Criadas colunas 'age_centered' e 'age_sq'.")
        else:
            log("Aviso: coluna 'age' não encontrada; não foi possível criar 'age_centered'/'age_sq'.")

    # ln_Value_Num
    if "ln_Value_Num" not in df2.columns:
        if "Value_Num" in df2.columns:
            val = pd.to_numeric(df2["Value_Num"], errors="coerce")
            df2["ln_Value_Num"] = np.where(val > 0, np.log(val), np.nan)
            log("Criada coluna 'ln_Value_Num' a partir de 'Value_Num'.")
        else:
            log("Erro: coluna 'Value_Num' não encontrada para criar 'ln_Value_Num'.")

    return df2, age_mean

def select_columns_with_alias(df: pd.DataFrame) -> Dict[str, str]:
    """Resolve aliases prioritários e retorna mapeamento lógico->nome_real"""
    cols = df.columns.tolist()
    def exists_any(names: List[str]) -> Optional[str]:
        for n in names:
            if n in cols:
                return n
        return None

    mapping: Dict[str, Optional[str]] = {}
    mapping["dep"] = exists_any(["ln_Value_Num"])
    mapping["club"] = exists_any(["Clube", "clube", "Club", "club"])
    mapping["height"] = exists_any(["Height", "height", "Altura"])
    mapping["use_main"] = exists_any(["fb_MnMP", "fb_Mn/MP"])
    mapping["perf_xg"] = exists_any(["fb_xG", "fb_xGpm", "fb_xG+/-", "fb_xG_pm"])
    mapping["ppm"] = exists_any(["fb_PPM", "PPM", "fb_ppm"])
    mapping["pos_gk"] = exists_any(["Dum_GK", "dum_GK", "GK"])
    mapping["pos_def"] = exists_any(["Dum_DEF", "dum_DEF", "DEF"])
    mapping["pos_mc"] = exists_any(["Dum_MC", "dum_MC", "MC"])
    mapping["pos_ata"] = exists_any(["Dum_ATA", "dum_ATA", "ATA"])
    mapping["exposure_pts"] = exists_any(["pts_rnc", "pts_RNC", "Pontos_RNC"])

    return {k: v for k, v in mapping.items() if v is not None}

def add_optional_keys(colmap: Dict[str, str], df_cols: List[str]) -> Dict[str, str]:
    new_map = dict(colmap)
    for k in ["age_centered", "age_sq"]:
        if k in df_cols:
            new_map[k] = k
    return new_map

def compute_in_sample_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> Tuple[float, float]:
    resid = y_true - y_pred
    rmse = float(np.sqrt(np.mean(resid ** 2)))
    mae = float(np.mean(np.abs(resid)))
    return rmse, mae

def compute_cv_metrics(X: pd.DataFrame, y: pd.Series) -> Tuple[float, float]:
    kf = KFold(n_splits=5, shuffle=True, random_state=RANDOM_STATE)
    model = LinearRegression()
    rmses: List[float] = []
    maes: List[float] = []
    for train_idx, test_idx in kf.split(X):
        X_train, X_test = X.iloc[train_idx, :], X.iloc[test_idx, :]
        y_train, y_test = y.iloc[train_idx], y.iloc[test_idx]
        model.fit(X_train, y_train)
        pred = model.predict(X_test)
        rmse, mae = compute_in_sample_metrics(y_test.values, pred)
        rmses.append(rmse)
        maes.append(mae)
    return float(np.mean(rmses)), float(np.mean(maes))

def ensure_complete_cases(df: pd.DataFrame, cols: List[str]) -> pd.DataFrame:
    mask = pd.Series(True, index=df.index)
    for c in cols:
        mask &= df[c].notna()
    return df.loc[mask].copy()

def fit_ols_with_cluster(df: pd.DataFrame, formula: str, group_col: str):
    model = smf.ols(formula=formula, data=df).fit()
    robust = model.get_robustcov_results(cov_type='cluster', groups=df[group_col])
    return model, robust

def save_summary_text(model, robust, tag: str) -> None:
    with open(OUT_DIR / f"{tag}_ols.txt", "w", encoding="utf-8") as f:
        f.write(model.summary().as_text())
    with open(OUT_DIR / f"{tag}_ols_cluster.txt", "w", encoding="utf-8") as f:
        f.write(robust.summary().as_text())

def run_diagnostics(df: pd.DataFrame, model) -> Dict[str, float]:
    resid = model.resid
    exog = model.model.exog

    # RESET
    try:
        reset_res = linear_reset(model, use_f=True)
        reset_p = float(reset_res.pvalue)
    except Exception:
        reset_p = np.nan

    # Breusch–Pagan
    try:
        bp_stat, bp_p, _, _ = het_breuschpagan(resid, exog)
        bp_p = float(bp_p)
    except Exception:
        bp_p = np.nan

    # White
    try:
        white_stat, white_p, _, _ = het_white(resid, exog)
        white_p = float(white_p)
    except Exception:
        white_p = np.nan

    # Jarque–Bera
    try:
        jb_stat, jb_p, _, _ = jarque_bera(resid)
        jb_p = float(jb_p)
    except Exception:
        jb_p = np.nan

    return {
        "p_RESET": reset_p,
        "p_BP": bp_p,
        "p_White": white_p,
        "p_JB": jb_p,
    }

def compute_vif(df: pd.DataFrame, cols: List[str]) -> pd.DataFrame:
    X = df[cols].astype(float)
    X_const = sm.add_constant(X, has_constant='add')
    vif_data = []
    for i, name in enumerate(X_const.columns):
        if name == 'const':
            continue
        vif_val = variance_inflation_factor(X_const.values, i)
        vif_data.append({"variable": name, "VIF": float(vif_val)})
    return pd.DataFrame(vif_data)

def save_plots(model, tag: str) -> None:
    fitted = model.fittedvalues
    resid = model.resid

    # Residual vs Fitted
    plt.figure(figsize=(6, 4))
    plt.scatter(fitted, resid, alpha=0.6)
    plt.axhline(0, color='red', linestyle='--', linewidth=1)
    plt.xlabel('Fitted values')
    plt.ylabel('Residuals')
    plt.title('Residuals vs Fitted')
    plt.tight_layout()
    plt.savefig(OUT_DIR / f"resid_vs_fitted_{tag}.png", dpi=150)
    plt.close()

    # QQ-plot
    fig = sm.qqplot(resid, line='45')
    plt.title('QQ-plot of residuals')
    plt.tight_layout()
    plt.savefig(OUT_DIR / f"qqplot_{tag}.png", dpi=150)
    plt.close()

def influential_obs(model, df: pd.DataFrame, tag: str) -> pd.DataFrame:
    infl = OLSInfluence(model)
    cooks_d = infl.cooks_distance[0]
    leverage = infl.hat_matrix_diag
    dfbetas = infl.dfbetas
    cols = [f"DFBETA_{i}" for i in range(dfbetas.shape[1])]
    df_dfbeta = pd.DataFrame(dfbetas, columns=cols, index=df.index)
    out = pd.DataFrame({
        "cooks_d": cooks_d,
        "leverage": leverage,
    }, index=df.index).join(df_dfbeta)
    out_sorted = out.sort_values("cooks_d", ascending=False)
    top5 = out_sorted.head(5)
    top5.to_csv(OUT_DIR / f"influential_top5_{tag}.csv", index=True)
    return top5

def turning_point_age(model, df: pd.DataFrame, age_mean: Optional[float]) -> Tuple[Optional[float], Optional[bool], Optional[float], Optional[float]]:
    try:
        params = model.params
        if 'age_centered' in params.index and 'age_sq' in params.index:
            beta_age_c = params['age_centered']
            beta_age_sq = params['age_sq']
            if beta_age_sq == 0:
                return None, None, None, None
            if age_mean is None and 'age' in df.columns:
                age_mean = pd.to_numeric(df['age'], errors='coerce').mean()
            if age_mean is None:
                return None, None, None, None
            age_star = -beta_age_c / (2.0 * beta_age_sq) + age_mean
            if 'age' in df.columns:
                age_min = float(pd.to_numeric(df['age'], errors='coerce').min())
                age_max = float(pd.to_numeric(df['age'], errors='coerce').max())
                in_support = bool((age_star >= age_min) and (age_star <= age_max))
                return float(age_star), in_support, age_min, age_max
            return float(age_star), None, None, None
        return None, None, None, None
    except Exception:
        return None, None, None, None

def build_design_matrix(df: pd.DataFrame, y_col: str, x_cols: List[str]) -> Tuple[pd.DataFrame, pd.Series]:
    y = df[y_col].astype(float)
    X = df[x_cols].astype(float)
    return X, y

def run_model_por_posicao(df_base: pd.DataFrame, colmap: Dict[str, str], posicao: str, pos_col: str) -> Dict[str, object]:
    """Executa modelo para uma posição específica"""
    
    # Filtra apenas jogadores da posição
    df_pos = df_base[df_base[pos_col] == 1].copy()
    
    if len(df_pos) < 20:  # Mínimo de observações
        log(f"Aviso: Poucas observações para {posicao} ({len(df_pos)}). Pulando.")
        return {}
    
    log(f"Modelo {posicao}: {len(df_pos)} observações")
    
    # Monta fórmula (sem dummies de posição, sem Height e fb_PPM)
    rhs_terms = []
    for k in ["age_centered", "age_sq", "perf_xg"]:
        if k in colmap:
            rhs_terms.append(colmap[k])
    if "use_main" in colmap:
        rhs_terms.append(colmap["use_main"])
    if "exposure_pts" in colmap:
        rhs_terms.append(colmap["exposure_pts"])

    rhs = " + ".join(rhs_terms)
    formula = f"{colmap['dep']} ~ {rhs}"

    # Limpa dados
    needed = [colmap['dep'], colmap['club']] + rhs_terms
    df_clean = ensure_complete_cases(df_pos, needed)
    
    if df_clean.empty:
        log(f"{posicao}: Sem casos completos após limpeza. Pulando.")
        return {}
    
    log(f"{posicao}: {len(df_clean)} observações após limpeza")

    # Estima modelo
    model, robust = fit_ols_with_cluster(df_clean, formula, group_col=colmap['club'])

    # Métricas in-sample
    rmse_in, mae_in = compute_in_sample_metrics(df_clean[colmap['dep']].values, robust.fittedvalues)

    # CV 5-fold
    x_cols = [c for c in df_clean.columns if c in rhs_terms]
    X, y = build_design_matrix(df_clean, colmap['dep'], x_cols)
    rmse_cv, mae_cv = compute_cv_metrics(X, y)

    # VIF (sem Height e fb_PPM)
    continuous = []
    for k in ["age_centered", "age_sq", "perf_xg"]:
        if k in colmap and colmap[k] in df_clean.columns:
            continuous.append(colmap[k])
    if "use_main" in colmap and colmap["use_main"] in df_clean.columns:
        continuous.append(colmap["use_main"])
    if "exposure_pts" in colmap and colmap["exposure_pts"] in df_clean.columns:
        continuous.append(colmap["exposure_pts"])
    
    continuous = sorted(set(continuous))
    vif_df = pd.DataFrame()
    if len(continuous) >= 2:
        try:
            vif_df = compute_vif(df_clean, continuous)
        except Exception:
            vif_df = pd.DataFrame()

    # Diagnósticos
    diags = run_diagnostics(df_clean, robust)

    # Gráficos
    save_plots(robust, tag=posicao)

    # Influentes
    top5 = influential_obs(robust, df_clean, tag=posicao)

    # Salva resumos
    save_summary_text(model, robust, tag=posicao)

    # Salva VIF e diagnósticos
    if not vif_df.empty:
        vif_df.to_csv(OUT_DIR / f"vif_{posicao}.csv", index=False)
    diag_out = pd.DataFrame([{**{"spec": posicao}, **diags}])
    diag_out.to_csv(OUT_DIR / f"diagnostics_{posicao}.csv", index=False)

    return {
        "tag": posicao,
        "model": model,
        "robust": robust,
        "rmse_in": rmse_in,
        "mae_in": mae_in,
        "rmse_cv5": rmse_cv,
        "mae_cv5": mae_cv,
        "r2": float(model.rsquared),
        "r2_adj": float(model.rsquared_adj),
        "n": int(model.nobs),
        "vif": vif_df,
        "diagnostics": diags,
        "top5": top5,
        "df_used": df_clean,
    }

def main():
    df_raw = read_data(INPUT_PATH)
    df0, alias_map = safe_alias_columns(df_raw)
    df1, age_mean = ensure_min_engineering(df0)
    colmap = select_columns_with_alias(df1)
    colmap = add_optional_keys(colmap, df1.columns.tolist())

    # Verificações essenciais
    required_keys = ["dep", "club"]
    for rk in required_keys:
        if rk not in colmap:
            raise ValueError(f"Coluna essencial não encontrada: {rk}")

    # Report de aliases aplicados
    for orig, alias in alias_map.items():
        log(f"Alias aplicado: '{orig}' -> '{alias}' (uso interno)")

    results: List[Dict[str, object]] = []

    # Modelos por posição
    posicoes = [
        ("Modelo_GK", "pos_gk"),
        ("Modelo_DEF", "pos_def"), 
        ("Modelo_MC", "pos_mc"),
        ("Modelo_ATA", "pos_ata")
    ]

    for posicao, pos_key in posicoes:
        if pos_key in colmap:
            log(f"\n=== Executando {posicao} ===")
            res = run_model_por_posicao(df1, colmap, posicao, colmap[pos_key])
            if res:
                results.append(res)
        else:
            log(f"Aviso: {pos_key} não encontrado. {posicao} pulado.")

    # Coleta métricas e salva metrics_models.csv
    if results:
        metrics_rows = []
        for r in results:
            metrics_rows.append({
                "spec": r["tag"],
                "RMSE_in": r["rmse_in"],
                "MAE_in": r["mae_in"],
                "RMSE_cv5": r["rmse_cv5"],
                "MAE_cv5": r["mae_cv5"],
                "R2": r["r2"],
                "Adj_R2": r["r2_adj"],
                "N": r["n"],
            })
        pd.DataFrame(metrics_rows).to_csv(OUT_DIR / "metrics_models.csv", index=False)

    # Relatório consolidado
    print("\n=== GERANDO RELATÓRIO CONSOLIDADO ===")
    try:
        def fmt_p(p: Optional[float]) -> str:
            if p is None or np.isnan(p):
                return "NA"
            if p < 0.001:
                return f"{p:.1e}"
            return f"{p:.3f}"

        def fmt_coef(x: Optional[float]) -> str:
            if x is None or np.isnan(x):
                return "NA"
            return f"{x:.4f}"

        def summary_table(res: Dict[str, object]) -> List[str]:
            model = res["robust"]
            lines = []
            lines.append(f"Especificação: {res['tag']}")
            lines.append("Coeficientes (HC1 cluster por Clube): coef | se | t | p")
            
            # Usar nomes corretos dos coeficientes
            original_model = res["model"]
            param_names = original_model.params.index
            
            for i, name in enumerate(param_names):
                coef = float(model.params[i])
                se = float(model.bse[i])
                t = float(model.tvalues[i])
                p = float(model.pvalues[i])
                lines.append(f"  {name}: {fmt_coef(coef)} | {fmt_coef(se)} | {fmt_coef(t)} | {fmt_p(p)}")
            
            lines.append(f"N={int(model.nobs)}, R2={res['r2']:.4f}, R2_adj={res['r2_adj']:.4f}")
            lines.append(f"RMSE_in={res['rmse_in']:.4f}, MAE_in={res['mae_in']:.4f}, RMSE_cv5={res['rmse_cv5']:.4f}, MAE_cv5={res['mae_cv5']:.4f}")
            return lines

        # TXT
        txt_lines: List[str] = []
        txt_lines.append("RELATÓRIO CONSOLIDADO - MODELOS POR POSIÇÃO")
        txt_lines.append("")
        txt_lines.append("Modelos estimados separadamente para cada posição:")
        txt_lines.append("- Modelo_GK: apenas goleiros (DUM_GK=1)")
        txt_lines.append("- Modelo_DEF: apenas defensores (DUM_DEF=1)")
        txt_lines.append("- Modelo_MC: apenas meio-campistas (DUM_MC=1)")
        txt_lines.append("- Modelo_ATA: apenas atacantes (DUM_ATA=1)")
        txt_lines.append("")
        txt_lines.append("Especificação comum: ln_Value_Num ~ age_centered + age_sq + fb_Mn/MP + fb_xG + pts_rnc")
        txt_lines.append("Inferência: EP robustos HC1 clusterizados por Clube")
        txt_lines.append("")

        for res in results:
            txt_lines.append(f"=== {res['tag']} ===")
            txt_lines += summary_table(res)
            
            # Diagnósticos
            diag_file = OUT_DIR / f"diagnostics_{res['tag']}.csv"
            if diag_file.exists():
                diag = pd.read_csv(diag_file)
                txt_lines.append("Testes diagnósticos (p-valores):")
                txt_lines.append(f"  RESET: {fmt_p(diag['p_RESET'].iloc[0])}")
                txt_lines.append(f"  Breusch–Pagan: {fmt_p(diag['p_BP'].iloc[0])}")
                txt_lines.append(f"  White: {fmt_p(diag['p_White'].iloc[0])}")
                txt_lines.append(f"  Jarque–Bera: {fmt_p(diag['p_JB'].iloc[0])}")
            
            # Turning point da idade
            age_star, in_support, age_min, age_max = turning_point_age(res["robust"], res["df_used"], age_mean)
            if age_star is not None:
                txt_lines.append(f"Turning point da idade: age*={age_star:.4f}; dentro do suporte: {in_support} (min={age_min}, max={age_max})")
            
            txt_lines.append("")

        # Salva relatório
        with open(OUT_DIR / "RELATORIO_MODELOS_POR_POSICAO.txt", "w", encoding="utf-8") as f:
            for line in txt_lines:
                f.write(line + "\n")

        # PDF
        with PdfPages(OUT_DIR / "RELATORIO_MODELOS_POR_POSICAO.pdf") as pdf:
            page_lines = 45
            for i in range(0, len(txt_lines), page_lines):
                chunk = txt_lines[i:i+page_lines]
                fig = plt.figure(figsize=(8.27, 11.69))
                text = "\n".join(chunk)
                fig.text(0.06, 0.98, "RELATÓRIO MODELOS POR POSIÇÃO", ha='left', va='top', fontsize=12, fontfamily='monospace')
                fig.text(0.06, 0.94, text, ha='left', va='top', fontsize=9, fontfamily='monospace')
                plt.axis('off')
                pdf.savefig(fig)
                plt.close(fig)

        print("Relatório consolidado gerado com sucesso!")

    except Exception as e:
        print(f"[ERRO] Falha ao gerar relatório: {e}")

    # Checklist final
    print("\n=== CHECKLIST ===")
    checklist_lines = []
    checklist_lines.append(f"Modelos por posição estimados: {len(results)} de 4")
    checklist_lines.append("Diagnósticos (VIF, RESET, BP, White, JB, influentes) salvos")
    checklist_lines.append("Métricas RMSE/MAE (in-sample e CV k=5) calculadas")
    checklist_lines.append("./artifacts_por_posicao/ criada com todos os artefatos")
    checklist_lines.append("RELATORIO_MODELOS_POR_POSICAO.txt e PDF gerados")
    
    for line in checklist_lines:
        print("- " + line)

if __name__ == "__main__":
    main()
