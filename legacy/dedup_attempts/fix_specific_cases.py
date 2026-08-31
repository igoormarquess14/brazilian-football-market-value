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

# Caminho do arquivo
PATH_INPUT = r"C:\Users\IGOR\Desktop\UFSC\TCC\dados\clubes\outcome\final_merged_fixed.csv"
PATH_OUTPUT = r"C:\Users\IGOR\Desktop\UFSC\TCC\dados\clubes\outcome\final_merged_complete.csv"

print("Carregando arquivo...")
df = pd.read_csv(PATH_INPUT, encoding="utf-8")

print(f"Total de linhas antes da correção: {len(df)}")

# Casos específicos que precisam de merge
specific_cases = [
    {'clube': 'bragantino', 'club_name': 'Eduardo', 'fbref_name': 'Eduardo Sasha'},
    {'clube': 'bragantino', 'club_name': 'Fernando', 'fbref_name': 'Fernando Costa'},
    {'clube': 'vasco', 'club_name': 'Paulinho Paula', 'fbref_name': 'Paulinho'}
]

print("Procurando casos específicos...")

duplicates_found = []

for case in specific_cases:
    clube = case['clube']
    club_name = case['club_name']
    fbref_name = case['fbref_name']
    
    # Procura pela linha com dados de clube
    club_row = df[(df['Clube'] == clube) & (df['Player'] == club_name) & 
                  (df['fb_Player'].isna() | (df['fb_Player'] == ''))]
    
    # Procura pela linha com dados do FBref
    fbref_row = df[(df['fb_Squad'] == clube) & (df['fb_Player'] == fbref_name) & 
                   (df['Player'].isna() | (df['Player'] == ''))]
    
    if len(club_row) > 0 and len(fbref_row) > 0:
        club_idx = club_row.index[0]
        fbref_idx = fbref_row.index[0]
        
        # Calcula similaridade
        club_name_norm = normalize_name(club_name)
        fbref_name_norm = normalize_name(fbref_name)
        sim = similarity(club_name_norm, fbref_name_norm)
        
        duplicates_found.append({
            'club_index': club_idx,
            'fbref_index': fbref_idx,
            'clube': clube,
            'club_name': club_name,
            'fbref_name': fbref_name,
            'similarity': sim
        })
        
        print(f"  Encontrado: {clube} - '{club_name}' <-> '{fbref_name}' (similaridade: {sim:.2f})")
    else:
        print(f"  Não encontrado: {clube} - '{club_name}' <-> '{fbref_name}'")

print(f"\nTotal de casos encontrados: {len(duplicates_found)}")

# Merge os duplicados encontrados
if duplicates_found:
    print("\nFazendo merge dos casos específicos...")
    
    # Cria uma lista de índices para remover
    indices_to_remove = []
    merged_rows = []
    
    for dup in duplicates_found:
        club_idx = dup['club_index']
        fbref_idx = dup['fbref_index']
        
        if club_idx in indices_to_remove or fbref_idx in indices_to_remove:
            continue
        
        # Pega as duas linhas
        club_row = df.iloc[club_idx].copy()
        fbref_row = df.iloc[fbref_idx].copy()
        
        # Cria uma nova linha combinando as informações
        merged_row = club_row.copy()
        
        # Preenche campos vazios da club_row com dados da fbref_row
        for col in df.columns:
            if pd.isna(merged_row[col]) or merged_row[col] == '':
                if not pd.isna(fbref_row[col]) and fbref_row[col] != '':
                    merged_row[col] = fbref_row[col]
        
        # Marca como merged
        merged_row['_merge_status'] = 'merged_duplicate'
        merged_row['_original_names'] = f"{club_row['Player']} | {fbref_row['fb_Player']}"
        merged_row['_similarity'] = dup['similarity']
        
        merged_rows.append(merged_row)
        indices_to_remove.extend([club_idx, fbref_idx])
    
    # Remove as linhas duplicadas e adiciona as merged
    df_clean = df.drop(indices_to_remove)
    df_final = pd.concat([df_clean, pd.DataFrame(merged_rows)], ignore_index=True)
    
    print(f"Total de linhas após correção: {len(df_final)}")
    print(f"Jogadores merged: {len(merged_rows)}")
    
    # Salva o resultado
    df_final.to_csv(PATH_OUTPUT, index=False, encoding="utf-8")
    print(f"Arquivo salvo em: {PATH_OUTPUT}")
    
    # Mostra estatísticas
    print(f"\nEstatísticas finais:")
    print(f"Total de jogadores únicos: {len(df_final)}")
    print(f"Jogadores com dados completos: {len(df_final[df_final['fb_Player'].notna()])}")
    print(f"Jogadores apenas com dados de clube: {len(df_final[df_final['fb_Player'].isna()])}")
    
    # Mostra os casos que foram merged
    print(f"\nCasos que foram merged:")
    merged_all = df_final[df_final['_merge_status'] == 'merged_duplicate']
    for i, row in merged_all.iterrows():
        print(f"  {row['_original_names']} (similaridade: {row['_similarity']:.2f})")
    
else:
    print("Nenhum caso específico encontrado para merge.")
