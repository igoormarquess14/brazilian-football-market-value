import csv
from collections import defaultdict

def diagnostico_matching():
    """
    Diagnóstico para entender por que temos poucos matches
    """
    
    print("DIAGNÓSTICO DE MATCHING")
    print("="*40)
    
    # Carregar dados de performance
    arquivo_perf = r"C:\Users\IGOR\Desktop\UFSC\TCC\dados\minutes_played\fbref_playing_time.csv"
    dados_perf = []
    
    with open(arquivo_perf, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f, delimiter=';')
        for row in reader:
            dados_perf.append(row)
    
    print(f"Dados de performance: {len(dados_perf)} registros")
    
    # Carregar dados de transferências
    arquivo_transf = r"C:\Users\IGOR\Desktop\UFSC\TCC\dados\clubes\outcome\todos_clubes_2024_final.csv"
    dados_transf = []
    
    with open(arquivo_transf, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            dados_transf.append(row)
    
    print(f"Dados de transferências: {len(dados_transf)} registros")
    
    # 1. ANÁLISE DE CLUBES
    print("\n1. ANÁLISE DE CLUBES")
    print("-" * 30)
    
    clubes_perf = set()
    for row in dados_perf:
        clube = row.get('Squad', '').strip()
        if clube:
            clubes_perf.add(clube)
    
    clubes_transf = set()
    for row in dados_transf:
        clube = row.get('Clube', '').strip()
        if clube:
            clubes_transf.add(clube)
    
    print(f"Clubes únicos na performance: {len(clubes_perf)}")
    print("Primeiros 10 clubes da performance:")
    for i, clube in enumerate(sorted(clubes_perf)[:10]):
        print(f"  {i+1}. {clube}")
    
    print(f"\nClubes únicos nas transferências: {len(clubes_transf)}")
    print("Clubes das transferências:")
    for clube in sorted(clubes_transf):
        print(f"  - {clube}")
    
    # 2. ANÁLISE DE NOMES
    print("\n2. ANÁLISE DE NOMES")
    print("-" * 30)
    
    print("Primeiros 10 nomes da performance:")
    for i, row in enumerate(dados_perf[:10]):
        nome = row.get('Player', '').strip()
        clube = row.get('Squad', '').strip()
        print(f"  {i+1}. {nome} - {clube}")
    
    print("\nPrimeiros 10 nomes das transferências:")
    for i, row in enumerate(dados_transf[:10]):
        nome = row.get('Player', '').strip()
        clube = row.get('Clube', '').strip()
        print(f"  {i+1}. {nome} - {clube}")
    
    # 3. ANÁLISE DE IDADES
    print("\n3. ANÁLISE DE IDADES")
    print("-" * 30)
    
    print("Primeiras 10 idades da performance:")
    for i, row in enumerate(dados_perf[:10]):
        idade = row.get('Age', '').strip()
        print(f"  {i+1}. {idade}")
    
    print("\nPrimeiras 10 idades das transferências:")
    for i, row in enumerate(dados_transf[:10]):
        idade = row.get('age', '').strip()
        print(f"  {i+1}. {idade}")
    
    # 4. TESTE DE MATCHING SIMPLES
    print("\n4. TESTE DE MATCHING SIMPLES")
    print("-" * 30)
    
    matches_teste = 0
    for i, transf_row in enumerate(dados_transf[:50]):  # Testar apenas os primeiros 50
        nome_transf = transf_row.get('Player', '').strip()
        clube_transf = transf_row.get('Clube', '').strip()
        
        for perf_row in dados_perf:
            nome_perf = perf_row.get('Player', '').strip()
            clube_perf = perf_row.get('Squad', '').strip()
            
            # Match exato
            if nome_transf.lower() == nome_perf.lower():
                matches_teste += 1
                print(f"MATCH EXATO: {nome_transf} - {clube_transf} -> {nome_perf} - {clube_perf}")
                break
    
    print(f"Matches exatos nos primeiros 50: {matches_teste}")
    
    # 5. ANÁLISE DE PROBLEMAS ESPECÍFICOS
    print("\n5. ANÁLISE DE PROBLEMAS ESPECÍFICOS")
    print("-" * 30)
    
    # Verificar se há problemas de encoding
    print("Verificando problemas de encoding...")
    for i, row in enumerate(dados_perf[:5]):
        for key, value in row.items():
            if '' in str(value):
                print(f"Problema de encoding em {key}: {value}")
    
    for i, row in enumerate(dados_transf[:5]):
        for key, value in row.items():
            if '' in str(value):
                print(f"Problema de encoding em {key}: {value}")

if __name__ == "__main__":
    diagnostico_matching()

