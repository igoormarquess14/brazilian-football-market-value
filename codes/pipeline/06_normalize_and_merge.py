from pathlib import Path
import pandas as pd
import re
import unicodedata
from difflib import SequenceMatcher

PROJECT_ROOT = Path(__file__).resolve().parents[2]

def normalize_name(name):
    """
    Normalizes player names to make matching easier:
    1. Fixes corrupted special characters
    2. Removes accents and special characters
    3. Converts to lowercase
    4. Removes extra spaces
    """
    if pd.isna(name) or name == '':
        return ''

    # Convert to string if it isn't one
    name = str(name).strip()

    # Fixes for specific corrupted characters (mojibake -> accented char;
    # both sides are literal characters, nothing here to translate)
    corrections = {
        'Ã¡': 'á', 'Ã©': 'é', 'Ã­': 'í', 'Ã³': 'ó', 'Ãº': 'ú',
        'Ã ': 'à', 'Ã¨': 'è', 'Ã¬': 'ì', 'Ã²': 'ò', 'Ã¹': 'ù',
        'Ã¢': 'â', 'Ãª': 'ê', 'Ã®': 'î', 'Ã´': 'ô', 'Ã»': 'û',
        'Ã§': 'ç', 'Ã±': 'ñ', 'Ã¼': 'ü', 'Ã¶': 'ö', 'Ã¤': 'ä',
        'Ã¥': 'å', 'Ã¦': 'æ', 'Ã¸': 'ø', 'Ã¥': 'å',
        'Ã': 'í', 'Ã': 'ó', 'Ã': 'ú', 'Ã': 'ñ',
        'Ã¶': 'ö', 'Ã¤': 'ä', 'Ã¼': 'ü',
        'Ã§': 'ç', 'Ã±': 'ñ', 'Ã¡': 'á',
        'Ã©': 'é', 'Ã­': 'í', 'Ã³': 'ó', 'Ãº': 'ú',
        'Ã¢': 'â', 'Ãª': 'ê', 'Ã®': 'î', 'Ã´': 'ô', 'Ã»': 'û',
        'Ã ': 'à', 'Ã¨': 'è', 'Ã¬': 'ì', 'Ã²': 'ò', 'Ã¹': 'ù',
        'Ã§': 'ç', 'Ã±': 'ñ', 'Ã¼': 'ü', 'Ã¶': 'ö', 'Ã¤': 'ä',
        'Ã¥': 'å', 'Ã¦': 'æ', 'Ã¸': 'ø'
    }
    
    # Apply the fixes
    for wrong, correct in corrections.items():
        name = name.replace(wrong, correct)

    # Remove accents and special characters
    name = unicodedata.normalize('NFD', name)
    name = ''.join(c for c in name if unicodedata.category(c) != 'Mn')

    # Convert to lowercase
    name = name.lower()

    # Remove special characters except spaces and hyphens
    name = re.sub(r'[^\w\s\-]', '', name)

    # Remove extra spaces
    name = ' '.join(name.split())

    return name

def similarity(a, b):
    """Computes similarity between two names"""
    return SequenceMatcher(None, a, b).ratio()

def find_best_match(target_name, candidate_names, threshold=0.8):
    """
    Finds the best match for a name among a list of candidates
    """
    if not target_name or not candidate_names:
        return None, 0.0
    
    best_match = None
    best_score = 0.0
    
    for candidate in candidate_names:
        if candidate and candidate != '':
            score = similarity(target_name, candidate)
            if score > best_score and score >= threshold:
                best_score = score
                best_match = candidate
    
    return best_match, best_score

# File paths
PATH_ANTIJOIN = str(PROJECT_ROOT / "dados" / "clubes" / "outcome" / "antijoin_only_clubes_fbref.csv")
PATH_MERGED = str(PROJECT_ROOT / "dados" / "clubes" / "outcome" / "atletas_fbref_merged.csv")
OUT_PATH = str(PROJECT_ROOT / "dados" / "clubes" / "outcome" / "final_merged_players.csv")

print("Loading files...")
# Load the files
antijoin_df = pd.read_csv(PATH_ANTIJOIN, encoding="utf-8")
merged_df = pd.read_csv(PATH_MERGED, encoding="utf-8")

print(f"Antijoin: {len(antijoin_df)} rows")
print(f"Merged: {len(merged_df)} rows")

# Normalize names in both dataframes
print("Normalizing names...")
antijoin_df['Player_normalized'] = antijoin_df['Player'].apply(normalize_name)
antijoin_df['fb_Player_normalized'] = antijoin_df['fb_Player'].apply(normalize_name)
merged_df['Player_normalized'] = merged_df['Player'].apply(normalize_name)
merged_df['fb_Player_normalized'] = merged_df['fb_Player'].apply(normalize_name)

# Build a list of unique names for matching
all_names = set()
all_names.update(antijoin_df['Player_normalized'].dropna())
all_names.update(antijoin_df['fb_Player_normalized'].dropna())
all_names.update(merged_df['Player_normalized'].dropna())
all_names.update(merged_df['fb_Player_normalized'].dropna())

print(f"Total unique names: {len(all_names)}")

# Combine the dataframes
print("Combining dataframes...")
combined_df = pd.concat([antijoin_df, merged_df], ignore_index=True)

# Remove duplicates based on normalized name and club
print("Removing duplicates...")
combined_df = combined_df.drop_duplicates(subset=['Player_normalized', 'Clube'], keep='first')

print(f"Final dataframe: {len(combined_df)} rows")

# Save the result
combined_df.to_csv(OUT_PATH, index=False, encoding="utf-8")
print(f"File saved to: {OUT_PATH}")

# Show a few normalization examples
print("\nNormalization examples:")
examples = combined_df[['Player', 'Player_normalized']].drop_duplicates().head(10)
for _, row in examples.iterrows():
    if row['Player'] != row['Player_normalized']:
        print(f"'{row['Player']}' -> '{row['Player_normalized']}'")
