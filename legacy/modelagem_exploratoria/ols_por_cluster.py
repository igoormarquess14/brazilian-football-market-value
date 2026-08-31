"""
OLS por Cluster - Análise Econométrica Separada por Cluster

Este script roda modelos OLS separadamente para cada cluster identificado,
usando as mesmas variáveis do baseline mas estimando coeficientes específicos
para cada grupo de jogadores.

Input: final_merged_filtrado_dummies_clean_with_cluster_v2.csv
Output: ./artifactsv3/clusters/
"""

import pandas as pd
import numpy as np
import os
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

# Configuração
INPUT_FILE = r"C:\Users\IGOR\Desktop\UFSC\TCC\dados\clubes\outcome\final_merged_filtrado_dummies_clean_with_cluster_v2.csv"
OUTPUT_DIR = "./artifactsv3/clusters"

def create_output_dir():
    """Cria diretório de saída"""
    Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)
    print(f"Diretório de saída: {OUTPUT_DIR}")

def load_data():
    """Carrega e prepara dados"""
    print("Carregando dados...")
    df = pd.read_csv(INPUT_FILE)
    
    # Verifica se cluster existe
    if 'cluster' not in df.columns:
        raise ValueError("Coluna 'cluster' não encontrada no dataset")
    
    print(f"Dataset carregado: {df.shape[0]} observações, {df.shape[1]} variáveis")
    print(f"Clusters encontrados: {sorted(df['cluster'].unique())}")
    
    return df

def prepare_variables(df):
    """Prepara variáveis para análise"""
    # Variáveis de interesse (mesmo conjunto do baseline)
    vars_uso = ['fb_Mn/MP']
    vars_desempenho = ['fb_PPM', 'fb_+/-', 'fb_xG+/-']
    vars_dummies = ['Dum_GK', 'Dum_DEF', 'Dum_ATA']  # Dum_MC é referência
    
    # Verifica se todas as variáveis existem
    all_vars = vars_uso + vars_desempenho + vars_dummies + ['Value_Num', 'cluster']
    missing_vars = [v for v in all_vars if v not in df.columns]
    if missing_vars:
        print(f"⚠️ Variáveis ausentes: {missing_vars}")
        return None, None
    
    # Remove missing values
    df_clean = df[all_vars].dropna()
    print(f"Após remover missing: {df_clean.shape[0]} observações")
    
    # Define X e y
    X_vars = vars_uso + vars_desempenho + vars_dummies
    X = df_clean[X_vars]
    y = df_clean['Value_Num']
    clusters = df_clean['cluster']
    
    return X, y, clusters, X_vars

def ols_manual(X, y, add_constant=True):
    """OLS manual com erros robustos"""
    if add_constant:
        X = np.column_stack([np.ones(len(X)), X])
    
    try:
        # Estimação OLS
        beta = np.linalg.inv(X.T @ X) @ X.T @ y
        y_pred = X @ beta
        residuals = y - y_pred
        
        # Erros-padrão robustos (HC1)
        n, k = X.shape
        df_resid = n - k
        
        # Matriz de covariância robusta
        XtX_inv = np.linalg.inv(X.T @ X)
        meat = X.T @ np.diag(residuals**2) @ X
        vcov_robust = XtX_inv @ meat @ XtX_inv
        
        se_robust = np.sqrt(np.diag(vcov_robust))
        
        # Estatísticas t
        t_stats = beta / se_robust
        
        # R²
        ss_res = np.sum(residuals**2)
        ss_tot = np.sum((y - np.mean(y))**2)
        r_squared = 1 - (ss_res / ss_tot)
        
        return {
            'beta': beta,
            'se_robust': se_robust,
            't_stats': t_stats,
            'r_squared': r_squared,
            'n_obs': n,
            'df_resid': df_resid,
            'residuals': residuals,
            'y_pred': y_pred
        }
    except Exception as e:
        print(f"Erro na estimação OLS: {e}")
        return None

def run_ols_per_cluster(X, y, clusters, X_vars):
    """Roda OLS para cada cluster"""
    results = {}
    cluster_stats = {}
    
    unique_clusters = sorted(clusters.unique())
    print(f"\nRodando OLS para {len(unique_clusters)} clusters...")
    
    for cluster_id in unique_clusters:
        print(f"\n--- Cluster {cluster_id} ---")
        
        # Filtra dados do cluster
        mask = clusters == cluster_id
        X_cluster = X[mask]
        y_cluster = y[mask]
        
        print(f"Observações: {len(y_cluster)}")
        
        if len(y_cluster) < 10:  # Mínimo para estimação
            print("⚠️ Poucas observações, pulando cluster")
            continue
        
        # Estatísticas descritivas
        cluster_stats[cluster_id] = {
            'n_obs': len(y_cluster),
            'mean_value': y_cluster.mean(),
            'std_value': y_cluster.std(),
            'min_value': y_cluster.min(),
            'max_value': y_cluster.max()
        }
        
        # Estima OLS
        ols_result = ols_manual(X_cluster, y_cluster)
        
        if ols_result is not None:
            results[cluster_id] = ols_result
            print(f"R² = {ols_result['r_squared']:.3f}")
            print(f"n = {ols_result['n_obs']}")
        else:
            print("❌ Falha na estimação")
    
    return results, cluster_stats

