"""
Comparação de estatísticas descritivas entre grupos (ex: amostra completa vs meio campistas)
Produz tabelas com n, média, mediana, desvio padrão, min, max, p10, p90
e também diferenças em nível e percentual entre grupos.
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import List


# ============================================================================
# CONFIGURAÇÕES
# ============================================================================

# Caminhos dos arquivos
PATHS = {
    'todos': Path("../dados/df_final.csv"),      # amostra completa
    'mc': Path("../dados/df_mc.csv"),            # meio campistas
    'output_dir': Path("artifacts_comparativo")
}

# Colunas para análise
COLUNAS_ANALISE = ["age", "Height", "Value_Num", "fb_Mn/MP", "fb_xG+/-", "ln_Value_Num"]


# ============================================================================
# FUNÇÕES AUXILIARES
# ============================================================================

def validar_colunas(df: pd.DataFrame, colunas_desejadas: List[str]) -> List[str]:
    """
    Valida quais colunas existem no DataFrame e retorna apenas as existentes.
    
    Args:
        df: DataFrame a ser validado
        colunas_desejadas: Lista de colunas desejadas
        
    Returns:
        Lista de colunas que existem no DataFrame
    """
    colunas_existentes = [col for col in colunas_desejadas if col in df.columns]
    colunas_faltantes = [col for col in colunas_desejadas if col not in df.columns]
    
    if colunas_faltantes:
        print(f"[AVISO] Colunas não encontradas: {colunas_faltantes}")
    
    return colunas_existentes


def calcular_estatisticas(df: pd.DataFrame, colunas: List[str]) -> pd.DataFrame:
    """
    Calcula estatísticas descritivas para as colunas especificadas.
    
    Args:
        df: DataFrame com os dados
        colunas: Lista de colunas para análise
        
    Returns:
        DataFrame com estatísticas por variável
    """
    # Validar colunas
    colunas_validas = validar_colunas(df, colunas)
    
    if not colunas_validas:
        raise ValueError("Nenhuma coluna válida encontrada para análise!")
    
    # Filtrar apenas colunas válidas
    df_filtrado = df[colunas_validas].copy()
    
    # Calcular estatísticas
    stats_dict = {
        "Variável": colunas_validas,
        "n": [df_filtrado[col].notna().sum() for col in colunas_validas],
        "Média": [df_filtrado[col].mean() for col in colunas_validas],
        "Mediana": [df_filtrado[col].median() for col in colunas_validas],
        "Desvio_Padrão": [df_filtrado[col].std(ddof=1) for col in colunas_validas],
        "Mínimo": [df_filtrado[col].min() for col in colunas_validas],
        "Máximo": [df_filtrado[col].max() for col in colunas_validas],
        "P10": [df_filtrado[col].quantile(0.10) for col in colunas_validas],
        "P90": [df_filtrado[col].quantile(0.90) for col in colunas_validas],
        "Assimetria": [df_filtrado[col].skew() for col in colunas_validas],
        "Curtose": [df_filtrado[col].kurtosis() for col in colunas_validas],
    }
    
    stats_df = pd.DataFrame(stats_dict)
    
    # Arredondar valores numéricos
    for col in stats_df.columns:
        if col != "Variável" and pd.api.types.is_numeric_dtype(stats_df[col]):
            stats_df[col] = stats_df[col].round(3)
    
    return stats_df


def criar_tabela_comparativa(
    stats_mc: pd.DataFrame, 
    stats_ata: pd.DataFrame,
    nome_grupo1: str = "MC",
    nome_grupo2: str = "ATA"
) -> pd.DataFrame:
    """
    Cria tabela comparativa entre dois grupos.
    
    Args:
        stats_mc: Estatísticas do grupo 1
        stats_ata: Estatísticas do grupo 2
        nome_grupo1: Nome do primeiro grupo
        nome_grupo2: Nome do segundo grupo
        
    Returns:
        DataFrame com comparação entre grupos
    """
    # Garantir que ambos têm as mesmas variáveis
    variaveis_comuns = set(stats_mc["Variável"]).intersection(set(stats_ata["Variável"]))
    variaveis_comuns = sorted(list(variaveis_comuns))
    
    if not variaveis_comuns:
        raise ValueError("Nenhuma variável comum encontrada entre os grupos!")
    
    # Filtrar apenas variáveis comuns
    stats_mc_filtrado = stats_mc[stats_mc["Variável"].isin(variaveis_comuns)].copy()
    stats_ata_filtrado = stats_ata[stats_ata["Variável"].isin(variaveis_comuns)].copy()
    
    # Ordenar por variável
    stats_mc_filtrado = stats_mc_filtrado.sort_values("Variável")
    stats_ata_filtrado = stats_ata_filtrado.sort_values("Variável")
    
    # Criar tabela comparativa
    comparativo = pd.DataFrame({
        "Variável": variaveis_comuns,
        f"{nome_grupo1}_n": stats_mc_filtrado["n"].values,
        f"{nome_grupo2}_n": stats_ata_filtrado["n"].values,
        f"{nome_grupo1}_Média": stats_mc_filtrado["Média"].values,
        f"{nome_grupo2}_Média": stats_ata_filtrado["Média"].values,
        "Delta_Média": stats_ata_filtrado["Média"].values - stats_mc_filtrado["Média"].values,
        "Delta_Média_%": np.where(
            stats_mc_filtrado["Média"].values != 0,
            100 * (stats_ata_filtrado["Média"].values - stats_mc_filtrado["Média"].values) / stats_mc_filtrado["Média"].values,
            np.nan
        ),
        f"{nome_grupo1}_Mediana": stats_mc_filtrado["Mediana"].values,
        f"{nome_grupo2}_Mediana": stats_ata_filtrado["Mediana"].values,
        f"{nome_grupo1}_Desvio": stats_mc_filtrado["Desvio_Padrão"].values,
        f"{nome_grupo2}_Desvio": stats_ata_filtrado["Desvio_Padrão"].values,
        f"{nome_grupo1}_Min": stats_mc_filtrado["Mínimo"].values,
        f"{nome_grupo2}_Min": stats_ata_filtrado["Mínimo"].values,
        f"{nome_grupo1}_Max": stats_mc_filtrado["Máximo"].values,
        f"{nome_grupo2}_Max": stats_ata_filtrado["Máximo"].values,
        f"{nome_grupo1}_Assimetria": stats_mc_filtrado["Assimetria"].values,
        f"{nome_grupo2}_Assimetria": stats_ata_filtrado["Assimetria"].values,
        f"{nome_grupo1}_Curtose": stats_mc_filtrado["Curtose"].values,
        f"{nome_grupo2}_Curtose": stats_ata_filtrado["Curtose"].values,
    })
    
    # Arredondar valores numéricos
    for col in comparativo.columns:
        if col != "Variável" and pd.api.types.is_numeric_dtype(comparativo[col]):
            comparativo[col] = comparativo[col].round(3)
    
    return comparativo


def carregar_dados(caminho: Path, nome_grupo: str) -> pd.DataFrame:
    """
    Carrega dados de um arquivo CSV com tratamento de erros.
    
    Args:
        caminho: Caminho do arquivo
        nome_grupo: Nome do grupo (para mensagens)
        
    Returns:
        DataFrame carregado
        
    Raises:
        FileNotFoundError: Se o arquivo não existir
        pd.errors.EmptyDataError: Se o arquivo estiver vazio
    """
    if not caminho.exists():
        raise FileNotFoundError(f"[ERRO] Arquivo não encontrado: {caminho}")
    
    try:
        df = pd.read_csv(caminho, encoding='utf-8')
        print(f"[OK] {nome_grupo}: {len(df)} registros carregados de {caminho}")
        return df
    except pd.errors.EmptyDataError as exc:
        raise pd.errors.EmptyDataError(f"[ERRO] Arquivo vazio: {caminho}") from exc
    except Exception as exc:
        raise RuntimeError(f"[ERRO] Erro ao carregar {caminho}: {str(exc)}") from exc


# ============================================================================
# FUNÇÃO PRINCIPAL
# ============================================================================

def main():
    """Função principal que executa a análise completa."""
    
    print("=" * 70)
    print("COMPARAÇÃO DE ESTATÍSTICAS DESCRITIVAS")
    print("=" * 70)
    print()
    
    # Criar diretório de saída
    PATHS['output_dir'].mkdir(parents=True, exist_ok=True)
    
    try:
        # Carregar dados
        print("[1/4] Carregando dados...")
        df_todos = carregar_dados(PATHS['todos'], "Amostra Completa (Todos)")
        df_mc = carregar_dados(PATHS['mc'], "Meio Campistas (MC)")
        print()
        
        # Calcular estatísticas
        print("[2/4] Calculando estatisticas...")
        stats_todos = calcular_estatisticas(df_todos, COLUNAS_ANALISE)
        stats_mc = calcular_estatisticas(df_mc, COLUNAS_ANALISE)
        print()
        
        # Criar tabela comparativa
        print("[3/4] Criando tabela comparativa...")
        comparativo = criar_tabela_comparativa(stats_todos, stats_mc, nome_grupo1="Todos", nome_grupo2="MC")
        print()
        
        # Salvar resultados
        print("[4/4] Salvando resultados...")
        
        # Estatísticas individuais
        path_stats_todos = PATHS['output_dir'] / "estatisticas_todos.csv"
        path_stats_mc = PATHS['output_dir'] / "estatisticas_mc.csv"
        path_comparativo = PATHS['output_dir'] / "comparativo_todos_vs_mc.csv"
        
        stats_todos.to_csv(path_stats_todos, index=False, encoding='utf-8')
        stats_mc.to_csv(path_stats_mc, index=False, encoding='utf-8')
        comparativo.to_csv(path_comparativo, index=False, encoding='utf-8')
        
        print(f"  [OK] {path_stats_todos}")
        print(f"  [OK] {path_stats_mc}")
        print(f"  [OK] {path_comparativo}")
        print()
        
        # Exibir resumo
        print("=" * 70)
        print("RESUMO DA ANALISE")
        print("=" * 70)
        print(f"\nVariáveis analisadas: {len(stats_todos)}")
        print(f"Amostra Completa: {len(df_todos)} registros")
        print(f"Meio Campistas: {len(df_mc)} registros")
        print()
        
        print("Tabela Comparativa:")
        print(comparativo.to_string(index=False))
        print()
        
        print("[SUCESSO] Analise concluida!")
        print(f"Arquivos salvos em: {PATHS['output_dir']}")
        
    except FileNotFoundError as e:
        print(f"\n{e}")
        print("\n[DICA] Verifique se os arquivos existem nos caminhos especificados.")
    except Exception as e:
        print(f"\n[ERRO] Erro durante a execucao: {str(e)}")
        raise


if __name__ == "__main__":
    main()
