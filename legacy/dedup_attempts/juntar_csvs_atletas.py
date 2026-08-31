import pandas as pd
import numpy as np

def juntar_csvs_atletas():
    """
    Junta dois CSVs com dados dos mesmos atletas:
    1. fbref_playing_time.csv - dados de performance
    2. todos_clubes_2024_final.csv - dados de transferências
    """
    
    # Caminhos dos arquivos
    arquivo_performance = r"C:\Users\IGOR\Desktop\UFSC\TCC\dados\minutes_played\fbref_playing_time.csv"
    arquivo_transferencias = r"C:\Users\IGOR\Desktop\UFSC\TCC\dados\clubes\outcome\todos_clubes_2024_final.csv"
    arquivo_saida = r"C:\Users\IGOR\Desktop\UFSC\TCC\dados\clubes\outcome\atletas_completo_2024.csv"
    
    print("Carregando arquivos CSV...")
    
    # Carregar CSV de performance (usando ; como separador)
    df_performance = pd.read_csv(arquivo_performance, sep=';')
    print(f"Performance: {len(df_performance)} linhas, {len(df_performance.columns)} colunas")
    
    # Carregar CSV de transferências
    df_transferencias = pd.read_csv(arquivo_transferencias)
    print(f"Transferências: {len(df_transferencias)} linhas, {len(df_transferencias.columns)} colunas")
    
    # Mostrar colunas de cada arquivo
    print(f"\nColunas do arquivo de performance:")
    print(df_performance.columns.tolist())
    
    print(f"\nColunas do arquivo de transferências:")
    print(df_transferencias.columns.tolist())
    
    # Limpar e padronizar nomes dos jogadores para melhor matching
    def limpar_nome(nome):
        if pd.isna(nome):
            return ''
        # Converter para string, remover espaços extras e converter para minúsculas
        nome_limpo = str(nome).strip().lower()
        # Remover acentos e caracteres especiais
        nome_limpo = nome_limpo.replace('á', 'a').replace('à', 'a').replace('ã', 'a').replace('â', 'a')
        nome_limpo = nome_limpo.replace('é', 'e').replace('ê', 'e')
        nome_limpo = nome_limpo.replace('í', 'i')
        nome_limpo = nome_limpo.replace('ó', 'o').replace('ô', 'o').replace('õ', 'o')
        nome_limpo = nome_limpo.replace('ú', 'u')
        nome_limpo = nome_limpo.replace('ç', 'c')
        nome_limpo = nome_limpo.replace('ñ', 'n')
        return nome_limpo
    
    # Criar colunas com nomes limpos para matching
    df_performance['Player_clean'] = df_performance['Player'].apply(limpar_nome)
    df_transferencias['Player_clean'] = df_transferencias['Player'].apply(limpar_nome)
    
    print(f"\nFazendo join dos dados...")
    
    # Fazer o merge (left join para manter todos os jogadores de transferências)
    df_final = pd.merge(
        df_transferencias, 
        df_performance, 
        on='Player_clean', 
        how='left',
        suffixes=('_transfer', '_performance')
    )
    
    # Remover colunas auxiliares
    df_final = df_final.drop(['Player_clean', 'Player_performance'], axis=1, errors='ignore')
    
    # Renomear coluna Player para evitar duplicação
    if 'Player_transfer' in df_final.columns:
        df_final = df_final.rename(columns={'Player_transfer': 'Player'})
    
    print(f"\nJoin concluído!")
    print(f"Arquivo final: {len(df_final)} linhas, {len(df_final.columns)} colunas")
    
    # Mostrar estatísticas do merge
    jogadores_com_performance = df_final['Rk'].notna().sum()
    jogadores_sem_performance = df_final['Rk'].isna().sum()
    
    print(f"\nEstatísticas do merge:")
    print(f"- Jogadores com dados de performance: {jogadores_com_performance}")
    print(f"- Jogadores sem dados de performance: {jogadores_sem_performance}")
    print(f"- Taxa de match: {(jogadores_com_performance/len(df_final)*100):.1f}%")
    
    # Salvar arquivo final
    print(f"\nSalvando arquivo final: {arquivo_saida}")
    df_final.to_csv(arquivo_saida, index=False, encoding='utf-8')
    
    # Mostrar algumas linhas de exemplo
    print(f"\nPrimeiras 5 linhas do arquivo final:")
    colunas_principais = ['Player', 'Clube', 'Position', 'Nation', 'Rk', 'MP', 'Min', 'Value_Num']
    colunas_disponiveis = [col for col in colunas_principais if col in df_final.columns]
    print(df_final[colunas_disponiveis].head())
    
    return df_final

if __name__ == "__main__":
    df_resultado = juntar_csvs_atletas()

