from pathlib import Path
# cleans fbref_playing_time.csv by removing accents and special characters
# still needs better mapping of player names
import os
import unicodedata
from typing import Dict, Any

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def read_csv_robust(path: str, sep: str, expected_cols: list[str]) -> pd.DataFrame:
    encodings = ["utf-8", "latin-1", "cp1252"]
    last_err: Exception | None = None
    for enc in encodings:
        try:
            df = pd.read_csv(path, sep=sep, encoding=enc)
            missing = [c for c in expected_cols if c not in df.columns]
            if missing:
                last_err = ValueError(f"Missing columns {missing} with sep={sep} enc={enc}")
                continue
            return df
        except Exception as e:  # noqa: BLE001
            last_err = e
            continue
    if last_err:
        raise last_err
    raise RuntimeError("Failed to read CSV with attempted encodings")


def strip_accents(text: str) -> str:
    if not isinstance(text, str):
        text = str(text) if pd.notna(text) else ""
    text = text.replace("\uFFFD", " ").replace("�", " ")
    normalized = unicodedata.normalize("NFKD", text)
    return "".join(ch for ch in normalized if not unicodedata.combining(ch))


def clean_player_name(name: Any) -> str:
    if pd.isna(name):
        return ""
    base = strip_accents(str(name))
    base = base.strip()
    base = " ".join(part.capitalize() for part in base.split())
    return base


def normalize_key(text: Any) -> str:
    if pd.isna(text):
        return ""
    s = strip_accents(str(text)).lower()
    # keep alnum and spaces/underscores only
    out_chars: list[str] = []
    for ch in s:
        if ch.isalnum():
            out_chars.append(ch)
        elif ch in {" ", "_"}:
            out_chars.append(" ")
        else:
            out_chars.append(" ")
    s = " ".join("".join(out_chars).split())
    return s


def slugify(text: str) -> str:
    key = normalize_key(text)
    return key.replace(" ", "_")


def build_squad_to_clube_map(path_atletas: str) -> Dict[str, str]:
    # Read atletas (comma sep)
    df_at = read_csv_robust(path_atletas, sep=",", expected_cols=["Clube"])  # Player not required for mapping
    # Unique clube slugs
    df_at["clube_slug"] = df_at["Clube"].astype(str).map(lambda x: slugify(x))
    unique_clubes = (
        df_at.drop_duplicates(["clube_slug"]).loc[:, ["clube_slug", "Clube"]]
    )
    # Map normalized keys to canonical Clube values
    mapping: Dict[str, str] = {}
    for _, row in unique_clubes.iterrows():
        mapping[row["clube_slug"]] = str(row["Clube"]).strip()
    # Manual aliases per user preference and common cases
    manual = {
        # keep as-is (identity mappings included for clarity)
        "sport": "sport",
        "juventude": "juventude",
        "fortaleza": "fortaleza",
        "flamengo": "flamengo",
        "vasco": "vasco",
        "fluminense": "fluminense",
        "internacional": "internacional",
        "botafogo": "botafogo",
        "santos": "santos",
        "corinthians": "corinthians",
        "palmeiras": "palmeiras",
        "bahia": "bahia",
        "cruzeiro": "cruzeiro",
        # corrected broken-encoding variants -> canonical
        "vit_ria": "vitoria",
        "gr_mio": "gremio",
        "s_o_paulo": "spfc",
        "atl_tico_mineiro": "atletico_mineiro",
        "rb_bragantino": "bragantino",
        "cear": "ceara",
        # other aliases that may appear
        "sao_paulo": "spfc",
        "atletico_mineiro": "atletico_mineiro",
        "red_bull_bragantino": "bragantino",
        "vasco_da_gama": "vasco",
        "botafogo_rj": "botafogo",
        "sport_recife": "sport",
        "ec_bahia": "bahia",
        "america_mg": "america_mg",
    }
    mapping.update(manual)
    return mapping


def clean_age(value: Any) -> str:
    if pd.isna(value):
        return ""
    s = str(value)
    if "-" in s:
        s = s.split("-", 1)[0]
    return s.strip()


def main() -> None:
    path_fbref = str(PROJECT_ROOT / "dados" / "minutes_played" / "fbref_playing_time.csv")
    path_atletas = str(PROJECT_ROOT / "dados" / "clubes" / "outcome" / "atletas_completo.csv")

    # Read fbref (semicolon)
    df = read_csv_robust(path_fbref, sep=";", expected_cols=["Player", "Squad", "Age"])

    # Clean Player
    df["Player"] = df["Player"].map(clean_player_name)

    # Build mapping for Squad to Clube canonical names
    squad_to_clube = build_squad_to_clube_map(path_atletas)

    # Normalize Squad names to slugs
    df["Squad_slug"] = df["Squad"].map(lambda x: slugify(x))

    # Map to Clube, default to slug if not found
    df["Squad"] = df["Squad_slug"].map(lambda k: squad_to_clube.get(k, k))

    # Clean Age (keep only part before '-')
    df["Age"] = df["Age"].map(clean_age)

    # Drop helper
    df.drop(columns=["Squad_slug"], inplace=True)

    # Write output
    out_dir = os.path.dirname(path_fbref)
    out_path = os.path.join(out_dir, "fbref_playing_time_cleaned.csv")
    df.to_csv(out_path, index=False, sep=";", encoding="utf-8")
    print(f"Saved cleaned file to: {out_path}")


if __name__ == "__main__":
    main()
