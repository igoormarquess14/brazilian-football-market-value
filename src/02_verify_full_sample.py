#!/usr/bin/env python3
"""
Checks that data/df_final.csv (283 rows, the full sample described in the
thesis) is data/players_checkpoint.csv (285 rows) after the Value_Num > 0
filter, and reports every column where the two differ.

Expected differences, all outside the published model:
- age_centered, age_sq: centered on the 283-row mean in df_final.csv and on
  the 285-row mean in the checkpoint.
- pos_rnc, pts_rnc: stored on different scales; the transformation was not
  recovered.
- dum_inf, dum_sup: exist only in df_final.csv (manual annotations from an
  unpublished robustness check).

Output: outputs/full_sample_check.txt
"""

from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
CHECKPOINT_PATH = PROJECT_ROOT / "data" / "players_checkpoint.csv"
FINAL_PATH = PROJECT_ROOT / "data" / "df_final.csv"
OUTPUT_PATH = PROJECT_ROOT / "outputs" / "full_sample_check.txt"


def main() -> None:
    checkpoint = pd.read_csv(CHECKPOINT_PATH)
    final = pd.read_csv(FINAL_PATH)

    expected = checkpoint[checkpoint["Value_Num"] > 0].copy()
    shared = [c for c in expected.columns if c in final.columns]
    matched = expected.merge(final, on=["Player", "Clube"], suffixes=("_expected", "_final"))

    lines = [
        f"Checkpoint after Value_Num > 0 filter: {len(expected)} rows",
        f"data/df_final.csv: {len(final)} rows",
        f"Rows matched by Player + Clube: {len(matched)}",
        "",
    ]

    diverging = []
    for col in shared:
        if col in ("Player", "Clube"):
            continue
        a = pd.to_numeric(matched[f"{col}_expected"], errors="coerce")
        b = pd.to_numeric(matched[f"{col}_final"], errors="coerce")
        max_diff = (a - b).abs().max()
        if max_diff > 1e-6:
            diverging.append(col)
            lines.append(f"DIFFERS: {col} (max abs diff = {max_diff:.6g})")

    if not diverging:
        lines.append("All shared columns match exactly.")

    extra = [c for c in final.columns if c not in checkpoint.columns]
    lines.append(f"Columns only in df_final.csv: {extra}")
    lines.append("")
    lines.append("See the docstring of this script for why each difference is expected.")

    report = "\n".join(lines)
    print(report)
    OUTPUT_PATH.parent.mkdir(exist_ok=True)
    OUTPUT_PATH.write_text(report + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
