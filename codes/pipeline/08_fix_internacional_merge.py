#!/usr/bin/env python3
"""
Updates rows for the 'inter' club in final_merged_filtrado_dummies.csv,
filling in FBRef metrics via the fbref antijoin for 'internacional' and
renaming the club to 'internacional'.
"""

import pandas as pd
import numpy as np
import unicodedata
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]


ANTIJOIN_PATH = Path(str(PROJECT_ROOT / "dados" / "clubes" / "outcome" / "antijoin_only_clubes_fbref.csv"))
FINAL_DUMMIES_PATH = Path(str(PROJECT_ROOT / "dados" / "clubes" / "outcome" / "final_merged_filtrado_dummies.csv"))
BACKUP_PATH = FINAL_DUMMIES_PATH.with_name("final_merged_filtrado_dummies.backup_before_internacional_fix.csv")


def normalize_text(s: str) -> str:
    if pd.isna(s):
        return ""
    s = str(s).strip().lower()
    s = unicodedata.normalize('NFKD', s).encode('ascii', 'ignore').decode('ascii')
    return s


def main():
    if not ANTIJOIN_PATH.exists() or not FINAL_DUMMIES_PATH.exists():
        print("ERROR: required files not found.")
        print(ANTIJOIN_PATH)
        print(FINAL_DUMMIES_PATH)
        return

    # Load files
    anti = pd.read_csv(ANTIJOIN_PATH)
    final_df = pd.read_csv(FINAL_DUMMIES_PATH)

    # Subset: FBRef 'right_only' rows referring to 'internacional'
    # (data value, not translated). In these rows, the fb_* columns are filled in.
    anti_fb = anti.copy()
    anti_fb['fb_Squad_norm'] = anti_fb.get('fb_Squad', '').apply(normalize_text)
    anti_fb['fb_Player_norm'] = anti_fb.get('fb_Player', '').apply(normalize_text)
    fbref_int = anti_fb[(anti_fb['_merge'] == 'right_only') & (anti_fb['fb_Squad_norm'] == 'internacional')]

    # Build the Player -> desired fb_ metrics mapping
    fb_cols = ['fb_Mn/MP', 'fb_PPM', 'fb_+/-', 'fb_xG+/-']
    available_fb_cols = [c for c in fb_cols if c in fbref_int.columns]
    fb_map = fbref_int[['fb_Player_norm'] + available_fb_cols].drop_duplicates('fb_Player_norm')

    # Filter 'inter' rows in the final base (club-name data values, not translated)
    final_df['Clube_norm'] = final_df['Clube'].apply(normalize_text)
    final_df['Player_norm'] = final_df['Player'].apply(normalize_text)
    mask_inter = final_df['Clube_norm'].isin(['inter', 'internacional'])
    inter_rows = final_df[mask_inter].copy()

    if inter_rows.empty:
        print("No row with club 'inter'/'internacional' found in the final file.")
        return

    # Merge on normalized name
    merged = inter_rows.merge(fb_map, left_on='Player_norm', right_on='fb_Player_norm', how='left')

    # Update the fb_* columns where available
    for col in available_fb_cols:
        ycol = col + '_y'
        xcol = col + '_x'
        if ycol in merged.columns or xcol in merged.columns:
            merged[col] = merged.get(ycol).combine_first(merged.get(xcol))
        elif col in merged.columns:
            merged[col] = merged[col]
        else:
            merged[col] = np.nan

    # Rename the club to 'internacional' (data value, not translated)
    merged['Clube'] = 'internacional'

    # Drop helper and merge-duplicate columns
    drop_cols = [c for c in merged.columns if c.endswith('_x') or c.endswith('_y') or c.endswith('_norm') or c == 'fb_Player_norm']
    merged_clean = merged.drop(columns=drop_cols, errors='ignore')

    # Recompute the position dummies if needed
    def make_dummies(pos_num: float):
        # Simple mapping based on Position_Num
        try:
            p = float(pos_num)
        except Exception:
            p = np.nan
        dum_gk = 1 if p == 1 else 0
        dum_def = 1 if p in [2, 3, 4, 5] else 0
        dum_mc = 1 if p in [6, 7, 8] else 0
        dum_ata = 1 if p in [9, 10, 11] else 0
        return pd.Series([dum_gk, dum_def, dum_mc, dum_ata], index=['Dum_GK','Dum_DEF','Dum_MC','Dum_ATA'])

    merged_clean[['Dum_GK','Dum_DEF','Dum_MC','Dum_ATA']] = merged_clean['Position_Num'].apply(make_dummies)

    # Replace in final_df: drop the old 'inter' rows and append the fixed ones
    final_updated = final_df[~mask_inter].copy()

    # Preserve the final file's column order
    final_cols = [c for c in final_df.columns if c not in ['Clube_norm','Player_norm']]
    final_cols_present = [c for c in final_cols if c in merged_clean.columns]
    merged_clean = merged_clean[final_cols_present]

    final_updated = pd.concat([final_updated[final_cols_present], merged_clean], ignore_index=True)

    # Back up and save
    if not BACKUP_PATH.exists():
        final_df.to_csv(BACKUP_PATH, index=False)
        print(f"Backup created: {BACKUP_PATH}")
    final_updated.to_csv(FINAL_DUMMIES_PATH, index=False)
    print(f"File updated: {FINAL_DUMMIES_PATH}")
    print(f"Rows updated for club 'internacional': {len(merged_clean)}")


if __name__ == "__main__":
    main()


