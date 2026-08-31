import pandas as pd
import os

def separar_dados_por_posicao():
    """
    Separa o arquivo df_final_with_clusters.csv em 4 arquivos diferentes
    baseado nas variáveis dummy de posição
    """
    
    # Caminho do arquivo original
    arquivo_original = "dados/cluster/df_final_with_clusters.csv"
    
    # Verificar se o arquivo existe
    if not os.path.exists(arquivo_original):
        print(f"Erro: Arquivo {arquivo_original} não encontrado!")
        return
    
    # Ler o arquivo CSV
    print("Carregando dados...")
    df = pd.read_csv(arquivo_original)
    
    print(f"Total de registros: {len(df)}")
    print(f"Colunas disponíveis: {list(df.columns)}")
    
    # Verificar se as colunas dummy existem
    colunas_dummy = ['Dum_GK', 'Dum_DEF', 'Dum_MC', 'Dum_ATA']
    for col in colunas_dummy:
        if col not in df.columns:
            print(f"Erro: Coluna {col} não encontrada!")
            return
    
    # Separar dados por posição
    posicoes = {
        'final_gk.csv': 'Dum_GK',
        'final_def.csv': 'Dum_DEF', 
        'final_mc.csv': 'Dum_MC',
        'final_ata.csv': 'Dum_ATA'
    }
    
    for nome_arquivo, coluna_dummy in posicoes.items():
        # Filtrar dados onde a dummy = 1
        df_posicao = df[df[coluna_dummy] == 1].copy()
        
        # Remover as colunas dummy (exceto a que foi usada para filtrar)
        colunas_para_remover = [col for col in colunas_dummy if col != coluna_dummy]
        df_posicao = df_posicao.drop(columns=colunas_para_remover)
        
        # Salvar arquivo
        df_posicao.to_csv(nome_arquivo, index=False)
        
        print(f"Arquivo {nome_arquivo} criado com {len(df_posicao)} registros")
        
        # Mostrar algumas estatísticas básicas
        print(f"  - Posição: {coluna_dummy}")
        print(f"  - Registros: {len(df_posicao)}")
        if len(df_posicao) > 0:
            print(f"  - Clubes únicos: {df_posicao['Clube'].nunique()}")
            print(f"  - Jogadores únicos: {df_posicao['Player'].nunique()}")
        print()

if __name__ == "__main__":
    separar_dados_por_posicao()



