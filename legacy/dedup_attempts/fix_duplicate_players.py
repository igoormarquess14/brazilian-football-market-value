import pandas as pd
import re
import unicodedata
from difflib import SequenceMatcher

def normalize_name(name):
    """
    Normaliza nomes de jogadores para facilitar o matching
    """
    if pd.isna(name) or name == '':
        return ''
    
    name = str(name).strip()
    
    # Correções específicas para caracteres corrompidos
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
    
    # Aplica correções
    for wrong, correct in corrections.items():
        name = name.replace(wrong, correct)
    
    # Remove acentos e caracteres especiais
    name = unicodedata.normalize('NFD', name)
    name = ''.join(c for c in name if unicodedata.category(c) != 'Mn')
    
    # Converte para minúsculas
    name = name.lower()
    
    # Remove caracteres especiais exceto espaços e hífens
    name = re.sub(r'[^\w\s\-]', '', name)
    
    # Remove espaços extras
    name = ' '.join(name.split())
    
    return name

def similarity(a, b):
    """Calcula similaridade entre dois nomes"""
    if not a or not b:
        return 0.0
    return SequenceMatcher(None, a, b).ratio()

def find_duplicate_players(df):
    """
    Encontra jogadores que aparecem em linhas separadas (uma com dados de clube, outra com dados do FBref)
    """
    duplicates = []
    
    # Agrupa por clube
    for clube in df['Clube'].dropna().unique():
        clube_df = df[df['Clube'] == clube].copy()
        
        if len(clube_df) < 2:
            continue
        
        # Procura por pares onde um tem dados de clube e outro tem dados do FBref
        for i, row1 in clube_df.iterrows():
            for j, row2 in clube_df.iterrows():
                if i >= j:
                    continue
                
                # Verifica se um tem dados de clube e outro tem dados do FBref
                has_club_data1 = pd.notna(row1['Player']) and row1['Player'] != ''
                has_fbref_data1 = pd.notna(row1['fb_Player']) and row1['fb_Player'] != ''
                has_club_data2 = pd.notna(row2['Player']) and row2['Player'] != ''
                has_fbref_data2 = pd.notna(row2['fb_Player']) and row2['fb_Player'] != ''
                
                # Caso 1: row1 tem dados de clube, row2 tem dados do FBref
                if has_club_data1 and has_fbref_data2 and not has_fbref_data1 and not has_club_data2:
                    name1 = row1['Player_normalized']
                    name2 = row2['fb_Player_normalized']
                    sim = similarity(name1, name2)
                    
                    if sim >= 0.7:  # Similaridade alta
                        duplicates.append({
                            'index1': i,
                            'index2': j,
                            'clube': clube,
                            'club_name': row1['Player'],
                            'fbref_name': row2['fb_Player'],
                            'similarity': sim,
                            'type': 'club_to_fbref'
                        })
                
                # Caso 2: row2 tem dados de clube, row1 tem dados do FBref
                elif has_club_data2 and has_fbref_data1 and not has_fbref_data2 and not has_club_data1:
                    name1 = row1['fb_Player_normalized']
                    name2 = row2['Player_normalized']
                    sim = similarity(name1, name2)
                    
                    if sim >= 0.7:  # Similaridade alta
                        duplicates.append({
                            'index1': i,
                            'index2': j,
                            'clube': clube,
                            'club_name': row2['Player'],
                            'fbref_name': row1['fb_Player'],
                            'similarity': sim,
                            'type': 'fbref_to_club'
                        })
    
    return duplicates

def merge_duplicate_players(df, duplicates):
    """
    Merge jogadores duplicados em uma única linha
    """
    merged_rows = []
    processed_indices = set()
    
    for dup in duplicates:
        idx1, idx2 = dup['index1'], dup['index2']
        
        if idx1 in processed_indices or idx2 in processed_indices:
            continue
        
        # Pega as duas linhas
        row1 = df.iloc[idx1].copy()
        row2 = df.iloc[idx2].copy()
        
        # Cria uma nova linha combinando as informações
        merged_row = row1.copy()
        
        # Preenche campos vazios da row1 com dados da row2
        for col in df.columns:
            if pd.isna(merged_row[col]) or merged_row[col] == '':
                if not pd.isna(row2[col]) and row2[col] != '':
                    merged_row[col] = row2[col]
        
        # Marca como merged
        merged_row['_merge_status'] = 'merged_duplicate'
        merged_row['_original_names'] = f"{row1['Player']} | {row2['fb_Player']}"
        merged_row['_similarity'] = dup['similarity']
        
        merged_rows.append(merged_row)
        processed_indices.add(idx1)
        processed_indices.add(idx2)
    
    # Adiciona linhas não processadas
    for idx, row in df.iterrows():
        if idx not in processed_indices:
            row_copy = row.copy()
            row_copy['_merge_status'] = 'original'
            row_copy['_original_names'] = row['Player']
            row_copy['_similarity'] = 0.0
            merged_rows.append(row_copy)
    
    return pd.DataFrame(merged_rows)

# Caminho do arquivo
PATH_INPUT = r"C:\Users\IGOR\Desktop\UFSC\TCC\dados\clubes\outcome\final_merged_clean.csv"
PATH_OUTPUT = r"C:\Users\IGOR\Desktop\UFSC\TCC\dados\clubes\outcome\final_merged_fixed.csv"

print("Carregando arquivo...")
df = pd.read_csv(PATH_INPUT, encoding="utf-8")

print(f"Total de linhas antes da correção: {len(df)}")

# Encontra jogadores duplicados
print("Procurando jogadores duplicados...")
duplicates = find_duplicate_players(df)

print(f"Encontrados {len(duplicates)} pares de jogadores duplicados:")

for dup in duplicates:
    print(f"  {dup['clube']}: '{dup['club_name']}' <-> '{dup['fbref_name']}' (similaridade: {dup['similarity']:.2f})")

# Merge os duplicados
if duplicates:
    print("\nFazendo merge dos duplicados...")
    df_fixed = merge_duplicate_players(df, duplicates)
    
    print(f"Total de linhas após correção: {len(df_fixed)}")
    print(f"Jogadores merged: {len([x for x in df_fixed['_merge_status'] if x == 'merged_duplicate'])}")
    
    # Salva o resultado
    df_fixed.to_csv(PATH_OUTPUT, index=False, encoding="utf-8")
    print(f"Arquivo salvo em: {PATH_OUTPUT}")
    
    # Mostra estatísticas
    print(f"\nEstatísticas finais:")
    print(f"Total de jogadores únicos: {len(df_fixed)}")
    print(f"Jogadores com dados completos: {len(df_fixed[df_fixed['fb_Player'].notna()])}")
    print(f"Jogadores apenas com dados de clube: {len(df_fixed[df_fixed['fb_Player'].isna()])}")
    
else:
    print("Nenhum jogador duplicado encontrado.")
