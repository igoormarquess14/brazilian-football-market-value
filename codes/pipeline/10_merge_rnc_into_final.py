from pathlib import Path
import os
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]

PATH_FINAL = str(PROJECT_ROOT / "dados" / "clubes" / "outcome" / "final_merged_filtrado_dummies_clean.csv")
PATH_RNC = str(PROJECT_ROOT / "dados" / "clubes" / "outcome" / "rnc_2025_clubes_pos_pontos_clean.csv")
OUT_PATH = str(PROJECT_ROOT / "dados" / "clubes" / "outcome" / "df_final.csv")

try:
    print(f"Reading FINAL: {PATH_FINAL}")
    df = pd.read_csv(PATH_FINAL, encoding="utf-8")
    print(f"FINAL shape: {df.shape}")

    print(f"Reading RNC: {PATH_RNC}")
    rnc = pd.read_csv(PATH_RNC, encoding="utf-8")
    print(f"RNC shape: {rnc.shape}")

    # Identify club column in RNC
    club_col = None
    for cand in ["Clube","clube","time","Time","clube_nome","team"]:
        if cand in rnc.columns:
            club_col = cand
            break
    if club_col is None:
        raise KeyError("Club column not found in the cleaned RNC file")

    # Ensure needed columns in RNC (these are the actual RNC column names — not translated)
    pos_col = "posicao" if "posicao" in rnc.columns else None
    pts_col = "pontos" if "pontos" in rnc.columns else None
    if pos_col is None or pts_col is None:
        raise KeyError("Columns 'posicao' and/or 'pontos' not found in the cleaned RNC file")

    # Reduce RNC to mapping (dedupe by taking first occurrence)
    rnc_map = rnc[[club_col, pos_col, pts_col]].copy()
    before = len(rnc_map)
    rnc_map = rnc_map.drop_duplicates(subset=[club_col])
    after = len(rnc_map)
    print(f"RNC mapping rows: {after} (deduped from {before}) using key '{club_col}'")

    # Merge by Clube name
    merged = df.merge(rnc_map, how="left", left_on="Clube", right_on=club_col)
    print(f"Merged shape: {merged.shape}")

    # Create new columns
    merged["pos_rnc"] = merged[pos_col]
    merged["pts_rnc"] = merged[pts_col]

    # Drop helper join columns
    drop_cols = [c for c in [club_col, pos_col, pts_col] if c in merged.columns]
    merged = merged.drop(columns=drop_cols)

    # Ensure directory exists
    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)

    # Save
    merged.to_csv(OUT_PATH, index=False, encoding="utf-8")
    print(f"Saved final dataframe with RNC cols to: {OUT_PATH} ({len(merged)} rows, {len(merged.columns)} cols)")
except Exception as e:
    print(f"ERROR: {e}")
    raise

