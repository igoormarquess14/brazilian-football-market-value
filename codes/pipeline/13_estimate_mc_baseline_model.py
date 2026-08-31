#!/usr/bin/env python3
"""
Reproduces in Python (statsmodels) the single econometric model published in
the thesis: OLS of ln(MarketValue) for the midfielder subset (N=87), per
Table 7 and Appendix A.

Specification confirmed in session.inp (Gretl session, 2025-10-16):
    ols ln_Value_Num 0 age_centered age_sq fb_xG fb_MnMP
No --robust: classical (non-robust) standard errors, not HC1.

Idempotent: does not modify the input data, only reads dados/df_mc.csv and writes to outputs/.
"""

from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_PATH = PROJECT_ROOT / "dados" / "df_mc.csv"
OUTPUT_DIR = PROJECT_ROOT / "outputs"
OUTPUT_PATH = OUTPUT_DIR / "mc_baseline_model.txt"

# Reference values: Table 7 and Appendix A of the thesis (Gretl, 2025-10-16).
REFERENCE = {
    "const":        {"coef": 14.3035,     "se": 0.336761,   "n_test": 42.47,  "p": 0.0000},
    "age_centered": {"coef": -0.0875236,  "se": 0.0244138,  "n_test": -3.585, "p": 0.0006},
    "age_sq":       {"coef": -0.0126963,  "se": 0.00456389, "n_test": -2.782, "p": 0.0067},
    "fb_xG+/-":     {"coef": 0.0406437,   "se": 0.0197692,  "n_test": 2.056,  "p": 0.0430},
    "fb_Mn/MP":     {"coef": 0.00659699,  "se": 0.00527208, "n_test": 1.251,  "p": 0.2144},
}
REFERENCE_N = 87
REFERENCE_R2 = 0.226538
REFERENCE_R2_ADJ = 0.188808
REFERENCE_F = 6.004195
REFERENCE_F_PVALUE = 0.000274

# CLAUDE.md tolerances: N identical; coef rel. err < 1e-4; SE rel. err < 1e-3;
# R2/adjusted R2 equal to the 4th decimal.
TOL_COEF = 1e-4
TOL_SE = 1e-3
TOL_R2_DECIMALS = 4


def rel_err(estimado: float, referencia: float) -> float:
    return abs(estimado - referencia) / abs(referencia)


def main() -> None:
    OUTPUT_DIR.mkdir(exist_ok=True)

    df = pd.read_csv(DATA_PATH)

    vars_do_modelo = ["age_centered", "age_sq", "fb_xG+/-", "fb_Mn/MP", "ln_Value_Num"]
    df = df.dropna(subset=vars_do_modelo)

    df["fb_xG+/-"] = pd.to_numeric(df["fb_xG+/-"], errors="raise")

    X = sm.add_constant(df[["age_centered", "age_sq", "fb_xG+/-", "fb_Mn/MP"]])
    y = df["ln_Value_Num"]
    modelo = sm.OLS(y, X).fit()  # default cov_type = "nonrobust", matching Gretl without --robust

    linhas = []
    linhas.append(f"Estimated N: {int(modelo.nobs)} | Thesis N: {REFERENCE_N}")
    linhas.append(f"N identical: {'OK' if int(modelo.nobs) == REFERENCE_N else 'FAIL'}")
    linhas.append("")
    linhas.append(f"{'Variable':<15}{'Python coef.':>15}{'Table 7 coef.':>16}{'Rel. error':>12}{'Python SE':>13}{'Table 7 SE':>14}{'Rel. error':>12}")

    todas_ok = True
    for nome, ref in REFERENCE.items():
        coef = modelo.params[nome]
        se = modelo.bse[nome]
        err_coef = rel_err(coef, ref["coef"])
        err_se = rel_err(se, ref["se"])
        ok = err_coef < TOL_COEF and err_se < TOL_SE
        todas_ok = todas_ok and ok
        linhas.append(
            f"{nome:<15}{coef:>15.7f}{ref['coef']:>16.7f}{err_coef:>12.2e}"
            f"{se:>13.7f}{ref['se']:>14.7f}{err_se:>12.2e}"
        )

    linhas.append("")
    r2_ok = round(modelo.rsquared, TOL_R2_DECIMALS) == round(REFERENCE_R2, TOL_R2_DECIMALS)
    r2adj_ok = round(modelo.rsquared_adj, TOL_R2_DECIMALS) == round(REFERENCE_R2_ADJ, TOL_R2_DECIMALS)
    linhas.append(f"Python R2: {modelo.rsquared:.6f} | Thesis R2: {REFERENCE_R2:.6f} | {'OK' if r2_ok else 'FAIL'}")
    linhas.append(f"Python adjusted R2: {modelo.rsquared_adj:.6f} | Thesis adjusted R2: {REFERENCE_R2_ADJ:.6f} | {'OK' if r2adj_ok else 'FAIL'}")
    linhas.append(f"Python F: {modelo.fvalue:.6f} | Thesis F: {REFERENCE_F:.6f}")
    linhas.append(f"Python p(F): {modelo.f_pvalue:.6f} | Thesis p(F): {REFERENCE_F_PVALUE:.6f}")

    todas_ok = todas_ok and r2_ok and r2adj_ok and int(modelo.nobs) == REFERENCE_N

    linhas.append("")
    linhas.append(f"REPRODUCTION: {'OK — within CLAUDE.md tolerance' if todas_ok else 'FAIL — outside CLAUDE.md tolerance'}")
    linhas.append("")
    linhas.append("=" * 78)
    linhas.append("Full statsmodels output:")
    linhas.append("=" * 78)
    linhas.append(str(modelo.summary()))

    relatorio = "\n".join(linhas)
    print(relatorio)
    OUTPUT_PATH.write_text(relatorio, encoding="utf-8")
    print(f"\nReport saved to: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
