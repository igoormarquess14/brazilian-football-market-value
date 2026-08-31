#!/usr/bin/env python3
"""
Filters out players with no market value (Value_Num == 0) and splits the
base by position, using the Dum_GK/Dum_DEF/Dum_MC/Dum_ATA dummies.

Reconstructed in this session: the original script that produced
dados/df_ata.csv, dados/df_def.csv, dados/df_gk.csv, and dados/df_mc.csv
(2025-10-16 session) did not survive in the repository (only the result
did). The logic was inferred from the existing files and verified byte for
byte against the three that were never corrupted afterward (df_ata.csv,
df_def.csv, df_gk.csv) — see docs/pipeline.md.

Input: dados/clubes/outcome/df_final.csv (285 rows, output of
codes/pipeline/08_merge_rnc_into_final.py — see the gap documented in
docs/pipeline.md regarding this step no longer running).

Output: dados/df_gk.csv, dados/df_def.csv, dados/df_mc.csv, dados/df_ata.csv.
"""

from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
INPUT_PATH = PROJECT_ROOT / "dados" / "clubes" / "outcome" / "df_final.csv"
OUTPUT_DIR = PROJECT_ROOT / "dados"

POSICOES = {
    "df_gk.csv": "Dum_GK",
    "df_def.csv": "Dum_DEF",
    "df_mc.csv": "Dum_MC",
    "df_ata.csv": "Dum_ATA",
}


def main() -> None:
    df = pd.read_csv(INPUT_PATH)
    print(f"Base loaded: {df.shape[0]} rows, {df.shape[1]} columns")

    df = df[df["Value_Num"] > 0].copy()
    print(f"After filtering Value_Num > 0: {df.shape[0]} rows")

    for nome_arquivo, coluna_dummy in POSICOES.items():
        df_posicao = df[df[coluna_dummy] == 1].copy()

        # age_centered/age_sq are recomputed on the subgroup's own mean, not
        # inherited from the full base (confirmed by byte-for-byte
        # verification against dados/df_ata.csv and dados/df_def.csv, which
        # preserve the original 2025-10-16 convention).
        df_posicao["age_centered"] = df_posicao["age"] - df_posicao["age"].mean()
        df_posicao["age_sq"] = df_posicao["age_centered"] ** 2

        out_path = OUTPUT_DIR / nome_arquivo
        df_posicao.to_csv(out_path, index=False)
        print(f"{nome_arquivo}: {len(df_posicao)} rows -> {out_path}")


if __name__ == "__main__":
    main()
