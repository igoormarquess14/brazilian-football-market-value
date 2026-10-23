#!/usr/bin/env python3
"""
Drops players with no market value (Value_Num == 0) and splits the base by
position using the Dum_GK/Dum_DEF/Dum_MC/Dum_ATA dummies.

age_centered and age_sq are recomputed on each subgroup's own mean, which is
the convention of the original 2025-10-16 files. The original script did not
survive; this one was reconstructed from its outputs and reproduces
df_ata.csv, df_def.csv and df_gk.csv byte for byte (see docs/methodology.md).

Input:  data/players_checkpoint.csv (285 rows)
Output: data/df_gk.csv, data/df_def.csv, data/df_mc.csv, data/df_ata.csv
"""

from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
INPUT_PATH = PROJECT_ROOT / "data" / "players_checkpoint.csv"
OUTPUT_DIR = PROJECT_ROOT / "data"

POSITIONS = {
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

    for file_name, dummy in POSITIONS.items():
        subset = df[df[dummy] == 1].copy()
        subset["age_centered"] = subset["age"] - subset["age"].mean()
        subset["age_sq"] = subset["age_centered"] ** 2

        out_path = OUTPUT_DIR / file_name
        subset.to_csv(out_path, index=False)
        print(f"{file_name}: {len(subset)} rows -> {out_path}")


if __name__ == "__main__":
    main()
