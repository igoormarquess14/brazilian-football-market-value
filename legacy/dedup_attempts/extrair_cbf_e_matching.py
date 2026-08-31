import csv
import requests
from bs4 import BeautifulSoup
import time
import unicodedata
from difflib import SequenceMatcher

def remover_acentos(texto):
    """Remove acentos de um texto"""
    if not texto:
        return ''
    return unicodedata.normalize('NFD', str(texto)).encode('ascii', 'ignore').decode('ascii').lower()

def similaridade_nomes(nome1, nome2):
    """Calcula similaridade entre nomes"""
    if not nome1 or not nome2:
        return 0
    return SequenceMatcher(None, str(nome1).lower(), str(nome2).lower()).ratio()

def extrair_dados_cbf():
    """
    Extrai dados da CBF (nome completo + clube)
    """
    print("EXTRAINDO DADOS DA CBF")
    print("="*30)
    
    url = "https://www.cbf.com.br/futebol-brasileiro/atletas/campeonato-brasileiro/serie-a/2025"
    
    try:
        print("Fazendo requisição para a CBF...")
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        print("Parseando HTML...")
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Procurar por elementos que contenham nomes de atletas
        atletas_cbf = []
        
        # Tentar diferentes seletores
        seletores = [
            'div[class*="atleta"]',
            'div[class*="player"]',
            'div[class*="jogador"]',
            'span[class*="nome"]',
            'p[class*="nome"]',
            'td[class*="nome"]',
            'div[class*="nome"]'
        ]
        
        for seletor in seletores:
            elementos = soup.select(seletor)
            if elementos:
                print(f"Encontrados {len(elementos)} elementos com seletor: {seletor}")
                for elemento in elementos:
                    texto = elemento.get_text().strip()
                    if texto and len(texto) > 3:
                        atletas_cbf.append(texto)
                break
        
        # Se não encontrou com seletores específicos, tentar buscar em toda a página
        if not atletas_cbf:
            print("Tentando busca geral na página...")
            todos_textos = soup.get_text()
            linhas = todos_textos.split('\n')
            
            for linha in linhas:
                linha = linha.strip()
                if len(linha) > 5 and len(linha) < 50:
                    # Verificar se parece com nome de atleta
                    if any(palavra in linha.lower() for palavra in ['fc', 'atlético', 'são paulo', 'flamengo', 'palmeiras']):
                        atletas_cbf.append(linha)
        
        print(f"Total de atletas encontrados: {len(atletas_cbf)}")
        
        # Salvar dados da CBF
        arquivo_cbf = r"C:\Users\IGOR\Desktop\UFSC\TCC\dados\clubes\outcome\atletas_cbf_2025.csv"
        
        with open(arquivo_cbf, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['Nome_Completo', 'Clube'])
            
            for atleta in atletas_cbf[:100]:  # Limitar a 100 para teste
                writer.writerow([atleta, ''])  # Clube será preenchido depois
        
        print(f"Dados da CBF salvos em: {arquivo_cbf}")
        return atletas_cbf
        
    except Exception as e:
        print(f"Erro ao extrair dados da CBF: {e}")
        print("Criando dados de exemplo...")
        
        # Criar dados de exemplo para teste
        atletas_exemplo = [
            "Gabriel Barbosa - Flamengo",
            "Éverson - Atlético Mineiro", 
            "Gabriel Jesus - Arsenal",
            "Neymar Jr - Al-Hilal",
            "Vinicius Jr - Real Madrid"
        ]
        
        arquivo_cbf = r"C:\Users\IGOR\Desktop\UFSC\TCC\dados\clubes\outcome\atletas_cbf_2025.csv"
        
        with open(arquivo_cbf, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['Nome_Completo', 'Clube'])
            
            for atleta in atletas_exemplo:
                if ' - ' in atleta:
                    nome, clube = atleta.split(' - ', 1)
                    writer.writerow([nome.strip(), clube.strip()])
                else:
                    writer.writerow([atleta, ''])
        
        print(f"Dados de exemplo salvos em: {arquivo_cbf}")
        return atletas_exemplo

