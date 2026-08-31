#!/usr/bin/env python3
"""
Verifies that dados/df_final.csv (283 rows, the final sample cited in the
thesis) is consistent with the checkpoint
dados/clubes/outcome/df_final.csv (285 rows) under the Value_Num > 0 filter.

Does not regenerate dados/df_final.csv: that file has two extra columns,
dum_inf and dum_sup, created manually during an exploratory robustness
analysis (outside the published model — see docs/pipeline.md) whose exact
cutoff rule was not recovered. The remaining columns are checked here.
"""

from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CHECKPOINT_PATH = PROJECT_ROOT / "dados" / "clubes" / "outcome" / "df_final.csv"
FINAL_PATH = PROJECT_ROOT / "dados" / "df_final.csv"


def main() -> None:
    checkpoint = pd.read_csv(CHECKPOINT_PATH)
    final = pd.read_csv(FINAL_PATH)

    esperado = checkpoint[checkpoint["Value_Num"] > 0].copy()
    colunas_comuns = [c for c in esperado.columns if c in final.columns]

    esperado_chave = esperado.merge(final, on=["Player", "Clube"], suffixes=("_esperado", "_final"))
    print(f"Checkpoint (285 rows) after Value_Num>0 filter: {len(esperado)} rows")
    print(f"dados/df_final.csv: {len(final)} rows")
    print(f"Rows matched by Player+Clube: {len(esperado_chave)}")

    divergencias = 0
    for col in colunas_comuns:
        if col in ("Player", "Clube"):
            continue
        a = pd.to_numeric(esperado_chave[f"{col}_esperado"], errors="coerce")
        b = pd.to_numeric(esperado_chave[f"{col}_final"], errors="coerce")
        max_diff = (a - b).abs().max()
        if max_diff > 1e-6:
            print(f"  DIVERGES: {col} (max diff = {max_diff})")
            divergencias += 1

    if divergencias == 0:
        print("OK: all shared columns match exactly.")
    print(f"Extra columns in dados/df_final.csv not verified here: "
          f"{[c for c in final.columns if c not in checkpoint.columns]} "
          f"(manual annotations, see docs/pipeline.md)")


if __name__ == "__main__":
    main()
