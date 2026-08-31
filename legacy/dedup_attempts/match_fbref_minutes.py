import os
import sys
import re
import unicodedata
from difflib import SequenceMatcher
from typing import List, Tuple, Dict, Optional, Any

import pandas as pd


def read_csv_robust(path: str, sep: Optional[str] = None, expected_cols: Optional[List[str]] = None) -> pd.DataFrame:
    """Read a CSV trying multiple encodings and separators.

    - Tries UTF-8, then Latin-1 encodings
    - If sep not provided, tries "," then ";"
    - Validates expected columns if provided
    """
    encodings = ["utf-8", "latin-1", "cp1252"]
    seps = [",", ";"] if sep is None else [sep]
    last_err: Optional[Exception] = None
    for enc in encodings:
        for s in seps:
            try:
                df = pd.read_csv(path, sep=s, encoding=enc)
                if expected_cols is not None:
                    missing = [c for c in expected_cols if c not in df.columns]
                    if missing:
                        # Not the right parse; keep trying
                        last_err = ValueError(f"Missing columns {missing} with sep={s} enc={enc}")
                        continue
                return df
            except Exception as e:  # noqa: BLE001 - robust read
                last_err = e
                continue
    if last_err is not None:
        raise last_err
    raise RuntimeError("Failed to read CSV with any attempted encoding/separator")


_non_alnum_re = re.compile(r"[^a-z0-9]+", re.IGNORECASE)


def normalize_text(value: Any) -> str:
    """Normalize strings for fuzzy matching.

    - Lowercase
    - Replace underscores and punctuation with spaces
    - Remove diacritics
    - Collapse multiple spaces
    - Strip
    """
    if pd.isna(value):
        return ""
    text = str(value)
    # Replace replacement char and unusual bytes
    text = text.replace("\uFFFD", " ")  # replacement char 
    text = text.replace("�", " ")
    # Lower
    text = text.lower()
    # Convert underscores to spaces
    text = text.replace("_", " ")
    # Remove diacritics
    text = unicodedata.normalize("NFKD", text)
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    # Keep only alnum
    text = _non_alnum_re.sub(" ", text)
    # Collapse whitespace
    text = " ".join(text.split())
    return text.strip()


def token_sort_key(text: str) -> str:
    tokens = [t for t in text.split() if t]
    tokens.sort()
    return " ".join(tokens)


def token_set_key(text: str) -> str:
    tokens = sorted(set(t for t in text.split() if t))
    return " ".join(tokens)


def similarity(a: str, b: str) -> float:
    """Compute a token-set ratio using SequenceMatcher; returns 0..1."""
    if not a or not b:
        return 0.0
    a_key = token_set_key(normalize_text(a))
    b_key = token_set_key(normalize_text(b))
    return SequenceMatcher(None, a_key, b_key).ratio()


def best_match(candidates: List[Tuple[int, str]], query: str) -> Tuple[Optional[int], float]:
    """Return (index_in_candidates_list, score) for best candidate vs query.

    candidates: list of (row_index_in_df2, candidate_name)
    query: string to match from df1
    """
    best_list_index: Optional[int] = None
    best_score = -1.0
    for list_index, (_df2_row_index, candidate_name) in enumerate(candidates):
        s = similarity(query, candidate_name)
        if s > best_score:
            best_score = s
            best_list_index = list_index
    return best_list_index, best_score if best_score >= 0 else 0.0


def build_club_blocks(df2: pd.DataFrame, club_col: str) -> Tuple[Dict[str, List[int]], List[str]]:
    """Build mapping from normalized club key to list of row indices in df2.
    Returns (club_key_to_indices, unique_club_keys)
    """
    club_key_to_indices: Dict[str, List[int]] = {}
    keys: List[str] = []
    for idx, val in enumerate(df2[club_col].astype(str).tolist()):
        key = normalize_text(val)
        if key not in club_key_to_indices:
            club_key_to_indices[key] = []
            keys.append(key)
        club_key_to_indices[key].append(idx)
    return club_key_to_indices, keys


def find_similar_club_keys(club_key: str, all_keys: List[str], min_similarity: float) -> List[str]:
    """Find club keys in all_keys similar to the given club_key above threshold."""
    results: List[Tuple[str, float]] = []
    for other in all_keys:
        score = SequenceMatcher(None, token_set_key(club_key), token_set_key(other)).ratio()
        if score >= min_similarity:
            results.append((other, score))
    results.sort(key=lambda x: x[1], reverse=True)
    return [k for k, _ in results]


