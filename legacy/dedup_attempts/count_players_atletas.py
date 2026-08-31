import os
import pandas as pd

path_in = r"C:\Users\IGOR\Desktop\UFSC\TCC\dados\clubes\outcome\atletas_completo.csv"
path_out = os.path.join(os.path.dirname(path_in), "players_counts.csv")

# Read atletas CSV (comma separated)
df = pd.read_csv(path_in, encoding="utf-8")

# Ensure column exists
if "Player" not in df.columns:
    raise KeyError("Column 'Player' not found in atletas_completo.csv")

# Count names (case-sensitive by default; if you need case-insensitive, lower() first)
counts = df["Player"].fillna("").value_counts().reset_index()
counts.columns = ["Player", "count"]

# Save
counts.to_csv(path_out, index=False, encoding="utf-8")
print(f"Saved player counts to: {path_out}")












