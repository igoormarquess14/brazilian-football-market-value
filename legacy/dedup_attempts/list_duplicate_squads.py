#lista os valores duplicados da coluna Squad
#deu certo
import pandas as pd

path_cleaned = r"C:\Users\IGOR\Desktop\UFSC\TCC\dados\minutes_played\fbref_playing_time_cleaned.csv"

# Read cleaned CSV (semicolon separated)
df = pd.read_csv(path_cleaned, sep=";", encoding="utf-8")

# Count occurrences of Squad
counts = df["Squad"].fillna("").value_counts()

duplicates = counts[counts > 1]

if duplicates.empty:
    print("No duplicate Squad values.")
else:
    print("Duplicate Squad values (value: count):")
    for value, cnt in duplicates.items():
        print(f"{value}: {cnt}")