def main() -> None:
    # Input paths
    path_clubes = r"C:\Users\IGOR\Desktop\UFSC\TCC\dados\clubes\outcome\todos_clubes_2024_final.csv"
    path_fbref = r"C:\Users\IGOR\Desktop\UFSC\TCC\dados\minutes_played\fbref_playing_time.csv"

    # Read dataframes
    df1 = read_csv_robust(path_clubes, sep=",", expected_cols=["Clube", "Player"])  # first file is comma-separated
    df2 = read_csv_robust(path_fbref, sep=";", expected_cols=["Player", "Squad"])   # fbref export is semicolon-separated

    # Prepare normalized columns
    df1["name_key"] = df1["Player"].map(normalize_text)
    df1["club_key"] = df1["Clube"].map(normalize_text)
    df2["name_key"] = df2["Player"].map(normalize_text)
    df2["club_key"] = df2["Squad"].map(normalize_text)

    # Build club blocks from df2 to reduce search space
    club_blocks, all_df2_club_keys = build_club_blocks(df2, "Squad")

    # Cache for similar club keys per df1 club
    similar_club_cache: Dict[str, List[str]] = {}

    # Tiered thresholds to broaden matches in subsequent passes
    club_similarity_tiers = [0.85, 0.75, 0.65]
    player_similarity_tiers = [0.90, 0.85, 0.80]

    matches: List[Dict[str, Any]] = []

    def last_name_key(text: str) -> str:
        toks = token_set_key(normalize_text(text)).split()
        return toks[-1] if toks else ""

    for _club_thr in club_similarity_tiers:
        for _player_thr in player_similarity_tiers:
            start_count = len(matches)
            for _, row in df1.iterrows():
                # Skip if already matched this df1 row (by name+club combo)
                already = any((m["Clube"] == row.get("Clube") and normalize_text(m["Player_df1"]) == normalize_text(row.get("Player"))) for m in matches)
                if already:
                    continue

                club_key = row["club_key"]
                name = row["Player"]

                if club_key not in similar_club_cache:
                    similar_club_cache[club_key] = find_similar_club_keys(club_key, all_df2_club_keys, _club_thr)
                candidate_club_keys = similar_club_cache[club_key]

                candidate_indices: List[Tuple[int, str]] = []
                for ckey in candidate_club_keys:
                    for idx in club_blocks.get(ckey, []):
                        candidate_indices.append((idx, df2.at[idx, "Player"]))

                # If no candidates by club, try a broader scan with stricter player name threshold
                broader_scan = False
                if not candidate_indices and _club_thr <= 0.70:
                    broader_scan = True
                    candidate_indices = [(idx, df2.at[idx, "Player"]) for idx in range(len(df2))]

                if not candidate_indices:
                    continue

                best_idx_in_candidates, score = best_match(candidate_indices, name)
                if best_idx_in_candidates is None:
                    continue

                # Fallback: accept slightly lower score if last name matches exactly
                if score < _player_thr:
                    if score >= max(0.78, _player_thr - 0.05):
                        if last_name_key(name) and last_name_key(name) == last_name_key(candidate_indices[best_idx_in_candidates][1]):
                            pass
                        else:
                            continue
                    else:
                        continue

                df2_row_index = candidate_indices[best_idx_in_candidates][0]
                row2 = df2.loc[df2_row_index]

                # If we used a broader scan, enforce the club similarity on the chosen row
                if broader_scan:
                    club_sim = SequenceMatcher(None, token_set_key(row["club_key"]), token_set_key(row2["club_key"]))
                    if club_sim.ratio() < 0.70:
                        continue

                matches.append({
                    "Clube": row.get("Clube"),
                    "Player_df1": name,
                    "Squad": row2.get("Squad"),
                    "Player_df2": row2.get("Player"),
                    "player_similarity": round(float(score), 4),
                    "MP": row2.get("MP"),
                    "Min": row2.get("Min"),
                })

            # If we added enough in this pass, we can stop early
            if len(matches) - start_count > 0 and len(matches) >= 550:
                break
        if len(matches) >= 550:
            break

    matched_count = len(matches)

    # Abort if not enough matches
    required_matches = 550
    if matched_count < required_matches:
        print(f"Only {matched_count} matches found (< {required_matches}). Aborting.")
        sys.exit(2)

    out_path = os.path.join(os.path.dirname(path_clubes), "matches_fbref_merged.csv")
    out_df = pd.DataFrame(matches)
    out_df.to_csv(out_path, index=False, encoding="utf-8")

    print(f"Matched players: {matched_count}")
    print(f"Saved merged matches to: {out_path}")


if __name__ == "__main__":
    main()


