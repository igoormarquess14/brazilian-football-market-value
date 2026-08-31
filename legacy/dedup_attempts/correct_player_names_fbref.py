import os
import unicodedata
from difflib import SequenceMatcher
from typing import Any, Dict, List, Tuple

import pandas as pd

# Paths
PATH_FBREF_CLEAN = r"C:\Users\IGOR\Desktop\UFSC\TCC\dados\minutes_played\fbref_playing_time_cleaned.csv"
PATH_ATLETAS = r"C:\Users\IGOR\Desktop\UFSC\TCC\dados\clubes\outcome\atletas_completo.csv"
OUT_PATH = r"C:\Users\IGOR\Desktop\UFSC\TCC\dados\minutes_played\fbref_playing_time_corrected.csv"


def strip_accents(text: Any) -> str:
    if pd.isna(text):
        return ""
    s = str(text)
    s = s.replace("\uFFFD", " ").replace("�", " ")
    s = unicodedata.normalize("NFKD", s)
    return "".join(ch for ch in s if not unicodedata.combining(ch))


def normalize_key(text: Any) -> str:
    if pd.isna(text):
        return ""
    s = strip_accents(str(text)).lower()
    tokens = s.replace("_", " ")
    tokens = " ".join(tokens.split())
    return tokens


def token_set_key(text: str) -> str:
    toks = sorted(set(t for t in text.split() if t))
    return " ".join(toks)


def similarity(a: str, b: str) -> float:
    if not a or not b:
        return 0.0
    ak = token_set_key(normalize_key(a))
    bk = token_set_key(normalize_key(b))
    return SequenceMatcher(None, ak, bk).ratio()


def build_blocks_by_club(df: pd.DataFrame, club_col: str, name_col: str) -> Dict[str, List[str]]:
    blocks: Dict[str, List[str]] = {}
    for _, row in df.iterrows():
        club_key = normalize_key(row[club_col])
        name = str(row[name_col])
        blocks.setdefault(club_key, []).append(name)
    return blocks


def best_match(candidates: List[str], query: str) -> Tuple[str | None, float]:
    best_name: str | None = None
    best_score = -1.0
    for cand in candidates:
        s = similarity(query, cand)
        if s > best_score:
            best_score = s
            best_name = cand
    return best_name, (best_score if best_score >= 0 else 0.0)


def main() -> None:
    # Read inputs
    df_fb = pd.read_csv(PATH_FBREF_CLEAN, sep=";", encoding="utf-8")
    df_at = pd.read_csv(PATH_ATLETAS, encoding="utf-8")

    # Build blocking by club using normalized Clube/Squad
    df_fb["club_key"] = df_fb["Squad"].map(normalize_key)
    df_at["club_key"] = df_at["Clube"].map(normalize_key)

    # Canonical player names per club
    club_to_canonical_names = build_blocks_by_club(df_at, "club_key", "Player")

    # For clubs without a block (fallback), also collect a global list
    global_canonical = sorted(set(df_at["Player"].astype(str).tolist()))

    updates = 0
    total = len(df_fb)
    corrected_names: List[str] = []

    # Similarity thresholds
    thr_same_club = 0.88
    thr_global = 0.92

    for _, row in df_fb.iterrows():
        raw_name = str(row["Player"]) if not pd.isna(row["Player"]) else ""
        club_key = row["club_key"]

        # Candidates: same club first
        candidates = club_to_canonical_names.get(club_key, [])
        chosen_name = raw_name
        applied = False

        # Try same club
        if candidates:
            best_name, score = best_match(candidates, raw_name)
            if best_name is not None and score >= thr_same_club:
                if best_name != raw_name:
                    chosen_name = best_name
                    applied = True
        # Fallback: global search stricter
        if not applied:
            best_name, score = best_match(global_canonical, raw_name)
            if best_name is not None and score >= thr_global:
                if best_name != raw_name:
                    chosen_name = best_name
                    applied = True

        if applied:
            updates += 1
        corrected_names.append(chosen_name)

    # Apply corrections
    df_fb["Player"] = corrected_names
    df_fb.drop(columns=["club_key"], inplace=True)

    # Save
    out_dir = os.path.dirname(PATH_FBREF_CLEAN)
    out_path = OUT_PATH
    df_fb.to_csv(out_path, index=False, sep=";", encoding="utf-8")
    print(f"Updated {updates} of {total} player names. Saved to: {out_path}")


if __name__ == "__main__":
    main()












