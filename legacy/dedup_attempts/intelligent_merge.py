import pandas as pd
import re
import unicodedata
from difflib import SequenceMatcher
from collections import defaultdict

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

def find_matching_players(df, threshold=0.85):
    """
    Encontra jogadores que são provavelmente a mesma pessoa
    """
    matches = []
    
    # Agrupa por clube para reduzir falsos positivos
    for clube in df['Clube'].dropna().unique():
        clube_df = df[df['Clube'] == clube].copy()
        
        if len(clube_df) < 2:
            continue
            
        # Compara todos os pares de jogadores do mesmo clube
        for i, row1 in clube_df.iterrows():
            for j, row2 in clube_df.iterrows():
                if i >= j:  # Evita comparar com ele mesmo e duplicatas
                    continue
                
                name1 = row1['Player_normalized']
                name2 = row2['Player_normalized']
                fb_name1 = row1['fb_Player_normalized']
                fb_name2 = row2['fb_Player_normalized']
                
                # Calcula similaridade entre diferentes combinações
                similarities = []
                
                if name1 and name2:
                    similarities.append(('Player', similarity(name1, name2)))
                if name1 and fb_name2:
                    similarities.append(('Player_fb', similarity(name1, fb_name2)))
                if fb_name1 and name2:
                    similarities.append(('fb_Player', similarity(fb_name1, name2)))
                if fb_name1 and fb_name2:
                    similarities.append(('fb_fb', similarity(fb_name1, fb_name2)))
                
                # Pega a maior similaridade
                if similarities:
                    best_match_type, best_score = max(similarities, key=lambda x: x[1])
                    
                    if best_score >= threshold:
                        matches.append({
                            'index1': i,
                            'index2': j,
                            'name1': row1['Player'],
                            'name2': row2['Player'],
                            'fb_name1': row1['fb_Player'],
                            'fb_name2': row2['fb_Player'],
                            'similarity': best_score,
                            'match_type': best_match_type,
                            'clube': clube
                        })
    
    return matches

def merge_matching_players(df, matches):
    """
    Merge jogadores que foram identificados como a mesma pessoa
    """
    merged_rows = []
    processed_indices = set()
    
    for match in matches:
        idx1, idx2 = match['index1'], match['index2']
        
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
        merged_row['_merge_status'] = 'merged'
        merged_row['_original_names'] = f"{row1['Player']} | {row2['Player']}"
        
        merged_rows.append(merged_row)
        processed_indices.add(idx1)
        processed_indices.add(idx2)
    
    # Adiciona linhas não processadas
    for idx, row in df.iterrows():
        if idx not in processed_indices:
            row_copy = row.copy()
            row_copy['_merge_status'] = 'original'
            row_copy['_original_names'] = row['Player']
            merged_rows.append(row_copy)
    
    return pd.DataFrame(merged_rows)

# Caminhos dos arquivos
PATH_ANTIJOIN = r"C:\Users\IGOR\Desktop\UFSC\TCC\dados\clubes\outcome\antijoin_only_clubes_fbref.csv"
PATH_MERGED = r"C:\Users\IGOR\Desktop\UFSC\TCC\dados\clubes\outcome\atletas_fbref_merged.csv"
OUT_PATH = r"C:\Users\IGOR\Desktop\UFSC\TCC\dados\clubes\outcome\intelligent_merged_players.csv"

print("Carregando arquivos...")
# Carrega os arquivos
antijoin_df = pd.read_csv(PATH_ANTIJOIN, encoding="utf-8")
merged_df = pd.read_csv(PATH_MERGED, encoding="utf-8")

print(f"Antijoin: {len(antijoin_df)} linhas")
print(f"Merged: {len(merged_df)} linhas")

# Normaliza nomes nos dois dataframes
print("Normalizando nomes...")
antijoin_df['Player_normalized'] = antijoin_df['Player'].apply(normalize_name)
antijoin_df['fb_Player_normalized'] = antijoin_df['fb_Player'].apply(normalize_name)
merged_df['Player_normalized'] = merged_df['Player'].apply(normalize_name)
merged_df['fb_Player_normalized'] = merged_df['fb_Player'].apply(normalize_name)

# Combina os dataframes
print("Combinando dataframes...")
combined_df = pd.concat([antijoin_df, merged_df], ignore_index=True)

print(f"Total de linhas antes do merge inteligente: {len(combined_df)}")

# Encontra jogadores similares
print("Procurando jogadores similares...")
matches = find_matching_players(combined_df, threshold=0.85)

print(f"Encontrados {len(matches)} pares de jogadores similares:")

# Mostra os matches encontrados
for match in matches[:10]:  # Mostra os primeiros 10
    print(f"  {match['name1']} <-> {match['name2']} (similaridade: {match['similarity']:.2f}) [{match['clube']}]")

# Faz o merge inteligente
print("Fazendo merge inteligente...")
final_df = merge_matching_players(combined_df, matches)

print(f"Dataframe final: {len(final_df)} linhas")
print(f"Jogadores merged: {len([x for x in final_df['_merge_status'] if x == 'merged'])}")

# Salva o resultado
final_df.to_csv(OUT_PATH, index=False, encoding="utf-8")
print(f"Arquivo salvo em: {OUT_PATH}")

# Mostra estatísticas
print("\nEstatísticas:")
print(f"Total de jogadores únicos: {len(final_df)}")
print(f"Jogadores com dados completos: {len(final_df[final_df['fb_Player'].notna()])}")
print(f"Jogadores apenas com dados de clube: {len(final_df[final_df['fb_Player'].isna()])}")
