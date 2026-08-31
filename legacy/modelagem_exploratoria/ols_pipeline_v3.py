#!/usr/bin/env python3
r"""
OLS pipeline (v3) - Modelos por Cluster.

Entrada:
  C:\Users\IGOR\Desktop\UFSC\TCC\dados\clubes\outcome\final_merged_filtrado_dummies_clean_with_cluster_v2.csv

Regras:
- Roda OLS separadamente para cada cluster
- Variáveis: fb_Mn/MP + fb_PPM + fb_+/- + fb_xG+/- + dummies posição
- Dependente: Value_Num (nível)
- Erros-padrão robustos (HC1)

Saídas em ./artifactsv3/
"""

import os
from pathlib import Path
import warnings
import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy import stats
from statsmodels.stats.outliers_influence import variance_inflation_factor

warnings.filterwarnings("ignore")

INPUT_PATH = r"C:\Users\IGOR\Desktop\UFSC\TCC\dados\clubes\outcome\final_merged_filtrado_dummies_clean_with_cluster_v2.csv"
OUT_DIR = Path("artifactsv3")
OUT_DIR.mkdir(exist_ok=True)


def load_data():
    """Carrega e prepara dados"""
    print("Carregando base...")
    df = pd.read_csv(INPUT_PATH)
    
    # Verifica se cluster existe
    if 'cluster' not in df.columns:
        raise ValueError("Coluna 'cluster' não encontrada no dataset")
    
    print(f"Dataset carregado: {df.shape[0]} observações, {df.shape[1]} variáveis")
    print(f"Clusters encontrados: {sorted(df['cluster'].unique())}")
    
    return df


def select_variables(df):
    """Seleciona variáveis para análise"""
    # Variáveis fixas
    usage_var = 'fb_Mn/MP'
    perf_vars = ['fb_PPM', 'fb_+/-', 'fb_xG+/-']
    pos_dummies = ['Dum_GK', 'Dum_DEF', 'Dum_ATA']  # Dum_MC é referência
    continuous_vars = ['age', 'Height']
    
    # Verifica se todas existem
    all_vars = [usage_var] + perf_vars + pos_dummies + continuous_vars + ['Value_Num', 'cluster']
    missing_vars = [v for v in all_vars if v not in df.columns]
    if missing_vars:
        raise ValueError(f"Variáveis ausentes: {missing_vars}")

    # Converte age e Height para numérico se necessário
    for var in continuous_vars:
        if df[var].dtype == 'object':
            df[var] = pd.to_numeric(df[var], errors='coerce')
            print(f"Convertido {var} para numérico")

    X_vars = [usage_var] + perf_vars + pos_dummies + continuous_vars
    print(f"Variáveis selecionadas\n- Uso: {usage_var}\n- Desempenho: {perf_vars}\n- Dummies posição: {pos_dummies}\n- Contínuas: {continuous_vars}")

    return X_vars


def fit_ols_cluster(X, y):
    """Ajusta OLS com erros robustos para um cluster"""
    try:
        X = sm.add_constant(X)
        model = sm.OLS(y, X).fit()
        robust = model.get_robustcov_results(cov_type='HC1')
        return model, robust
    except Exception as e:
        print(f"Erro na estimação: {e}")
        return None, None


def compute_vif_cluster(X, X_vars):
    """Calcula VIF para um cluster"""
    try:
        X_with_const = sm.add_constant(X)
        vif_data = []
        
        for i, var in enumerate(['const'] + X_vars):
            if var == 'const':
                continue
            vif = variance_inflation_factor(X_with_const.values, i)
            vif_data.append({'variable': var, 'vif': float(vif)})
        
        return pd.DataFrame(vif_data)
    except Exception as e:
        print(f"Erro no cálculo VIF: {e}")
        return pd.DataFrame()


def run_ols_per_cluster(df, X_vars):
    """Roda OLS para cada cluster"""
    results = {}
    cluster_stats = {}
    vif_results = {}
    
    unique_clusters = sorted(df['cluster'].unique())
    print(f"\nRodando OLS para {len(unique_clusters)} clusters...")
    
    for cluster_id in unique_clusters:
        print(f"\n--- Cluster {cluster_id} ---")
        
        # Filtra dados do cluster
        mask = df['cluster'] == cluster_id
        df_cluster = df[mask]
        
        if len(df_cluster) < 30:  # Critério de N mínimo
            print("⚠️ Poucas observações (< 30), pulando cluster")
            continue
        
        # Prepara X e y
        X = df_cluster[X_vars].astype(float)
        y = df_cluster['Value_Num'].astype(float)
        
        # Remove missing values
        mask_clean = X.notna().all(axis=1) & y.notna()
        X_clean = X[mask_clean]
        y_clean = y[mask_clean]
        
        print(f"Observações: {len(y_clean)}")
        
        if len(y_clean) < 30:
            print("⚠️ Poucas observações após limpeza (< 30), pulando cluster")
            continue
        
        # Estatísticas descritivas
        cluster_stats[cluster_id] = {
            'n_obs': len(y_clean),
            'mean_value': y_clean.mean(),
            'std_value': y_clean.std(),
            'min_value': y_clean.min(),
            'max_value': y_clean.max()
        }
        
        # Calcula VIF
        vif_df = compute_vif_cluster(X_clean, X_vars)
        vif_results[cluster_id] = vif_df
        
        # Estima OLS
        model, robust = fit_ols_cluster(X_clean, y_clean)
        
        if model is not None:
            results[cluster_id] = {
                'model': model,
                'robust': robust,
                'X_vars': X_vars
            }
            print(f"R² = {model.rsquared:.3f}")
            print(f"n = {model.nobs}")
        else:
            print("❌ Falha na estimação")
    
    return results, cluster_stats, vif_results


