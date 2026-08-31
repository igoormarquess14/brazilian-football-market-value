import unicodedata
from difflib import SequenceMatcher
from typing import Any, Dict, List, Tuple

import pandas as pd

PATH_CLUBES = r"C:\Users\IGOR\Desktop\UFSC\TCC\dados\clubes\outcome\todos_clubes_2024_final.csv"
PATH_FBREF = r"C:\Users\IGOR\Desktop\UFSC\TCC\dados\minutes_played\fbref_playing_time_cleaned.csv"
PATH_ANTIJOIN = r"C:\Users\IGOR\Desktop\UFSC\TCC\dados\clubes\outcome\antijoin_only_clubes_fbref.csv"
OUT_PATH = r"C:\Users\IGOR\Desktop\UFSC\TCC\dados\clubes\outcome\fuzzy_corrected_merged.csv"


def strip_accents(text: Any) -> str:
    if pd.isna(text):
        return ""
    s = str(text)
    s = s.replace("\uFFFD", " ").replace("", " ")
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


def main() -> None:
    # Read inputs
    cl = pd.read_csv(PATH_CLUBES, encoding="utf-8")
    fb = pd.read_csv(PATH_FBREF, sep=";", encoding="utf-8")
    anti = pd.read_csv(PATH_ANTIJOIN, encoding="utf-8")

    # Separate left_only and right_only from anti-join
    left_only = anti[anti["_merge"] == "left_only"].copy()
    right_only = anti[anti["_merge"] == "right_only"].copy()

    print(f"Left-only (clubes): {len(left_only)}")
    print(f"Right-only (fbref): {len(right_only)}")

    # Build club blocks for efficient matching
    cl["club_key"] = cl["Clube"].map(normalize_key)
    fb["club_key"] = fb["Squad"].map(normalize_key)

    club_blocks: Dict[str, List[Tuple[int, str]]] = {}
    for idx, row in fb.iterrows():
        key = row["club_key"]
        if key not in club_blocks:
            club_blocks[key] = []
        club_blocks[key].append((idx, row["Player"]))

    # Find fuzzy matches for left_only (clubes without fbref)
    fuzzy_matches: List[Dict[str, Any]] = []
    name_threshold = 0.85
    club_threshold = 0.80

    for _, row in left_only.iterrows():
        if pd.isna(row["Player"]) or pd.isna(row["Clube"]):
            continue
            
        club_key = normalize_key(row["Clube"])
        player_name = str(row["Player"])
        
        # Find similar clubs
        best_match_idx = None
        best_score = 0.0
        
        for fb_club_key, candidates in club_blocks.items():
            club_sim = similarity(club_key, fb_club_key)
            if club_sim < club_threshold:
                continue
                
            for fb_idx, fb_name in candidates:
                name_sim = similarity(player_name, fb_name)
                combined_score = (name_sim * 0.7) + (club_sim * 0.3)
                
                if combined_score > best_score and name_sim >= name_threshold:
                    best_score = combined_score
                    best_match_idx = fb_idx

        if best_match_idx is not None:
            fb_row = fb.iloc[best_match_idx]
            fuzzy_matches.append({
                "clubes_idx": row.name,
                "fbref_idx": best_match_idx,
                "clubes_player": player_name,
                "fbref_player": fb_row["Player"],
                "clubes_club": row["Clube"],
                "fbref_club": fb_row["Squad"],
                "score": best_score
            })

    print(f"Found {len(fuzzy_matches)} fuzzy matches")

    # Create corrected merged dataset
    # Start with exact matches (from original merge)
    exact_matches = cl.merge(
        fb.add_prefix("fb_"),
        left_on=["Player", "Clube", "age"],
        right_on=["fb_Player", "fb_Squad", "fb_Age"],
        how="inner"
    )

    # Add fuzzy matches
    for match in fuzzy_matches:
        cl_row = cl.iloc[match["clubes_idx"]]
        fb_row = fb.iloc[match["fbref_idx"]]
        
        # Create combined row
        combined_row = cl_row.to_dict()
        for col in fb.columns:
            combined_row[f"fb_{col}"] = fb_row[col]
        combined_row["fuzzy_match_score"] = match["score"]
        
        exact_matches = pd.concat([exact_matches, pd.DataFrame([combined_row])], ignore_index=True)

    # Add remaining unmatched from both sides
    matched_cl_indices = set(exact_matches.index.tolist())
    matched_fb_indices = set()
    
    for match in fuzzy_matches:
        matched_fb_indices.add(match["fbref_idx"])

    # Remaining unmatched from clubes
    remaining_cl = cl[~cl.index.isin(matched_cl_indices)].copy()
    for col in fb.columns:
        remaining_cl[f"fb_{col}"] = None

    # Remaining unmatched from fbref
    remaining_fb = fb[~fb.index.isin(matched_fb_indices)].copy()
    for col in cl.columns:
        remaining_fb[col] = None
    # Rename fbref columns to have fb_ prefix
    remaining_fb = remaining_fb.add_prefix("fb_")

    # Combine all
    final = pd.concat([exact_matches, remaining_cl, remaining_fb], ignore_index=True)

    # Save
    final.to_csv(OUT_PATH, index=False, encoding="utf-8")
    print(f"Saved fuzzy-corrected merge to: {OUT_PATH} with {len(final)} rows")


if __name__ == "__main__":
    main()
