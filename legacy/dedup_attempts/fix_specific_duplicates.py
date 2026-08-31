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
PATH_INPUT = r"C:\Users\IGOR\Desktop\UFSC\TCC\dados\clubes\outcome\final_merged_clean.csv"
PATH_OUTPUT = r"C:\Users\IGOR\Desktop\UFSC\TCC\dados\clubes\outcome\final_merged_fixed.csv"

print("Carregando arquivo...")
df = pd.read_csv(PATH_INPUT, encoding="utf-8")

print(f"Total de linhas antes da correção: {len(df)}")

# Identifica casos específicos onde temos dados de clube em uma linha e dados do FBref em outra
print("Procurando casos específicos de duplicação...")

duplicates_found = []

# Procura por linhas com dados de clube (Player preenchido, fb_Player vazio)
club_rows = df[(df['Player'].notna()) & (df['Player'] != '') & 
               (df['fb_Player'].isna() | (df['fb_Player'] == ''))].copy()

# Procura por linhas com dados do FBref (Player vazio, fb_Player preenchido)
fbref_rows = df[(df['Player'].isna() | (df['Player'] == '')) & 
                (df['fb_Player'].notna()) & (df['fb_Player'] != '')].copy()

print(f"Linhas com dados de clube: {len(club_rows)}")
print(f"Linhas com dados do FBref: {len(fbref_rows)}")

# Para cada linha de clube, procura por uma linha do FBref que seja do mesmo clube
for _, club_row in club_rows.iterrows():
    club_name = club_row['Player']
    club_clube = club_row['Clube']
    
    # Procura por linhas do FBref que tenham o mesmo clube
    matching_fbref = fbref_rows[fbref_rows['fb_Squad'] == club_clube]
    
    for _, fbref_row in matching_fbref.iterrows():
        fbref_name = fbref_row['fb_Player']
        
        # Normaliza os nomes
        club_name_norm = normalize_name(club_name)
        fbref_name_norm = normalize_name(fbref_name)
        
        # Calcula similaridade
        sim = similarity(club_name_norm, fbref_name_norm)
        
        # Verifica se são similares (mesmo nome base ou contém um ao outro)
        is_similar = (sim >= 0.6 or 
                     club_name_norm in fbref_name_norm or 
                     fbref_name_norm in club_name_norm or
                     club_name_norm.split()[0] == fbref_name_norm.split()[0])
        
        if is_similar:
            duplicates_found.append({
                'club_index': club_row.name,
                'fbref_index': fbref_row.name,
                'clube': club_clube,
                'club_name': club_name,
                'fbref_name': fbref_name,
                'similarity': sim
            })

print(f"Encontrados {len(duplicates_found)} casos de duplicação:")

for dup in duplicates_found:
    print(f"  {dup['clube']}: '{dup['club_name']}' <-> '{dup['fbref_name']}' (similaridade: {dup['similarity']:.2f})")

# Merge os duplicados encontrados
if duplicates_found:
    print("\nFazendo merge dos duplicados...")
    
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
    for i, row in enumerate(merged_rows):
        print(f"  {i+1}. {row['_original_names']} (similaridade: {row['_similarity']:.2f})")
    
else:
    print("Nenhum caso de duplicação encontrado.")
