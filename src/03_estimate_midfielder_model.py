#!/usr/bin/env python3
"""
Re-estimates in Python (statsmodels) the econometric model published in the
thesis: OLS of ln(MarketValue) on the midfielder subset (N=87), Table 7 and
Appendix A. Compares every coefficient, standard error and fit statistic
against the values printed in the thesis.

Specification, as recorded in thesis/gretl_session.inp (2025-10-16):
    ols ln_Value_Num 0 age_centered age_sq fb_xG fb_MnMP
No --robust flag: classical (non-robust) standard errors.

Reproduction criteria, fixed before running:
- N identical
- coefficient relative error < 1e-4
- standard error relative error < 1e-3
- R2 and adjusted R2 equal to the 4th decimal

Input:  data/df_mc.csv
Output: outputs/midfielder_model.txt
"""

from pathlib import Path

import pandas as pd
import statsmodels.api as sm

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = PROJECT_ROOT / "data" / "df_mc.csv"
OUTPUT_PATH = PROJECT_ROOT / "outputs" / "midfielder_model.txt"

# Table 7 and Appendix A of the thesis (Gretl, 2025-10-16).
REFERENCE = {
    "const":        {"coef": 14.3035,    "se": 0.336761},
    "age_centered": {"coef": -0.0875236, "se": 0.0244138},
    "age_sq":       {"coef": -0.0126963, "se": 0.00456389},
    "fb_xG+/-":     {"coef": 0.0406437,  "se": 0.0197692},
    "fb_Mn/MP":     {"coef": 0.00659699, "se": 0.00527208},
}
REFERENCE_N = 87
REFERENCE_R2 = 0.226538
REFERENCE_R2_ADJ = 0.188808
REFERENCE_F = 6.004195
REFERENCE_F_PVALUE = 0.000274

TOL_COEF = 1e-4
TOL_SE = 1e-3
TOL_R2_DECIMALS = 4

REGRESSORS = ["age_centered", "age_sq", "fb_xG+/-", "fb_Mn/MP"]
DEPENDENT = "ln_Value_Num"


def rel_err(estimate: float, reference: float) -> float:
    return abs(estimate - reference) / abs(reference)


def main() -> None:
    df = pd.read_csv(DATA_PATH)
    df = df.dropna(subset=REGRESSORS + [DEPENDENT])
    df["fb_xG+/-"] = pd.to_numeric(df["fb_xG+/-"], errors="raise")

    X = sm.add_constant(df[REGRESSORS])
    y = df[DEPENDENT]
    model = sm.OLS(y, X).fit()  # nonrobust covariance, same as Gretl without --robust

    n_ok = int(model.nobs) == REFERENCE_N
    lines = [
        f"Estimated N: {int(model.nobs)} | Thesis N: {REFERENCE_N}",
        f"N identical: {'OK' if n_ok else 'FAIL'}",
        "",
        f"{'Variable':<15}{'Python coef.':>15}{'Table 7 coef.':>16}{'Rel. error':>12}"
        f"{'Python SE':>13}{'Table 7 SE':>14}{'Rel. error':>12}",
    ]

    all_ok = n_ok
    for name, ref in REFERENCE.items():
        coef = model.params[name]
        se = model.bse[name]
        err_coef = rel_err(coef, ref["coef"])
        err_se = rel_err(se, ref["se"])
        all_ok = all_ok and err_coef < TOL_COEF and err_se < TOL_SE
        lines.append(
            f"{name:<15}{coef:>15.7f}{ref['coef']:>16.7f}{err_coef:>12.2e}"
            f"{se:>13.7f}{ref['se']:>14.7f}{err_se:>12.2e}"
        )

    r2_ok = round(model.rsquared, TOL_R2_DECIMALS) == round(REFERENCE_R2, TOL_R2_DECIMALS)
    r2adj_ok = round(model.rsquared_adj, TOL_R2_DECIMALS) == round(REFERENCE_R2_ADJ, TOL_R2_DECIMALS)
    all_ok = all_ok and r2_ok and r2adj_ok

    lines += [
        "",
        f"Python R2: {model.rsquared:.6f} | Thesis R2: {REFERENCE_R2:.6f} | {'OK' if r2_ok else 'FAIL'}",
        f"Python adjusted R2: {model.rsquared_adj:.6f} | Thesis adjusted R2: {REFERENCE_R2_ADJ:.6f} | "
        f"{'OK' if r2adj_ok else 'FAIL'}",
        f"Python F: {model.fvalue:.6f} | Thesis F: {REFERENCE_F:.6f}",
        f"Python p(F): {model.f_pvalue:.6f} | Thesis p(F): {REFERENCE_F_PVALUE:.6f}",
        "",
        f"REPRODUCTION: {'OK, within tolerance' if all_ok else 'FAIL, outside tolerance'}",
        "",
        "=" * 78,
        "Full statsmodels output:",
        "=" * 78,
    ]

    # Blank the run date/time (left half of those rows) so the report is
    # identical across runs; the right half carries p(F) and log-likelihood.
    half = 39
    for row in str(model.summary()).splitlines():
        if row.startswith(("Date:", "Time:")):
            row = (row.split(":")[0] + ":").ljust(half) + row[half:]
        lines.append(row)

    report = "\n".join(lines)
    print(report)
    OUTPUT_PATH.parent.mkdir(exist_ok=True)
    OUTPUT_PATH.write_text(report, encoding="utf-8")


if __name__ == "__main__":
    main()
