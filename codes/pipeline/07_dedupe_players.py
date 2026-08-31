from pathlib import Path
import pandas as pd
import re
import unicodedata
from difflib import SequenceMatcher

PROJECT_ROOT = Path(__file__).resolve().parents[2]

def normalize_name(name):
    """
    Normalizes player names to make matching easier
    """
    if pd.isna(name) or name == '':
        return ''

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
    if not a or not b:
        return 0.0
    return SequenceMatcher(None, a, b).ratio()

# File path
PATH_INPUT = str(PROJECT_ROOT / "dados" / "clubes" / "outcome" / "final_merged_clean.csv")
PATH_OUTPUT = str(PROJECT_ROOT / "dados" / "clubes" / "outcome" / "final_merged_fixed.csv")

print("Loading file...")
df = pd.read_csv(PATH_INPUT, encoding="utf-8")

print(f"Total rows before the fix: {len(df)}")

# Identify specific cases where we have club data in one row and FBref data in another
print("Looking for specific duplication cases...")

duplicates_found = []

# Look for rows with club data (Player filled in, fb_Player empty)
club_rows = df[(df['Player'].notna()) & (df['Player'] != '') &
               (df['fb_Player'].isna() | (df['fb_Player'] == ''))].copy()

# Look for rows with FBref data (Player empty, fb_Player filled in)
fbref_rows = df[(df['Player'].isna() | (df['Player'] == '')) &
                (df['fb_Player'].notna()) & (df['fb_Player'] != '')].copy()

print(f"Rows with club data: {len(club_rows)}")
print(f"Rows with FBref data: {len(fbref_rows)}")

# For each club row, look for an FBref row from the same club
for _, club_row in club_rows.iterrows():
    club_name = club_row['Player']
    club_clube = club_row['Clube']

    # Look for FBref rows that have the same club in the fb_Squad field
    matching_fbref = fbref_rows[fbref_rows['fb_Squad'] == club_clube]

    for _, fbref_row in matching_fbref.iterrows():
        fbref_name = fbref_row['fb_Player']

        # Normalize the names
        club_name_norm = normalize_name(club_name)
        fbref_name_norm = normalize_name(fbref_name)

        # Compute similarity
        sim = similarity(club_name_norm, fbref_name_norm)

        # Check whether they are similar (same base name, or one contains the other)
        is_similar = (sim >= 0.5 or
                     club_name_norm in fbref_name_norm or
                     fbref_name_norm in club_name_norm or
                     (len(club_name_norm.split()) > 0 and len(fbref_name_norm.split()) > 0 and
                      club_name_norm.split()[0] == fbref_name_norm.split()[0]))

        if is_similar:
            duplicates_found.append({
                'club_index': club_row.name,
                'fbref_index': fbref_row.name,
                'clube': club_clube,
                'club_name': club_name,
                'fbref_name': fbref_name,
                'similarity': sim
            })

print(f"Found {len(duplicates_found)} duplication cases:")

for dup in duplicates_found:
    print(f"  {dup['clube']}: '{dup['club_name']}' <-> '{dup['fbref_name']}' (similarity: {dup['similarity']:.2f})")

# Merge the duplicates found
if duplicates_found:
    print("\nMerging duplicates...")

    # Build a list of indices to remove
    indices_to_remove = []
    merged_rows = []

    for dup in duplicates_found:
        club_idx = dup['club_index']
        fbref_idx = dup['fbref_index']

        if club_idx in indices_to_remove or fbref_idx in indices_to_remove:
            continue

        # Get both rows
        club_row = df.iloc[club_idx].copy()
        fbref_row = df.iloc[fbref_idx].copy()

        # Build a new row combining the information
        merged_row = club_row.copy()

        # Fill empty fields in club_row with data from fbref_row
        for col in df.columns:
            if pd.isna(merged_row[col]) or merged_row[col] == '':
                if not pd.isna(fbref_row[col]) and fbref_row[col] != '':
                    merged_row[col] = fbref_row[col]

        # Flag as merged (the value below is written into the output CSV
        # as data — do not translate it)
        merged_row['_merge_status'] = 'merged_duplicate'
        merged_row['_original_names'] = f"{club_row['Player']} | {fbref_row['fb_Player']}"
        merged_row['_similarity'] = dup['similarity']

        merged_rows.append(merged_row)
        indices_to_remove.extend([club_idx, fbref_idx])

    # Remove the duplicated rows and add the merged ones
    df_clean = df.drop(indices_to_remove)
    df_final = pd.concat([df_clean, pd.DataFrame(merged_rows)], ignore_index=True)

    print(f"Total rows after the fix: {len(df_final)}")
    print(f"Players merged: {len(merged_rows)}")

    # Save the result
    df_final.to_csv(PATH_OUTPUT, index=False, encoding="utf-8")
    print(f"File saved to: {PATH_OUTPUT}")

    # Show stats
    print(f"\nFinal stats:")
    print(f"Total unique players: {len(df_final)}")
    print(f"Players with complete data: {len(df_final[df_final['fb_Player'].notna()])}")
    print(f"Players with only club data: {len(df_final[df_final['fb_Player'].isna()])}")

    # Show the cases that were merged
    print(f"\nCases that were merged:")
    for i, row in enumerate(merged_rows):
        print(f"  {i+1}. {row['_original_names']} (similarity: {row['_similarity']:.2f})")

else:
    print("No duplication cases found.")
