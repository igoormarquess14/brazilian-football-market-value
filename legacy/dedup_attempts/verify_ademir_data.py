import pandas as pd

# Caminho do arquivo
PATH_INPUT = r"C:\Users\IGOR\Desktop\UFSC\TCC\dados\clubes\outcome\final_merged_fixed.csv"

print("Carregando arquivo...")
df = pd.read_csv(PATH_INPUT, encoding="utf-8")

# Encontra a linha do Ademir
ademir_row = df[df['Player'] == 'Ademir'].iloc[0]

print("Dados do Ademir:")
print(f"Clube: {ademir_row['Clube']}")
print(f"Player: {ademir_row['Player']}")
print(f"Idade: {ademir_row['age']}")
print(f"Posição: {ademir_row['Position']}")
print(f"Valor: {ademir_row['Value (€)']}")
print(f"Valor_Num: {ademir_row['Value_Num']}")

print("\nDados do FBref:")
print(f"fb_Rk: {ademir_row['fb_Rk']}")
print(f"fb_Player: {ademir_row['fb_Player']}")
print(f"fb_Nation: {ademir_row['fb_Nation']}")
print(f"fb_Pos: {ademir_row['fb_Pos']}")
print(f"fb_Squad: {ademir_row['fb_Squad']}")
print(f"fb_Age: {ademir_row['fb_Age']}")
print(f"fb_Born: {ademir_row['fb_Born']}")
print(f"fb_MP: {ademir_row['fb_MP']}")
print(f"fb_Min: {ademir_row['fb_Min']}")
print(f"fb_Mn/MP: {ademir_row['fb_Mn/MP']}")
print(f"fb_Min%: {ademir_row['fb_Min%']}")
print(f"fb_90s: {ademir_row['fb_90s']}")
print(f"fb_Starts: {ademir_row['fb_Starts']}")
print(f"fb_Mn/Start: {ademir_row['fb_Mn/Start']}")
print(f"fb_Compl: {ademir_row['fb_Compl']}")
print(f"fb_Subs: {ademir_row['fb_Subs']}")
print(f"fb_Mn/Sub: {ademir_row['fb_Mn/Sub']}")
print(f"fb_unSub: {ademir_row['fb_unSub']}")
print(f"fb_PPM: {ademir_row['fb_PPM']}")
print(f"fb_onG: {ademir_row['fb_onG']}")
print(f"fb_onGA: {ademir_row['fb_onGA']}")
print(f"fb_+/-: {ademir_row['fb_+/-']}")
print(f"fb_+/-90: {ademir_row['fb_+/-90']}")
print(f"fb_On-Off: {ademir_row['fb_On-Off']}")
print(f"fb_onxG: {ademir_row['fb_onxG']}")
print(f"fb_onxGA: {ademir_row['fb_onxGA']}")
print(f"fb_xG+/-: {ademir_row['fb_xG+/-']}")
print(f"fb_xG+/-90: {ademir_row['fb_xG+/-90']}")
print(f"fb_On-Off.1: {ademir_row['fb_On-Off.1']}")
print(f"fb_Matches: {ademir_row['fb_Matches']}")

print(f"\nStatus do merge: {ademir_row['_merge_status']}")
print(f"Nomes originais: {ademir_row['_original_names']}")
print(f"Similaridade: {ademir_row['_similarity']}")

# Verifica se há dados do FBref
has_fbref_data = pd.notna(ademir_row['fb_Player']) and ademir_row['fb_Player'] != ''
print(f"\nTem dados do FBref: {has_fbref_data}")

if has_fbref_data:
    print("✅ Os dados do FBref estão preenchidos corretamente!")
else:
    print("❌ Os dados do FBref estão vazios!")


