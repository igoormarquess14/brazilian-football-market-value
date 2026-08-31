from pathlib import Path
# merges FBref players with club players
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]

PATH_CLUBES = str(PROJECT_ROOT / "dados" / "clubes" / "outcome" / "todos_clubes_2024_final.csv")
PATH_FBREF = str(PROJECT_ROOT / "dados" / "minutes_played" / "fbref_playing_time_cleaned.csv")
OUT_PATH = str(PROJECT_ROOT / "dados" / "clubes" / "outcome" / "atletas_fbref_merged.csv")

# Read inputs
cl = pd.read_csv(PATH_CLUBES, encoding="utf-8")
fb = pd.read_csv(PATH_FBREF, sep=";", encoding="utf-8")

# Ensure required columns
for col in ["Player", "Clube", "age"]:
    if col not in cl.columns:
        raise KeyError(f"Missing column '{col}' in todos_clubes_2024_final.csv")
for col in ["Player", "Squad", "Age"]:
    if col not in fb.columns:
        raise KeyError(f"Missing column '{col}' in fbref_playing_time_cleaned.csv")

# Coerce ages to integers where possible
cl_age = pd.to_numeric(cl["age"], errors="coerce").astype("Int64")
fb_age = pd.to_numeric(fb["Age"], errors="coerce").astype("Int64")

cl = cl.assign(_join_age=cl_age)
fb = fb.assign(_join_age=fb_age)

# Rename fbref columns to avoid collisions and make provenance explicit
fb_prefixed = fb.add_prefix("fb_")

# Merge on Player + club + age equality
merged_full = cl.merge(
    fb_prefixed,
    left_on=["Player", "Clube", "_join_age"],
    right_on=["fb_Player", "fb_Squad", "fb__join_age"],
    how="inner",
)

# Drop helper join key copy from FBref
if "fb__join_age" in merged_full.columns:
    merged_full = merged_full.drop(columns=["fb__join_age"]) 

# Save output with all clubes columns + all prefixed FBref columns
merged_full.to_csv(OUT_PATH, index=False, encoding="utf-8")
print(f"Merged rows: {len(merged_full)}. Saved to: {OUT_PATH}")
