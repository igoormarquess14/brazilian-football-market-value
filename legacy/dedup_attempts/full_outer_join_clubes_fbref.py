import pandas as pd

PATH_CLUBES = r"C:\Users\IGOR\Desktop\UFSC\TCC\dados\clubes\outcome\todos_clubes_2024_final.csv"
PATH_FBREF = r"C:\Users\IGOR\Desktop\UFSC\TCC\dados\minutes_played\fbref_playing_time_cleaned.csv"
OUT_PATH = r"C:\Users\IGOR\Desktop\UFSC\TCC\dados\clubes\outcome\full_outer_clubes_fbref.csv"

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

# Prefix FBref columns
fb_prefixed = fb.add_prefix("fb_")

# Full outer join on Player+club+age
merged = cl.merge(
    fb_prefixed,
    left_on=["Player", "Clube", "_join_age"],
    right_on=["fb_Player", "fb_Squad", "fb__join_age"],
    how="outer",
)

# Drop helper fb key
if "fb__join_age" in merged.columns:
    merged = merged.drop(columns=["fb__join_age"]) 

# Save
merged.to_csv(OUT_PATH, index=False, encoding="utf-8")
print(f"Saved full outer join to: {OUT_PATH} with {len(merged)} rows and {len(merged.columns)} columns")












