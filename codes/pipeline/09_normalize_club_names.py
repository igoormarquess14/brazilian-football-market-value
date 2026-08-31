#!/usr/bin/env python3
"""
Standardizes club names in the 'Clube' column of the given CSVs.
E.g.: 'inter' -> 'internacional'.
"""

import sys
from pathlib import Path
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]

# club-name data values, not translated
CLUB_MAP = {
    'inter': 'internacional',
    # add other mappings here if needed
}


def normalize_file(csv_path: Path) -> None:
    if not csv_path.exists():
        print(f"File not found: {csv_path}")
        return
    df = pd.read_csv(csv_path)
    if 'Clube' not in df.columns:
        print(f"Column 'Clube' not found in: {csv_path}")
        return
    before_counts = df['Clube'].value_counts().to_dict()
    df['Clube'] = df['Clube'].astype(str).str.strip().str.lower().replace(CLUB_MAP)
    after_counts = df['Clube'].value_counts().to_dict()
    df.to_csv(csv_path, index=False)
    print(f"Normalized: {csv_path}")
    # Optional: show a brief summary of the change
    if 'inter' in before_counts or 'internacional' in after_counts:
        print("inter -> internacional applied (if present)")


def main():
    # Default targets, if no argument is passed
    outcome_dir = PROJECT_ROOT / "dados" / "clubes" / "outcome"
    default_targets = [
        str(outcome_dir / "final_merged_filtrado.csv"),
        str(outcome_dir / "final_merged_filtrado_dummies.csv"),
        str(outcome_dir / "final_merged_filtrado_dummies_clean.csv"),
        str(outcome_dir / "final_merged_filtrado_dummies_clean_with_cluster_v2.csv"),
    ]

    targets = [Path(p) for p in (sys.argv[1:] if len(sys.argv) > 1 else default_targets)]
    for path in targets:
        normalize_file(Path(path))


if __name__ == "__main__":
    main()



