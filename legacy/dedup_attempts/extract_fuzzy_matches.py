import pandas as pd

PATH_FUZZY_MERGED = r"C:\Users\IGOR\Desktop\UFSC\TCC\dados\clubes\outcome\fuzzy_corrected_merged.csv"
OUT_PATH = r"C:\Users\IGOR\Desktop\UFSC\TCC\dados\clubes\outcome\fuzzy_matches_only.csv"

# Read the fuzzy-corrected merged file
df = pd.read_csv(PATH_FUZZY_MERGED, encoding="utf-8")

# Filter only rows that have fuzzy_match_score (the 100 fuzzy matches)
fuzzy_only = df[df["fuzzy_match_score"].notna()].copy()

# Sort by score descending to see best matches first
fuzzy_only = fuzzy_only.sort_values("fuzzy_match_score", ascending=False)

# Save
fuzzy_only.to_csv(OUT_PATH, index=False, encoding="utf-8")
print(f"Saved {len(fuzzy_only)} fuzzy matches to: {OUT_PATH}")
print(f"Score range: {fuzzy_only['fuzzy_match_score'].min():.3f} - {fuzzy_only['fuzzy_match_score'].max():.3f}")














