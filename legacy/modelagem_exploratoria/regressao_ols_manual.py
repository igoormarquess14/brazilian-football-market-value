"""
Regressão OLS Manual - Valoração de Atletas
Implementação manual de OLS usando apenas numpy

Autor: Assistente IA
Data: 2025
"""

import pandas as pd
import numpy as np
import warnings
warnings.filterwarnings('ignore')

class RegressaoOLSManual:
    def __init__(self, df):
        """Inicializa com dataframe preparado"""
        self.df = df
        self.results = {}
        
    def ols_manual(self, y, X, robust=True):
        """
        Implementa OLS manual com opção de erros robustos
        
        Parâmetros:
        - y: variável dependente (array)
        - X: matriz de variáveis independentes (array)
        - robust: se True, calcula erros robustos (White)
        """
        # Adicionar constante se não existir
        if X.shape[1] > 0 and not np.allclose(X[:, 0], 1):
            X = np.column_stack([np.ones(len(X)), X])
        
        # Calcular coeficientes: beta = (X'X)^-1 X'y
        try:
            XTX_inv = np.linalg.inv(X.T @ X)
            beta = XTX_inv @ X.T @ y
            
            # Resíduos
            y_pred = X @ beta
            residuals = y - y_pred
            
            # R²
            TSS = np.sum((y - np.mean(y))**2)
            RSS = np.sum(residuals**2)
            r_squared = 1 - (RSS / TSS)
            
            # R² ajustado
            n, k = X.shape
            r_squared_adj = 1 - (1 - r_squared) * (n - 1) / (n - k)
            
            # Erros padrão
            if robust:
                # Erros robustos (White)
                residuals_sq = residuals**2
                X_resid = X * residuals.reshape(-1, 1)
                robust_var = XTX_inv @ (X_resid.T @ X_resid) @ XTX_inv
                se = np.sqrt(np.diag(robust_var))
            else:
                # Erros padrão clássicos
                mse = RSS / (n - k)
                var_beta = mse * XTX_inv
                se = np.sqrt(np.diag(var_beta))
            
            # Estatísticas t
            t_stats = beta / se
            
            # P-valores (aproximação normal)
            p_values = 2 * (1 - self._normal_cdf(np.abs(t_stats)))
            
            # F-statistic
            f_stat = (r_squared / (k - 1)) / ((1 - r_squared) / (n - k))
            f_pvalue = 1 - self._f_cdf(f_stat, k - 1, n - k)
            
            return {
                'coefficients': beta,
                'std_errors': se,
                't_stats': t_stats,
                'p_values': p_values,
                'r_squared': r_squared,
                'r_squared_adj': r_squared_adj,
                'f_stat': f_stat,
                'f_pvalue': f_pvalue,
                'residuals': residuals,
                'y_pred': y_pred,
                'n_obs': n,
                'n_vars': k
            }
            
        except np.linalg.LinAlgError:
            print("Erro: Matriz singular - multicolinearidade detectada")
            return None
    
    def _normal_cdf(self, x):
        """Aproximação da CDF normal padrão"""
        return 0.5 * (1 + np.sign(x) * np.sqrt(1 - np.exp(-2 * x**2 / np.pi)))
    
    def _f_cdf(self, x, df1, df2):
        """Aproximação da CDF F"""
        # Aproximação simples para F-distribution
        if x < 0:
            return 0
        if x > 10:
            return 1
        # Aproximação baseada em transformação
        z = np.sqrt(2 * x) - np.sqrt(2 * df1 - 1)
        return self._normal_cdf(z)
    
    def modelo_baseline(self):
        """Modelo baseline OLS"""
        print("\n" + "="*60)
        print("MODELO BASELINE OLS")
        print("="*60)
        
        # Definir variáveis
        X_vars = ['age', 'age_squared', 'Height', 'is_brazilian', 'transfer_fee_clean']
        
        # Adicionar dummies de posição
        pos_cols = [col for col in self.df.columns if col.startswith('pos_')]
        X_vars.extend(pos_cols)
        
        # Adicionar variáveis de desempenho
        performance_vars = ['fb_Min%', 'fb_90s', 'fb_Starts', 'fb_PPM']
        for var in performance_vars:
            if var in self.df.columns:
                X_vars.append(var)
        
        # Filtrar amostra
        sample = self.df[X_vars + ['ln_value']].dropna()
        
        print(f"Amostra: {len(sample)} observações")
        print(f"Variáveis: {len(X_vars)} regressores")
        
        # Preparar dados
        y = sample['ln_value'].values.astype(float)
        X = sample[X_vars].values.astype(float)
        
        # Estimar modelo
        results = self.ols_manual(y, X, robust=True)
        
        if results:
            self.results['baseline'] = results
            self.results['sample_baseline'] = sample
            self.results['X_vars'] = X_vars
            
            # Exibir resultados
            print(f"\nR²: {results['r_squared']:.4f}")
            print(f"R² Ajustado: {results['r_squared_adj']:.4f}")
            print(f"F-statistic: {results['f_stat']:.4f}")
            print(f"Prob(F): {results['f_pvalue']:.4f}")
            
            # Tabela de coeficientes
            print(f"\nCoeficientes:")
            print(f"{'Variável':<20} {'Coef':<10} {'Std.Err':<10} {'t-stat':<10} {'P-valor':<10}")
            print("-" * 70)
            print(f"{'Constante':<20} {results['coefficients'][0]:<10.4f} {results['std_errors'][0]:<10.4f} {results['t_stats'][0]:<10.4f} {results['p_values'][0]:<10.4f}")
            
            for i, var in enumerate(X_vars):
                print(f"{var:<20} {results['coefficients'][i+1]:<10.4f} {results['std_errors'][i+1]:<10.4f} {results['t_stats'][i+1]:<10.4f} {results['p_values'][i+1]:<10.4f}")
        
        return results
    
    def analise_robustez(self):
        """Análises de robustez"""
        print("\n" + "="*60)
        print("ANÁLISES DE ROBUSTEZ")
        print("="*60)
        
        if 'baseline' not in self.results:
            print("Execute primeiro o modelo baseline")
            return
        
        sample = self.results['sample_baseline']
        X_vars = self.results['X_vars']
        
        # Robustez A: Substituir fb_Min% por fb_90s
        print("\nRobustez A: Substituindo fb_Min% por fb_90s")
        X_vars_robA = [col for col in X_vars if col != 'fb_Min%']
        if 'fb_90s' in X_vars_robA:
            sample_robA = sample[X_vars_robA + ['ln_value']].dropna()
            y_robA = sample_robA['ln_value'].values.astype(float)
            X_robA = sample_robA[X_vars_robA].values.astype(float)
            
            results_robA = self.ols_manual(y_robA, X_robA, robust=True)
            if results_robA:
                self.results['robustez_A'] = results_robA
                print(f"R²: {results_robA['r_squared']:.4f} (N={results_robA['n_obs']})")
        
        # Robustez B: Excluir top 1%
        print("\nRobustez B: Excluindo top 1% de valores")
        threshold_99 = np.percentile(sample['ln_value'], 99)
        sample_robB = sample[sample['ln_value'] <= threshold_99]
        
        y_robB = sample_robB['ln_value'].values.astype(float)
        X_robB = sample_robB[X_vars].values.astype(float)
        
        results_robB = self.ols_manual(y_robB, X_robB, robust=True)
        if results_robB:
            self.results['robustez_B'] = results_robB
            print(f"R²: {results_robB['r_squared']:.4f} (N={results_robB['n_obs']})")
        
        # Robustez C: Apenas valores positivos
        print("\nRobustez C: Apenas valores positivos")
        sample_robC = sample[sample['ln_value'] > 0]
        
        y_robC = sample_robC['ln_value'].values.astype(float)
        X_robC = sample_robC[X_vars].values.astype(float)
        
        results_robC = self.ols_manual(y_robC, X_robC, robust=True)
        if results_robC:
            self.results['robustez_C'] = results_robC
            print(f"R²: {results_robC['r_squared']:.4f} (N={results_robC['n_obs']})")
        
        return self.results
    
    def analise_por_posicao(self):
        """Análise separada por posição"""
        print("\n" + "="*60)
        print("ANÁLISE POR POSIÇÃO")
        print("="*60)
        
        if 'baseline' not in self.results:
            print("Execute primeiro o modelo baseline")
            return
        
        # Usar dataframe completo com todas as variáveis necessárias
        X_vars = self.results['X_vars']
        all_vars = X_vars + ['ln_value', 'Position']
        
        # Filtrar amostra completa
        sample_full = self.df[all_vars].dropna()
        
        posicoes = sample_full['Position'].unique()
        resultados_posicao = {}
        
        for pos in posicoes:
            if pd.isna(pos):
                continue
                
            sample_pos = sample_full[sample_full['Position'] == pos]
            
            if len(sample_pos) < 10:
                print(f"\n{pos}: Poucas observações ({len(sample_pos)}), pulando...")
                continue
            
            print(f"\n{pos}: {len(sample_pos)} observações")
            
            y_pos = sample_pos['ln_value'].values.astype(float)
            X_pos = sample_pos[X_vars].values.astype(float)
            
            results_pos = self.ols_manual(y_pos, X_pos, robust=True)
            if results_pos:
                resultados_posicao[pos] = results_pos
                print(f"R²: {results_pos['r_squared']:.4f}")
        
        self.results['por_posicao'] = resultados_posicao
        return resultados_posicao
    
    def gerar_relatorio_final(self):
        """Gera relatório final dos resultados"""
        print("\n" + "="*60)
        print("RELATÓRIO FINAL")
        print("="*60)
        
        if 'baseline' not in self.results:
            print("Nenhum resultado disponível")
            return
        
        baseline = self.results['baseline']
        
        print(f"\nMODELO BASELINE:")
        print(f"• R²: {baseline['r_squared']:.4f}")
        print(f"• R² Ajustado: {baseline['r_squared_adj']:.4f}")
        print(f"• F-statistic: {baseline['f_stat']:.4f} (p={baseline['f_pvalue']:.4f})")
        print(f"• Observações: {baseline['n_obs']}")
        
        print(f"\nCOEFICIENTES SIGNIFICATIVOS (p<0.05):")
        X_vars = ['Constante'] + self.results['X_vars']
        for i, var in enumerate(X_vars):
            if baseline['p_values'][i] < 0.05:
                print(f"• {var}: {baseline['coefficients'][i]:.4f} (t={baseline['t_stats'][i]:.4f})")
        
        print(f"\nROBUSTEZ:")
        if 'robustez_A' in self.results:
            print(f"• Modelo A (fb_90s): R² = {self.results['robustez_A']['r_squared']:.4f}")
        if 'robustez_B' in self.results:
            print(f"• Modelo B (sem top 1%): R² = {self.results['robustez_B']['r_squared']:.4f}")
        if 'robustez_C' in self.results:
            print(f"• Modelo C (valores positivos): R² = {self.results['robustez_C']['r_squared']:.4f}")
        
        return {
            'baseline': baseline,
            'robustez': {k: v for k, v in self.results.items() if k.startswith('robustez')},
            'por_posicao': self.results.get('por_posicao', {})
        }

