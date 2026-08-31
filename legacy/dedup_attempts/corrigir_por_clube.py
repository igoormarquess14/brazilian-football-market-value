import csv

def corrigir_por_clube():
    """
    Corrige o matching verificando apenas se o clube bate
    """
    
    print("CORRIGINDO MATCHING POR CLUBE")
    print("="*40)
    
    # Mapeamento de clubes
    mapeamento_clubes = {
        'atletico_mineiro': 'atlético mineiro',
        'sao_paulo': 'são paulo', 
        'palmeiras': 'palmeiras',
        'flamengo': 'flamengo',
        'corinthians': 'corinthians',
        'fluminense': 'fluminense',
        'gremio': 'grêmio',
        'internacional': 'internacional',
        'botafogo': 'botafogo',
        'santos': 'santos',
        'vasco': 'vasco da gama',
        'fortaleza': 'fortaleza',
        'bahia': 'bahia',
        'cruzeiro': 'cruzeiro',
        'ceara': 'ceará',
        'bragantino': 'red bull bragantino',
        'sport': 'sport recife',
        'vitoria': 'vitória',
        'juventude': 'juventude',
        'mirassol': 'mirassol'
    }
    
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
    
    # Colunas de performance
    colunas_performance = [
        'Rk', 'Nation_performance', 'Pos', 'Squad', 'Age', 'Born', 
        'MP', 'Min', 'Mn/MP', 'Min%', '90s', 'Starts', 'Mn/Start', 
        'Compl', 'Subs', 'Mn/Sub', 'unSub', 'PPM', 'onG', 'onGA', 
        '+/-', '+/-90', 'On-Off', 'onxG', 'onxGA', 'xG+/-', 
        'xG+/-90', 'On-Off.1', 'Matches'
    ]
    
    matches_encontrados = 0
    dados_corrigidos = []
    
    for i, transf_row in enumerate(dados_transf):
        if i % 100 == 0:
            print(f"Processando... {i}/{len(dados_transf)}")
        
        # Copiar dados de transferências
        row_corrigida = transf_row.copy()
        
        # Adicionar colunas de performance vazias
        for col in colunas_performance:
            row_corrigida[col] = ''
        
        # Obter dados do jogador
        nome_transf = transf_row.get('Player', '').strip()
        clube_transf = transf_row.get('Clube', '').strip()
        
        # Obter clube mapeado
        clube_mapeado = mapeamento_clubes.get(clube_transf, clube_transf)
        
        # Buscar match apenas no mesmo clube
        melhor_match = None
        
        for perf_row in dados_perf:
            clube_perf = perf_row.get('Squad', '').strip().lower()
            nome_perf = perf_row.get('Player', '').strip()
            
            # Verificar se o clube bate
            clube_mapeado_lower = clube_mapeado.lower()
            
            if (clube_mapeado_lower in clube_perf or 
                clube_perf in clube_mapeado_lower or
                (clube_mapeado_lower == 'atlético mineiro' and 'atlético' in clube_perf) or
                (clube_mapeado_lower == 'são paulo' and 'são paulo' in clube_perf) or
                (clube_mapeado_lower == 'grêmio' and 'grêmio' in clube_perf)):
                
                # Se o clube bate, verificar se o nome é similar
                if (nome_transf.lower() == nome_perf.lower() or
                    nome_transf.lower() in nome_perf.lower() or
                    nome_perf.lower() in nome_transf.lower()):
                    
                    melhor_match = perf_row
                    break
        
        # Se encontrou match, copiar dados
        if melhor_match:
            for col in colunas_performance:
                if col in melhor_match:
                    row_corrigida[col] = melhor_match[col]
            
            matches_encontrados += 1
            
            # Debug para casos específicos
            if 'everson' in nome_transf.lower():
                print(f"EVERSON MATCH:")
                print(f"  Transfer: {nome_transf} - {clube_transf}")
                print(f"  Performance: {melhor_match.get('Player', '')} - {melhor_match.get('Squad', '')}")
                print()
        
        dados_corrigidos.append(row_corrigida)
    
    print(f"\nMatches encontrados: {matches_encontrados}")
    print(f"Taxa de match: {(matches_encontrados/len(dados_transf)*100):.1f}%")
    
    # Salvar arquivo corrigido
    arquivo_saida = r"C:\Users\IGOR\Desktop\UFSC\TCC\dados\clubes\outcome\atletas_completo_corrigido_2024.csv"
    
    with open(arquivo_saida, 'w', newline='', encoding='utf-8') as f:
        fieldnames = list(dados_corrigidos[0].keys())
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(dados_corrigidos)
    
    print(f"Arquivo corrigido salvo: {arquivo_saida}")
    
    return dados_corrigidos

if __name__ == "__main__":
    dados = corrigir_por_clube()

