import pandas as pd

# Caminho do arquivo
PATH_INPUT = r"C:\Users\IGOR\Desktop\UFSC\TCC\dados\clubes\outcome\final_merged_fixed.csv"

print("Carregando arquivo...")
df = pd.read_csv(PATH_INPUT, encoding="utf-8")

print(f"Total de linhas: {len(df)}")

# Verifica jogadores com dados completos (tanto clube quanto FBref)
complete_data = df[(df['Player'].notna()) & (df['Player'] != '') & 
                   (df['fb_Player'].notna()) & (df['fb_Player'] != '')]

print(f"Jogadores com dados completos: {len(complete_data)}")

# Verifica jogadores apenas com dados de clube
club_only = df[(df['Player'].notna()) & (df['Player'] != '') & 
               (df['fb_Player'].isna() | (df['fb_Player'] == ''))]

print(f"Jogadores apenas com dados de clube: {len(club_only)}")

# Verifica jogadores apenas com dados do FBref
fbref_only = df[(df['Player'].isna() | (df['Player'] == '')) & 
                (df['fb_Player'].notna()) & (df['fb_Player'] != '')]

print(f"Jogadores apenas com dados do FBref: {len(fbref_only)}")

# Verifica jogadores merged
merged_players = df[df['_merge_status'] == 'merged_duplicate']
print(f"Jogadores que foram merged: {len(merged_players)}")

print("\nJogadores que foram merged:")
for _, row in merged_players.iterrows():
    print(f"  {row['_original_names']} (similaridade: {row['_similarity']:.2f})")

# Verifica se há casos onde deveria ter dados do FBref mas não tem
print("\nVerificando casos problemáticos...")

# Procura por jogadores que têm dados de clube mas não têm dados do FBref
# mas que deveriam ter (baseado no clube)
problematic_cases = []

for _, row in club_only.iterrows():
    clube = row['Clube']
    player_name = row['Player']
    
    # Procura se existe uma linha do FBref para o mesmo clube
    fbref_match = df[(df['fb_Squad'] == clube) & 
                     (df['fb_Player'].notna()) & (df['fb_Player'] != '')]
    
    if len(fbref_match) > 0:
        # Verifica se algum nome é similar
        for _, fbref_row in fbref_match.iterrows():
            fbref_name = fbref_row['fb_Player']
            if player_name.lower() in fbref_name.lower() or fbref_name.lower() in player_name.lower():
                problematic_cases.append({
                    'clube': clube,
                    'club_name': player_name,
                    'fbref_name': fbref_name,
                    'club_index': row.name,
                    'fbref_index': fbref_row.name
                })

if problematic_cases:
    print(f"Encontrados {len(problematic_cases)} casos que podem precisar de merge:")
    for case in problematic_cases:
        print(f"  {case['clube']}: '{case['club_name']}' <-> '{case['fbref_name']}'")
else:
    print("Nenhum caso problemático encontrado.")

# Mostra alguns exemplos de jogadores com dados completos
print(f"\nExemplos de jogadores com dados completos:")
examples = complete_data.head(5)
for _, row in examples.iterrows():
    print(f"  {row['Clube']}: {row['Player']} | {row['fb_Player']}")

print(f"\nEstatísticas finais:")
print(f"Total de jogadores únicos: {len(df)}")
print(f"Jogadores com dados completos: {len(complete_data)} ({len(complete_data)/len(df)*100:.1f}%)")
print(f"Jogadores apenas com dados de clube: {len(club_only)} ({len(club_only)/len(df)*100:.1f}%)")
print(f"Jogadores apenas com dados do FBref: {len(fbref_only)} ({len(fbref_only)/len(df)*100:.1f}%)")


