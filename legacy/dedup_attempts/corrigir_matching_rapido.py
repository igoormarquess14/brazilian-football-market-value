import csv
from collections import defaultdict

def corrigir_matching_rapido():
    """
    Corrige o matching de forma mais eficiente
    """
    
    print("CORRIGINDO MATCHING - VERSÃO RÁPIDA")
    print("="*50)
    
    # Carregar dados de performance
    arquivo_perf = r"C:\Users\IGOR\Desktop\UFSC\TCC\dados\minutes_played\fbref_playing_time.csv"
    dados_perf = []
    
    with open(arquivo_perf, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f, delimiter=';')
        for row in reader:
            dados_perf.append(row)
    
    print(f"Dados de performance carregados: {len(dados_perf)} registros")
    
    # Criar índice por clube para busca mais rápida
    indice_por_clube = defaultdict(list)
    for i, row in enumerate(dados_perf):
        clube = row.get('Squad', '').lower()
        indice_por_clube[clube].append(i)
    
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
    
    # Carregar dados de transferências
    arquivo_transf = r"C:\Users\IGOR\Desktop\UFSC\TCC\dados\clubes\outcome\todos_clubes_2024_final.csv"
    dados_transf = []
    
    with open(arquivo_transf, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            dados_transf.append(row)
    
    print(f"Dados de transferências carregados: {len(dados_transf)} registros")
    
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
        if i % 50 == 0:
            print(f"Processando... {i}/{len(dados_transf)}")
        
        # Copiar dados de transferências
        row_corrigida = transf_row.copy()
        
        # Adicionar colunas de performance vazias
        for col in colunas_performance:
            row_corrigida[col] = ''
        
        # Buscar match
        nome_transf = transf_row.get('Player', '').strip()
        clube_transf = transf_row.get('Clube', '').strip()
        idade_transf = transf_row.get('age', '')
        pos_transf = transf_row.get('Position', '').strip()
        
        # Obter clube mapeado
        clube_mapeado = mapeamento_clubes.get(clube_transf, clube_transf)
        
        # Buscar apenas nos dados do mesmo clube
        candidatos_indices = []
        for clube_perf, indices in indice_por_clube.items():
            if (clube_mapeado.lower() in clube_perf or 
                clube_perf in clube_mapeado.lower() or
                'atlético' in clube_perf and 'atletico' in clube_mapeado.lower()):
                candidatos_indices.extend(indices)
        
        # Buscar match entre candidatos
        melhor_match = None
        melhor_score = 0
        
        for idx in candidatos_indices:
            perf_row = dados_perf[idx]
            nome_perf = perf_row.get('Player', '').strip()
            idade_perf = perf_row.get('Age', '')
            pos_perf = perf_row.get('Pos', '').strip()
            
            score = 0
            
            # 1. Nome similar
            if nome_transf.lower() == nome_perf.lower():
                score += 1.0
            elif nome_transf.lower() in nome_perf.lower() or nome_perf.lower() in nome_transf.lower():
                score += 0.8
            else:
                # Verificar similaridade básica
                chars_iguais = sum(1 for a, b in zip(nome_transf.lower(), nome_perf.lower()) if a == b)
                if len(nome_transf) > 0 and len(nome_perf) > 0:
                    similaridade = chars_iguais / max(len(nome_transf), len(nome_perf))
                    if similaridade > 0.7:
                        score += 0.6
            
            # 2. Idade compatível
            try:
                idade_t = int(idade_transf)
                idade_p = int(idade_perf)
                if abs(idade_t - idade_p) <= 1:
                    score += 0.3
            except:
                pass
            
            # 3. Posição compatível
            pos_transf_lower = pos_transf.lower()
            pos_perf_lower = pos_perf.lower()
            
            if (('goleiro' in pos_transf_lower and 'gk' in pos_perf_lower) or
                ('zagueiro' in pos_transf_lower and 'df' in pos_perf_lower) or
                ('volante' in pos_transf_lower and 'mf' in pos_perf_lower) or
                ('meia' in pos_transf_lower and 'mf' in pos_perf_lower) or
                ('ponta' in pos_transf_lower and 'fw' in pos_perf_lower) or
                ('atacante' in pos_transf_lower and 'fw' in pos_perf_lower)):
                score += 0.2
            
            if score > melhor_score and score >= 0.8:  # Threshold alto
                melhor_score = score
                melhor_match = perf_row
        
        # Se encontrou match, copiar dados
        if melhor_match:
            for col in colunas_performance:
                if col in melhor_match:
                    row_corrigida[col] = melhor_match[col]
            
            matches_encontrados += 1
            
            # Debug para casos específicos
            if 'everson' in nome_transf.lower():
                print(f"EVERSON MATCH:")
                print(f"  Transfer: {nome_transf} - {clube_transf} - {idade_transf} - {pos_transf}")
                print(f"  Performance: {melhor_match.get('Player', '')} - {melhor_match.get('Squad', '')} - {melhor_match.get('Age', '')} - {melhor_match.get('Pos', '')}")
                print(f"  Score: {melhor_score:.2f}")
                print()
        
        dados_corrigidos.append(row_corrigida)
    
    print(f"\nMatches encontrados: {matches_encontrados}")
    print(f"Taxa de match: {(matches_encontrados/len(dados_transf)*100):.1f}%")
    
    # Salvar arquivo corrigido
    arquivo_saida = r"C:\Users\IGOR\Desktop\UFSC\TCC\dados\clubes\outcome\atletas_completo_corrigido_2024.csv"
    
    if dados_corrigidos:
        with open(arquivo_saida, 'w', newline='', encoding='utf-8') as f:
            fieldnames = list(dados_corrigidos[0].keys())
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(dados_corrigidos)
        
        print(f"Arquivo corrigido salvo: {arquivo_saida}")
    
    return dados_corrigidos

if __name__ == "__main__":
    dados = corrigir_matching_rapido()