def main():
    """Função principal"""
    # Carregar dados preparados
    file_path = r'C:\Users\IGOR\Desktop\UFSC\TCC\dados\clubes\outcome\final_merged_fixed.csv'
    df = pd.read_csv(file_path)
    
    # Preparar variáveis (replicar preparação da análise anterior)
    df['ln_value'] = np.log(df['Value_Num'] + 1)
    df['has_value'] = (df['Value_Num'] > 0).astype(int)
    df['age_squared'] = df['age'] ** 2
    df['is_brazilian'] = df['Nation'].str.contains('Brasil', na=False).astype(int)
    df['transfer_fee_clean'] = pd.to_numeric(df['Taxa_Transferencia'], errors='coerce').fillna(0)
    
    # Dummies de posição
    position_dummies = pd.get_dummies(df['Position'], prefix='pos', drop_first=True)
    df = pd.concat([df, position_dummies], axis=1)
    
    # Tratar variáveis de desempenho
    performance_vars = ['fb_Min%', 'fb_90s', 'fb_Starts', 'fb_PPM']
    for var in performance_vars:
        if var in df.columns:
            df[var] = df[var].fillna(0)
    
    # Criar instância da regressão
    regressao = RegressaoOLSManual(df)
    
    # Executar análises
    print("INICIANDO ANÁLISE DE REGRESSÃO OLS")
    print("="*60)
    
    # Modelo baseline
    baseline_results = regressao.modelo_baseline()
    
    # Análises de robustez
    robustez_results = regressao.analise_robustez()
    
    # Análise por posição
    posicao_results = regressao.analise_por_posicao()
    
    # Relatório final
    relatorio = regressao.gerar_relatorio_final()
    
    print("\n" + "="*60)
    print("ANÁLISE DE REGRESSÃO CONCLUÍDA!")
    print("="*60)
    
    return regressao, relatorio

if __name__ == "__main__":
    regressao, relatorio = main()
