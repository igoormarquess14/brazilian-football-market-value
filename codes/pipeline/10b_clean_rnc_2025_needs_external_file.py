from pathlib import Path
import os
import pandas as pd

PATH_RNC = r"C:\Users\IGOR\Downloads\rnc_2025_clubes_pos_pontos.csv"
PATH_FINAL = str(PROJECT_ROOT / "dados" / "clubes" / "outcome" / "final_merged_filtrado_dummies_clean.csv")
OUT_PATH = str(PROJECT_ROOT / "dados" / "clubes" / "outcome" / "rnc_2025_clubes_pos_pontos_clean.csv")

# Read inputs
rnc = pd.read_csv(PATH_RNC, encoding="utf-8")
base = pd.read_csv(PATH_FINAL, encoding="utf-8")

# Ensure columns (column name is the actual RNC CSV column — not translated)
if "posicao" not in rnc.columns:
    # Try case variants
    possible = [c for c in rnc.columns if c.lower() == "posicao"]
    if not possible:
        raise KeyError("Column 'posicao' not found in the RNC CSV")
    rnc.rename(columns={possible[0]: "posicao"}, inplace=True)

# 1) Keep only posicao <= 38
rnc["posicao_num"] = pd.to_numeric(rnc["posicao"], errors="coerce")
rnc = rnc[rnc["posicao_num"].notna()]
rnc = rnc[rnc["posicao_num"] <= 38].copy()

# 2) Remove Botafogo at posicao == 32 (case-insensitive)
club_col = None
for cand in ["clube","Clube","time","Time","clube_nome","team"]:
    if cand in rnc.columns:
        club_col = cand
        break
if club_col is None:
    raise KeyError("Club column not found in the RNC CSV (e.g. 'clube'/'Clube')")

rnc = rnc[~((rnc["posicao_num"] == 32) & (rnc[club_col].str.strip().str.lower() == "botafogo"))]

# 3) Map club names to match final_merged CSV
# Build mapping from base clubs (unique)
base_clubs = sorted(base["Clube"].astype(str).str.strip().unique())

# Simple normalization for keys
import unicodedata

PROJECT_ROOT = Path(__file__).resolve().parents[2]

def norm(s: str) -> str:
    s2 = "" if not isinstance(s, str) else s
    s2 = unicodedata.normalize("NFKD", s2)
    s2 = "".join(ch for ch in s2 if not unicodedata.combining(ch))
    s2 = s2.lower().replace("_"," ")
    s2 = " ".join(s2.split())
    return s2

base_key_to_name = {norm(c): c for c in base_clubs}

# Common aliases -> target name (based on earlier mappings)
aliases = {
    "sao paulo": "spfc",
    "sao paulo fc": "spfc",
    "red bull bragantino": "bragantino",
    "rb bragantino": "bragantino",
    "atletico mineiro": "atletico_mineiro",
    "atletico-mg": "atletico_mineiro",
    "botafogo rj": "botafogo",
    "sport recife": "sport",
    "ec bahia": "bahia",
    "gremio": "gremio",
    "ceara": "ceara",
    "vitoria": "vitoria",
}

# Map function

def map_club(name: str) -> str:
    key = norm(name)
    if key in base_key_to_name:
        return base_key_to_name[key]
    if key in aliases:
        return aliases[key]
    # try collapses without spaces
    key2 = key.replace(" ", "_")
    if key2 in base_key_to_name:
        return base_key_to_name[key2]
    return name  # leave as-is if not found

rnc[club_col] = rnc[club_col].astype(str).map(map_club)

# Drop helper
rnc.drop(columns=["posicao_num"], inplace=True)

# Save
rnc.to_csv(OUT_PATH, index=False, encoding="utf-8")
print(f"Saved cleaned RNC CSV to: {OUT_PATH} with {len(rnc)} rows")