def save_results(results, cluster_stats, X_vars):
    """Salva resultados"""
    print(f"\nSalvando resultados em {OUTPUT_DIR}...")
    
    # 1. Resumo por cluster
    summary_data = []
    for cluster_id, stats in cluster_stats.items():
        summary_data.append({
            'cluster': cluster_id,
            'n_obs': stats['n_obs'],
            'mean_value': stats['mean_value'],
            'std_value': stats['std_value'],
            'min_value': stats['min_value'],
            'max_value': stats['max_value'],
            'r_squared': results.get(cluster_id, {}).get('r_squared', np.nan)
        })
    
    summary_df = pd.DataFrame(summary_data)
    summary_df.to_csv(f"{OUTPUT_DIR}/cluster_summary.csv", index=False)
    
    # 2. Coeficientes por cluster
    coef_data = []
    for cluster_id, result in results.items():
        for i, var in enumerate(['const'] + X_vars):
            coef_data.append({
                'cluster': cluster_id,
                'variable': var,
                'coefficient': result['beta'][i],
                'se_robust': result['se_robust'][i],
                't_stat': result['t_stats'][i],
                'p_value': 2 * (1 - stats.t.cdf(abs(result['t_stats'][i]), result['df_resid']))
            })
    
    coef_df = pd.DataFrame(coef_data)
    coef_df.to_csv(f"{OUTPUT_DIR}/coefficients_by_cluster.csv", index=False)
    
    # 3. Relatório texto
    with open(f"{OUTPUT_DIR}/relatorio_ols_por_cluster.txt", 'w', encoding='utf-8') as f:
        f.write("OLS POR CLUSTER - RELATÓRIO\n")
        f.write("=" * 50 + "\n\n")
        
        f.write("RESUMO POR CLUSTER\n")
        f.write("-" * 30 + "\n")
        f.write(summary_df.to_string(index=False))
        f.write("\n\n")
        
        f.write("COEFICIENTES DETALHADOS\n")
        f.write("-" * 30 + "\n")
        for cluster_id in sorted(results.keys()):
            f.write(f"\nCLUSTER {cluster_id}\n")
            f.write("-" * 20 + "\n")
            result = results[cluster_id]
            
            f.write(f"Observações: {result['n_obs']}\n")
            f.write(f"R²: {result['r_squared']:.4f}\n\n")
            
            f.write("Variável\t\tCoef\t\tSE\t\tt-stat\t\tp-value\n")
            f.write("-" * 60 + "\n")
            
            for i, var in enumerate(['const'] + X_vars):
                coef = result['beta'][i]
                se = result['se_robust'][i]
                t_stat = result['t_stats'][i]
                p_val = 2 * (1 - stats.t.cdf(abs(t_stat), result['df_resid']))
                
                f.write(f"{var:<15}\t{coef:>8.4f}\t{se:>8.4f}\t{t_stat:>8.2f}\t{p_val:>8.4f}\n")
    
    print("✅ Resultados salvos:")
    print(f"  - {OUTPUT_DIR}/cluster_summary.csv")
    print(f"  - {OUTPUT_DIR}/coefficients_by_cluster.csv") 
    print(f"  - {OUTPUT_DIR}/relatorio_ols_por_cluster.txt")

def main():
    """Função principal"""
    print("OLS POR CLUSTER - v1")
    print("=" * 30)
    
    try:
        # Setup
        create_output_dir()
        
        # Carrega dados
        df = load_data()
        
        # Prepara variáveis
        X, y, clusters, X_vars = prepare_variables(df)
        if X is None:
            return
        
        print(f"\nVariáveis X: {X_vars}")
        
        # Roda OLS por cluster
        results, cluster_stats = run_ols_per_cluster(X, y, clusters, X_vars)
        
        if not results:
            print("❌ Nenhum cluster pôde ser estimado")
            return
        
        # Salva resultados
        save_results(results, cluster_stats, X_vars)
        
        print(f"\n✅ Análise concluída! {len(results)} clusters estimados.")
        
    except Exception as e:
        print(f"❌ Erro: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # Importa stats para p-values
    from scipy import stats
    main()
