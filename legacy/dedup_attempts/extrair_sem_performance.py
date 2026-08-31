import pandas as pd

def extrair_jogadores_sem_performance():
    """
    Extrai todos os jogadores sem dados de performance para um novo CSV
    """
    
    # Caminho do arquivo completo
    arquivo_entrada = r"C:\Users\IGOR\Desktop\UFSC\TCC\dados\clubes\outcome\atletas_completo_2024.csv"
    arquivo_saida = r"C:\Users\IGOR\Desktop\UFSC\TCC\dados\clubes\outcome\wout_data.csv"
    
    print("Carregando arquivo completo...")
    df = pd.read_csv(arquivo_entrada)
    
    print(f"Arquivo carregado com {len(df)} linhas e {len(df.columns)} colunas")
    
    # Filtrar jogadores sem dados de performance (Rk é NaN)
    jogadores_sem_performance = df[df['Rk'].isna()].copy()
    
    print(f"\nJogadores sem dados de performance: {len(jogadores_sem_performance)}")
    
    # Remover colunas de performance que estão vazias
    colunas_performance = [
        'Rk', 'Nation_performance', 'Pos', 'Squad', 'Age', 'Born', 
        'MP', 'Min', 'Mn/MP', 'Min%', '90s', 'Starts', 'Mn/Start', 
        'Compl', 'Subs', 'Mn/Sub', 'unSub', 'PPM', 'onG', 'onGA', 
        '+/-', '+/-90', 'On-Off', 'onxG', 'onxGA', 'xG+/-', 
        'xG+/-90', 'On-Off.1', 'Matches'
    ]
    
    # Remover colunas de performance vazias
    df_limpo = jogadores_sem_performance.drop(columns=colunas_performance, errors='ignore')
    
    # Reorganizar colunas para melhor visualização
    colunas_principais = [
        'Clube', 'Player', 'nasc', 'age', 'Position', 'Position_Num', 
        'Height', 'Nation_transfer', 'Ex_Club_Limpo', 'Transferencia', 
        'Taxa_Transferencia', 'Value_Num'
    ]
    
    # Manter apenas as colunas que existem no DataFrame
    colunas_finais = [col for col in colunas_principais if col in df_limpo.columns]
    
    # Adicionar outras colunas importantes se existirem
    outras_colunas = [col for col in df_limpo.columns if col not in colunas_finais]
    colunas_finais.extend(outras_colunas)
    
    df_final = df_limpo[colunas_finais]
    
    # Salvar arquivo
    print(f"\nSalvando arquivo: {arquivo_saida}")
    df_final.to_csv(arquivo_saida, index=False, encoding='utf-8')
    
    print(f"\nArquivo salvo com {len(df_final)} jogadores e {len(df_final.columns)} colunas")
    
    # Mostrar estatísticas por clube
    print(f"\nDistribuição por clube:")
    print(df_final['Clube'].value_counts().sort_index())
    
    # Mostrar estatísticas por posição
    print(f"\nDistribuição por posição:")
    print(df_final['Position'].value_counts())
    
    # Mostrar algumas linhas de exemplo
    print(f"\nPrimeiras 10 linhas do arquivo:")
    print(df_final[['Player', 'Clube', 'Position', 'Value_Num']].head(10))
    
    return df_final

if __name__ == "__main__":
    df_resultado = extrair_jogadores_sem_performance()

