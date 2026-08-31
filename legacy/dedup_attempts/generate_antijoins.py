import os
import pandas as pd

PATH_CLUBES = r"C:\Users\IGOR\Desktop\UFSC\TCC\dados\clubes\outcome\todos_clubes_2024_final.csv"
PATH_FBREF = r"C:\Users\IGOR\Desktop\UFSC\TCC\dados\minutes_played\fbref_playing_time_cleaned.csv"
OUT_DIR = r"C:\Users\IGOR\Desktop\UFSC\TCC\dados\clubes\outcome"

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
cl["_join_age"] = pd.to_numeric(cl["age"], errors="coerce").astype("Int64")
fb["_join_age"] = pd.to_numeric(fb["Age"], errors="coerce").astype("Int64")

# Build keys for anti-join
cl["_key"] = cl["Player"].astype(str) + "||" + cl["Clube"].astype(str) + "||" + cl["_join_age"].astype(str)
fb["_key"] = fb["Player"].astype(str) + "||" + fb["Squad"].astype(str) + "||" + fb["_join_age"].astype(str)

cl_keys = set(cl["_key"].tolist())
fb_keys = set(fb["_key"].tolist())

# Anti-joins
cl_minus_fb = cl[~cl["_key"].isin(fb_keys)].drop(columns=["_join_age", "_key"])  # A-B
fb_minus_cl = fb[~fb["_key"].isin(cl_keys)].drop(columns=["_join_age", "_key"])  # B-A

# Save outputs
path_a = os.path.join(OUT_DIR, "nao_casados_todos_clubes_vs_fbref.csv")
path_b = os.path.join(OUT_DIR, "nao_casados_fbref_vs_todos_clubes.csv")

cl_minus_fb.to_csv(path_a, index=False, encoding="utf-8")
fb_minus_cl.to_csv(path_b, index=False, sep=";", encoding="utf-8")

print(f"Saved A-B: {path_a} ({len(cl_minus_fb)} rows)")
print(f"Saved B-A: {path_b} ({len(fb_minus_cl)} rows)")