def adicionar_nome_completo_transferencias():
    """
    Adiciona coluna nome_completo no dataframe de transferências
    """
    print("\nADICIONANDO NOME COMPLETO - TRANSFERÊNCIAS")
    print("="*50)
    
    # Carregar dados da CBF
    arquivo_cbf = r"C:\Users\IGOR\Desktop\UFSC\TCC\dados\clubes\outcome\atletas_cbf_2025.csv"
    atletas_cbf = []
    
    try:
        with open(arquivo_cbf, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                atletas_cbf.append(row)
    except:
        print("Arquivo da CBF não encontrado, criando dados de exemplo...")
        atletas_cbf = [
            {'Nome_Completo': 'Gabriel Barbosa', 'Clube': 'Flamengo'},
            {'Nome_Completo': 'Éverson', 'Clube': 'Atlético Mineiro'},
            {'Nome_Completo': 'Gabriel Jesus', 'Clube': 'Arsenal'},
            {'Nome_Completo': 'Neymar Jr', 'Clube': 'Al-Hilal'},
            {'Nome_Completo': 'Vinicius Jr', 'Clube': 'Real Madrid'}
        ]
    
    print(f"Dados da CBF carregados: {len(atletas_cbf)} registros")
    
    # Carregar dados de transferências
    arquivo_transf = r"C:\Users\IGOR\Desktop\UFSC\TCC\dados\clubes\outcome\todos_clubes_2024_final.csv"
    dados_transf = []
    
    with open(arquivo_transf, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            dados_transf.append(row)
    
    print(f"Dados de transferências carregados: {len(dados_transf)} registros")
    
    # Adicionar coluna nome_completo
    for transf_row in dados_transf:
        nome_transf = transf_row.get('Player', '').strip()
        clube_transf = transf_row.get('Clube', '').strip()
        
        melhor_match = None
        melhor_score = 0
        
        for cbf_row in atletas_cbf:
            nome_cbf = cbf_row.get('Nome_Completo', '').strip()
            clube_cbf = cbf_row.get('Clube', '').strip()
            
            # Verificar se o clube bate
            clube_bate = False
            if clube_transf == 'atletico_mineiro' and 'atlético' in clube_cbf.lower():
                clube_bate = True
            elif clube_transf == 'sao_paulo' and 'são paulo' in clube_cbf.lower():
                clube_bate = True
            elif clube_transf == 'gremio' and 'grêmio' in clube_cbf.lower():
                clube_bate = True
            elif clube_transf == 'flamengo' and 'flamengo' in clube_cbf.lower():
                clube_bate = True
            elif clube_transf == 'palmeiras' and 'palmeiras' in clube_cbf.lower():
                clube_bate = True
            elif clube_transf == 'corinthians' and 'corinthians' in clube_cbf.lower():
                clube_bate = True
            elif clube_transf == 'fluminense' and 'fluminense' in clube_cbf.lower():
                clube_bate = True
            elif clube_transf == 'internacional' and 'internacional' in clube_cbf.lower():
                clube_bate = True
            elif clube_transf == 'botafogo' and 'botafogo' in clube_cbf.lower():
                clube_bate = True
            elif clube_transf == 'santos' and 'santos' in clube_cbf.lower():
                clube_bate = True
            elif clube_transf == 'fortaleza' and 'fortaleza' in clube_cbf.lower():
                clube_bate = True
            elif clube_transf == 'bahia' and 'bahia' in clube_cbf.lower():
                clube_bate = True
            elif clube_transf == 'cruzeiro' and 'cruzeiro' in clube_cbf.lower():
                clube_bate = True
            elif clube_transf == 'bragantino' and 'bragantino' in clube_cbf.lower():
                clube_bate = True
            elif clube_transf == 'sport' and 'sport' in clube_cbf.lower():
                clube_bate = True
            elif clube_transf == 'vasco' and 'vasco' in clube_cbf.lower():
                clube_bate = True
            elif clube_transf == 'juventude' and 'juventude' in clube_cbf.lower():
                clube_bate = True
            elif clube_transf == 'mirassol' and 'mirassol' in clube_cbf.lower():
                clube_bate = True
            elif clube_transf == 'ceara' and 'ceará' in clube_cbf.lower():
                clube_bate = True
            elif clube_transf == 'vitoria' and 'vitória' in clube_cbf.lower():
                clube_bate = True
            
            if not clube_bate:
                continue
            
            # Calcular similaridade do nome
            similaridade = similaridade_nomes(nome_transf, nome_cbf)
            
            if similaridade > melhor_score and similaridade > 0.6:
                melhor_score = similaridade
                melhor_match = nome_cbf
        
        # Adicionar nome completo
        if melhor_match:
            transf_row['Nome_Completo'] = melhor_match
        else:
            transf_row['Nome_Completo'] = nome_transf  # Usar nome original se não encontrar
    
    # Salvar arquivo atualizado
    arquivo_saida = r"C:\Users\IGOR\Desktop\UFSC\TCC\dados\clubes\outcome\todos_clubes_2024_com_nome_completo.csv"
    
    with open(arquivo_saida, 'w', newline='', encoding='utf-8') as f:
        fieldnames = list(dados_transf[0].keys())
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(dados_transf)
    
    print(f"Arquivo com nome completo salvo: {arquivo_saida}")
    return dados_transf

def adicionar_nome_completo_performance():
    """
    Adiciona coluna nome_completo no dataframe de performance
    """
    print("\nADICIONANDO NOME COMPLETO - PERFORMANCE")
    print("="*50)
    
    # Carregar dados da CBF
    arquivo_cbf = r"C:\Users\IGOR\Desktop\UFSC\TCC\dados\clubes\outcome\atletas_cbf_2025.csv"
    atletas_cbf = []
    
    try:
        with open(arquivo_cbf, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                atletas_cbf.append(row)
    except:
        print("Arquivo da CBF não encontrado, criando dados de exemplo...")
        atletas_cbf = [
            {'Nome_Completo': 'Gabriel Barbosa', 'Clube': 'Flamengo'},
            {'Nome_Completo': 'Éverson', 'Clube': 'Atlético Mineiro'},
            {'Nome_Completo': 'Gabriel Jesus', 'Clube': 'Arsenal'},
            {'Nome_Completo': 'Neymar Jr', 'Clube': 'Al-Hilal'},
            {'Nome_Completo': 'Vinicius Jr', 'Clube': 'Real Madrid'}
        ]
    
    print(f"Dados da CBF carregados: {len(atletas_cbf)} registros")
    
    # Carregar dados de performance
    arquivo_perf = r"C:\Users\IGOR\Desktop\UFSC\TCC\dados\minutes_played\fbref_playing_time.csv"
    dados_perf = []
    
    with open(arquivo_perf, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f, delimiter=';')
        for row in reader:
            dados_perf.append(row)
    
    print(f"Dados de performance carregados: {len(dados_perf)} registros")
    
    # Adicionar coluna nome_completo
    for perf_row in dados_perf:
        nome_perf = perf_row.get('Player', '').strip()
        clube_perf = perf_row.get('Squad', '').strip()
        
        melhor_match = None
        melhor_score = 0
        
        for cbf_row in atletas_cbf:
            nome_cbf = cbf_row.get('Nome_Completo', '').strip()
            clube_cbf = cbf_row.get('Clube', '').strip()
            
            # Verificar se o clube bate
            clube_bate = False
            if 'atlético' in clube_perf.lower() and 'atlético' in clube_cbf.lower():
                clube_bate = True
            elif 'são paulo' in clube_perf.lower() and 'são paulo' in clube_cbf.lower():
                clube_bate = True
            elif 'grêmio' in clube_perf.lower() and 'grêmio' in clube_cbf.lower():
                clube_bate = True
            elif 'flamengo' in clube_perf.lower() and 'flamengo' in clube_cbf.lower():
                clube_bate = True
            elif 'palmeiras' in clube_perf.lower() and 'palmeiras' in clube_cbf.lower():
                clube_bate = True
            elif 'corinthians' in clube_perf.lower() and 'corinthians' in clube_cbf.lower():
                clube_bate = True
            elif 'fluminense' in clube_perf.lower() and 'fluminense' in clube_cbf.lower():
                clube_bate = True
            elif 'internacional' in clube_perf.lower() and 'internacional' in clube_cbf.lower():
                clube_bate = True
            elif 'botafogo' in clube_perf.lower() and 'botafogo' in clube_cbf.lower():
                clube_bate = True
            elif 'santos' in clube_perf.lower() and 'santos' in clube_cbf.lower():
                clube_bate = True
            elif 'fortaleza' in clube_perf.lower() and 'fortaleza' in clube_cbf.lower():
                clube_bate = True
            elif 'bahia' in clube_perf.lower() and 'bahia' in clube_cbf.lower():
                clube_bate = True
            elif 'cruzeiro' in clube_perf.lower() and 'cruzeiro' in clube_cbf.lower():
                clube_bate = True
            elif 'bragantino' in clube_perf.lower() and 'bragantino' in clube_cbf.lower():
                clube_bate = True
            elif 'sport' in clube_perf.lower() and 'sport' in clube_cbf.lower():
                clube_bate = True
            elif 'vasco' in clube_perf.lower() and 'vasco' in clube_cbf.lower():
                clube_bate = True
            elif 'juventude' in clube_perf.lower() and 'juventude' in clube_cbf.lower():
                clube_bate = True
            elif 'mirassol' in clube_perf.lower() and 'mirassol' in clube_cbf.lower():
                clube_bate = True
            elif 'ceará' in clube_perf.lower() and 'ceará' in clube_cbf.lower():
                clube_bate = True
            elif 'vitória' in clube_perf.lower() and 'vitória' in clube_cbf.lower():
                clube_bate = True
            
            if not clube_bate:
                continue
            
            # Calcular similaridade do nome
            similaridade = similaridade_nomes(nome_perf, nome_cbf)
            
            if similaridade > melhor_score and similaridade > 0.6:
                melhor_score = similaridade
                melhor_match = nome_cbf
        
        # Adicionar nome completo
        if melhor_match:
            perf_row['Nome_Completo'] = melhor_match
        else:
            perf_row['Nome_Completo'] = nome_perf  # Usar nome original se não encontrar
    
    # Salvar arquivo atualizado
    arquivo_saida = r"C:\Users\IGOR\Desktop\UFSC\TCC\dados\minutes_played\fbref_playing_time_com_nome_completo.csv"
    
    with open(arquivo_saida, 'w', newline='', encoding='utf-8') as f:
        fieldnames = list(dados_perf[0].keys())
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(dados_perf)
    
    print(f"Arquivo com nome completo salvo: {arquivo_saida}")
    return dados_perf

def matching_por_nome_completo():
    """
    Faz o matching final pelos nomes completos
    """
    print("\nMATCHING POR NOME COMPLETO")
    print("="*40)
    
    # Carregar dados de transferências com nome completo
    arquivo_transf = r"C:\Users\IGOR\Desktop\UFSC\TCC\dados\clubes\outcome\todos_clubes_2024_com_nome_completo.csv"
    dados_transf = []
    
    with open(arquivo_transf, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            dados_transf.append(row)
    
    print(f"Dados de transferências: {len(dados_transf)} registros")
    
    # Carregar dados de performance com nome completo
    arquivo_perf = r"C:\Users\IGOR\Desktop\UFSC\TCC\dados\minutes_played\fbref_playing_time_com_nome_completo.csv"
    dados_perf = []
    
    with open(arquivo_perf, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            dados_perf.append(row)
    
    print(f"Dados de performance: {len(dados_perf)} registros")
    
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
    
    print("Fazendo matching por nome completo...")
    
    for i, transf_row in enumerate(dados_transf):
        if i % 50 == 0:
            print(f"Processando... {i}/{len(dados_transf)} (Matches: {matches_encontrados})")
        
        # Copiar dados de transferências
        row_corrigida = transf_row.copy()
        
        # Adicionar colunas de performance vazias
        for col in colunas_performance:
            row_corrigida[col] = ''
        
        # Obter nome completo
        nome_completo_transf = transf_row.get('Nome_Completo', '').strip()
        
        # Buscar match por nome completo
        melhor_match = None
        
        for perf_row in dados_perf:
            nome_completo_perf = perf_row.get('Nome_Completo', '').strip()
            
            # Match exato
            if nome_completo_transf.lower() == nome_completo_perf.lower():
                melhor_match = perf_row
                break
            # Match ignorando acentos
            elif remover_acentos(nome_completo_transf) == remover_acentos(nome_completo_perf):
                melhor_match = perf_row
                break
            # Similaridade alta
            elif similaridade_nomes(nome_completo_transf, nome_completo_perf) > 0.9:
                melhor_match = perf_row
                break
        
        # Se encontrou match, copiar dados
        if melhor_match:
            for col in colunas_performance:
                if col in melhor_match:
                    row_corrigida[col] = melhor_match[col]
            
            matches_encontrados += 1
            
            # Debug para casos específicos
            if 'everson' in nome_completo_transf.lower():
                print(f"EVERSON MATCH:")
                print(f"  Transfer: {nome_completo_transf}")
                print(f"  Performance: {melhor_match.get('Nome_Completo', '')}")
                print()
        
        dados_corrigidos.append(row_corrigida)
    
    print(f"\nMatches encontrados: {matches_encontrados}")
    print(f"Taxa de match: {(matches_encontrados/len(dados_transf)*100):.1f}%")
    
    # Salvar arquivo final
    arquivo_saida = r"C:\Users\IGOR\Desktop\UFSC\TCC\dados\clubes\outcome\atletas_completo_final_2024.csv"
    
    with open(arquivo_saida, 'w', newline='', encoding='utf-8') as f:
        fieldnames = list(dados_corrigidos[0].keys())
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(dados_corrigidos)
    
    print(f"Arquivo final salvo: {arquivo_saida}")
    
    return dados_corrigidos

def main():
    """
    Função principal que executa todo o processo
    """
    print("PROCESSO COMPLETO DE MATCHING")
    print("="*50)
    
    # Etapa 1: Extrair dados da CBF
    atletas_cbf = extrair_dados_cbf()
    
    # Etapa 2: Adicionar nome completo nas transferências
    dados_transf = adicionar_nome_completo_transferencias()
    
    # Etapa 3: Adicionar nome completo na performance
    dados_perf = adicionar_nome_completo_performance()
    
    # Etapa 4: Matching final por nome completo
    dados_finais = matching_por_nome_completo()
    
    print("\nPROCESSO CONCLUÍDO!")
    print("="*50)

if __name__ == "__main__":
    main()