def save_results(results, cluster_stats, vif_results, X_vars):
    """Salva resultados"""
    print(f"\nSalvando resultados em {OUT_DIR}...")
    
    # 1. Resumo por cluster
    summary_data = []
    for cluster_id, stats in cluster_stats.items():
        r_squared = results.get(cluster_id, {}).get('model', {}).rsquared if cluster_id in results else np.nan
        summary_data.append({
            'cluster': cluster_id,
            'n_obs': stats['n_obs'],
            'mean_value': stats['mean_value'],
            'std_value': stats['std_value'],
            'min_value': stats['min_value'],
            'max_value': stats['max_value'],
            'r_squared': r_squared
        })
    
    summary_df = pd.DataFrame(summary_data)
    summary_df.to_csv(f"{OUT_DIR}/cluster_summary.csv", index=False)
    
    # 2. Coeficientes por cluster
    coef_data = []
    for cluster_id, result in results.items():
        model = result['model']
        robust = result['robust']
        
        for i, var in enumerate(['const'] + X_vars):
            # Corrige acesso aos arrays/Series
            if hasattr(model.params, 'iloc'):
                coef = model.params.iloc[i]
            else:
                coef = model.params[i]
                
            if hasattr(robust.bse, 'iloc'):
                se = robust.bse.iloc[i]
            else:
                se = robust.bse[i]
                
            if hasattr(robust.tvalues, 'iloc'):
                t_stat = robust.tvalues.iloc[i]
            else:
                t_stat = robust.tvalues[i]
                
            if hasattr(robust.pvalues, 'iloc'):
                p_val = robust.pvalues.iloc[i]
            else:
                p_val = robust.pvalues[i]
            
            coef_data.append({
                'cluster': cluster_id,
                'variable': var,
                'coefficient': coef,
                'se_robust': se,
                't_stat': t_stat,
                'p_value': p_val
            })
    
    coef_df = pd.DataFrame(coef_data)
    coef_df.to_csv(f"{OUT_DIR}/coefficients_by_cluster.csv", index=False)
    
    # 3. VIF por cluster
    for cluster_id, vif_df in vif_results.items():
        if not vif_df.empty:
            vif_df.to_csv(f"{OUT_DIR}/vif_cluster{cluster_id}.csv", index=False)
    
    # 4. Relatório texto
    with open(f"{OUT_DIR}/relatorio_ols_por_cluster.txt", 'w', encoding='utf-8') as f:
        f.write("OLS POR CLUSTER - RELATÓRIO ATUALIZADO\n")
        f.write("=" * 50 + "\n\n")
        f.write("Variáveis incluídas: fb_Mn/MP, fb_PPM, fb_+/-, fb_xG+/-, age, Height, Dum_GK, Dum_DEF, Dum_ATA\n")
        f.write("Critério N mínimo: 30 observações por cluster\n\n")
        
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
            model = result['model']
            robust = result['robust']
            
            f.write(f"Observações: {int(model.nobs)}\n")
            f.write(f"R²: {model.rsquared:.4f}\n\n")
            
            f.write("Variável\t\tCoef\t\tSE\t\tt-stat\t\tp-value\n")
            f.write("-" * 60 + "\n")
            
            for i, var in enumerate(['const'] + X_vars):
                # Corrige acesso aos arrays/Series
                if hasattr(model.params, 'iloc'):
                    coef = model.params.iloc[i]
                else:
                    coef = model.params[i]
                    
                if hasattr(robust.bse, 'iloc'):
                    se = robust.bse.iloc[i]
                else:
                    se = robust.bse[i]
                    
                if hasattr(robust.tvalues, 'iloc'):
                    t_stat = robust.tvalues.iloc[i]
                else:
                    t_stat = robust.tvalues[i]
                    
                if hasattr(robust.pvalues, 'iloc'):
                    p_val = robust.pvalues.iloc[i]
                else:
                    p_val = robust.pvalues[i]
                
                f.write(f"{var:<15}\t{coef:>8.4f}\t{se:>8.4f}\t{t_stat:>8.2f}\t{p_val:>8.4f}\n")
        
        f.write(f"\n\nVIF calculado e salvo em vif_cluster{{c}}.csv para cada cluster\n")
    
    print("✅ Resultados salvos:")
    print(f"  - {OUT_DIR}/cluster_summary.csv")
    print(f"  - {OUT_DIR}/coefficients_by_cluster.csv") 
    print(f"  - {OUT_DIR}/relatorio_ols_por_cluster.txt")
    print(f"  - {OUT_DIR}/vif_cluster{{c}}.csv (para cada cluster)")


def main():
    """Função principal"""
    print("OLS POR CLUSTER - v3")
    print("=" * 30)
    
    try:
        # Carrega dados
        df = load_data()
        
        # Seleciona variáveis
        X_vars = select_variables(df)
        
        # Roda OLS por cluster
        results, cluster_stats, vif_results = run_ols_per_cluster(df, X_vars)
        
        if not results:
            print("❌ Nenhum cluster pôde ser estimado")
            return
        
        # Salva resultados
        save_results(results, cluster_stats, vif_results, X_vars)
        
        print(f"\n✅ Análise concluída! {len(results)} clusters estimados.")
        
    except Exception as e:
        print(f"❌ Erro: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()