"""
Análise Econométrica Básica - Valoração de Atletas
Versão simplificada usando apenas pandas e numpy

Autor: Assistente IA
Data: 2025
"""

import pandas as pd
import numpy as np
import warnings
warnings.filterwarnings('ignore')

class AnaliseEconometricaBasica:
    def __init__(self, file_path):
        """Inicializa a análise com o dataset"""
        self.df = pd.read_csv(file_path)
        self.df_original = self.df.copy()
        self.results = {}
        self.diagnostics = {}
        
    def explorar_dados(self):
        """Exploração inicial dos dados"""
        print("="*60)
        print("EXPLORAÇÃO INICIAL DOS DADOS")
        print("="*60)
        
        print(f"Shape do dataset: {self.df.shape}")
        print(f"\nZeros em Value_Num: {(self.df['Value_Num'] == 0).sum()} ({(self.df['Value_Num'] == 0).mean()*100:.1f}%)")
        
        # Estatísticas descritivas de Value_Num
        print("\nEstatísticas descritivas de Value_Num:")
        print(self.df['Value_Num'].describe())
        
        # Missing values
        print("\nMissing values por coluna (top 15):")
        missing = self.df.isnull().sum().sort_values(ascending=False)
        print(missing.head(15))
        
        # Distribuição de posições
        print("\nDistribuição de posições:")
        print(self.df['Position'].value_counts())
        
        return self.df.describe()
    
    def preparar_variaveis(self):
        """Preparação das variáveis seguindo as diretrizes"""
        print("\n" + "="*60)
        print("PREPARAÇÃO DAS VARIÁVEIS")
        print("="*60)
        
        # 1. Transformação logarítmica
        self.df['ln_value'] = np.log(self.df['Value_Num'] + 1)  # +1 para evitar log(0)
        
        # 2. Criar dummy para zeros (para modelo em duas partes)
        self.df['has_value'] = (self.df['Value_Num'] > 0).astype(int)
        
        # 3. Idade quadrática
        self.df['age_squared'] = self.df['age'] ** 2
        
        # 4. Dummies de posição (evitando armadilha de dummies)
        position_dummies = pd.get_dummies(self.df['Position'], prefix='pos', drop_first=True)
        self.df = pd.concat([self.df, position_dummies], axis=1)
        
        # 5. Dummy de nacionalidade brasileira
        self.df['is_brazilian'] = self.df['Nation'].str.contains('Brasil', na=False).astype(int)
        
        # 6. Tratamento de Taxa_Transferencia
        self.df['transfer_fee_clean'] = pd.to_numeric(self.df['Taxa_Transferencia'], errors='coerce')
        self.df['transfer_fee_missing'] = self.df['Taxa_Transferencia'].isin(['?', '-', '']).astype(int)
        self.df['transfer_fee_clean'] = self.df['transfer_fee_clean'].fillna(0)
        
        # 7. Variáveis de desempenho (tratando missing)
        performance_vars = ['fb_Min%', 'fb_90s', 'fb_Starts', 'fb_PPM', 'fb_onG', 'fb_onGA']
        
        for var in performance_vars:
            if var in self.df.columns:
                # Criar dummy de missing
                self.df[f'{var}_missing'] = self.df[var].isnull().astype(int)
                # Preencher missing com 0
                self.df[var] = self.df[var].fillna(0)
        
        # 8. Normalizar altura (z-score)
        self.df['height_z'] = (self.df['Height'] - self.df['Height'].mean()) / self.df['Height'].std()
        
        print("Variáveis criadas:")
        print("- ln_value: logaritmo do valor")
        print("- has_value: dummy para valor > 0")
        print("- age_squared: idade ao quadrado")
        print("- Dummies de posição (evitando armadilha)")
        print("- is_brazilian: dummy de nacionalidade")
        print("- transfer_fee_clean: taxa de transferência limpa")
        print("- Dummies de missing para variáveis de desempenho")
        print("- height_z: altura normalizada")
        
        return self.df
    
    def calcular_correlacoes(self):
        """Calcula matriz de correlações para detectar multicolinearidade"""
        print("\n" + "="*60)
        print("ANÁLISE DE CORRELAÇÕES")
        print("="*60)
        
        # Variáveis numéricas principais
        numeric_vars = ['ln_value', 'age', 'age_squared', 'Height', 'is_brazilian', 
                       'transfer_fee_clean', 'fb_Min%', 'fb_90s', 'fb_Starts', 'fb_PPM']
        
        # Filtrar variáveis que existem no dataset
        available_vars = [var for var in numeric_vars if var in self.df.columns]
        
        # Calcular correlações
        corr_matrix = self.df[available_vars].corr()
        
        print("Matriz de correlações:")
        print(corr_matrix.round(3))
        
        # Identificar correlações altas (>0.8)
        high_corr = []
        for i in range(len(corr_matrix.columns)):
            for j in range(i+1, len(corr_matrix.columns)):
                corr_val = abs(corr_matrix.iloc[i, j])
                if corr_val > 0.8:
                    high_corr.append((corr_matrix.columns[i], corr_matrix.columns[j], corr_val))
        
        if high_corr:
            print(f"\nCorrelações altas (>0.8):")
            for var1, var2, corr in high_corr:
                print(f"{var1} - {var2}: {corr:.3f}")
        else:
            print("\nNenhuma correlação alta detectada.")
        
        return corr_matrix
    
    def analise_por_posicao(self):
        """Análise descritiva por posição"""
        print("\n" + "="*60)
        print("ANÁLISE POR POSIÇÃO")
        print("="*60)
        
        # Estatísticas por posição
        pos_stats = self.df.groupby('Position').agg({
            'ln_value': ['count', 'mean', 'std', 'min', 'max'],
            'age': ['mean', 'std'],
            'Height': ['mean', 'std'],
            'Value_Num': ['mean', 'median']
        }).round(3)
        
        print("Estatísticas por posição:")
        print(pos_stats)
        
        # Análise de zeros por posição
        zeros_por_pos = self.df.groupby('Position')['has_value'].agg(['count', 'sum']).reset_index()
        zeros_por_pos['pct_zeros'] = (zeros_por_pos['count'] - zeros_por_pos['sum']) / zeros_por_pos['count'] * 100
        
        print(f"\nZeros por posição:")
        print(zeros_por_pos)
        
        return pos_stats
    
    def analise_robustez_basica(self):
        """Análises de robustez básicas"""
        print("\n" + "="*60)
        print("ANÁLISES DE ROBUSTEZ BÁSICAS")
        print("="*60)
        
        # Amostra com valores positivos
        sample_positive = self.df[self.df['has_value'] == 1].copy()
        print(f"Amostra com valores positivos: {len(sample_positive)} observações")
        
        # Amostra sem top 1%
        threshold_99 = np.percentile(sample_positive['ln_value'], 99)
        sample_no_outliers = sample_positive[sample_positive['ln_value'] <= threshold_99].copy()
        print(f"Amostra sem top 1%: {len(sample_no_outliers)} observações")
        
        # Comparar estatísticas
        print(f"\nComparação de estatísticas:")
        print(f"ln_value - Amostra completa: média={self.df['ln_value'].mean():.3f}, std={self.df['ln_value'].std():.3f}")
        print(f"ln_value - Valores positivos: média={sample_positive['ln_value'].mean():.3f}, std={sample_positive['ln_value'].std():.3f}")
        print(f"ln_value - Sem outliers: média={sample_no_outliers['ln_value'].mean():.3f}, std={sample_no_outliers['ln_value'].std():.3f}")
        
        return {
            'sample_positive': sample_positive,
            'sample_no_outliers': sample_no_outliers
        }
    
    def gerar_tabelas_resultados(self):
        """Gera tabelas de resultados finais"""
        print("\n" + "="*60)
        print("TABELAS DE RESULTADOS")
        print("="*60)
        
        # Tabela 1: Estatísticas descritivas
        print("\nTABELA 1: ESTATÍSTICAS DESCRITIVAS")
        desc_vars = ['ln_value', 'age', 'Height', 'fb_Min%', 'fb_90s', 'fb_Starts', 'Value_Num']
        desc_vars = [var for var in desc_vars if var in self.df.columns]
        
        desc_stats = self.df[desc_vars].describe()
        print(desc_stats.round(3))
        
        # Tabela 2: Distribuição de zeros
        print("\nTABELA 2: DISTRIBUIÇÃO DE ZEROS")
        zeros_summary = pd.DataFrame({
            'Total_Observações': [len(self.df)],
            'Valores_Positivos': [self.df['has_value'].sum()],
            'Valores_Zero': [(self.df['has_value'] == 0).sum()],
            'Pct_Zeros': [(self.df['has_value'] == 0).mean() * 100]
        })
        print(zeros_summary.round(2))
        
        # Tabela 3: Por posição
        print("\nTABELA 3: ESTATÍSTICAS POR POSIÇÃO")
        pos_summary = self.df.groupby('Position').agg({
            'ln_value': ['count', 'mean', 'std'],
            'age': 'mean',
            'Value_Num': 'mean'
        }).round(3)
        print(pos_summary)
        
        return {
            'descritivas': desc_stats,
            'zeros': zeros_summary,
            'por_posicao': pos_summary
        }
    
    def executar_analise_completa(self):
        """Executa a análise completa"""
        print("INICIANDO ANÁLISE ECONOMÉTRICA BÁSICA")
        print("="*60)
        
        # 1. Exploração
        self.explorar_dados()
        
        # 2. Preparação
        self.preparar_variaveis()
        
        # 3. Correlações
        corr_matrix = self.calcular_correlacoes()
        
        # 4. Análise por posição
        pos_stats = self.analise_por_posicao()
        
        # 5. Robustez
        robustez = self.analise_robustez_basica()
        
        # 6. Tabelas finais
        tabelas = self.gerar_tabelas_resultados()
        
        print("\n" + "="*60)
        print("ANÁLISE CONCLUÍDA COM SUCESSO!")
        print("="*60)
        
        # Resumo das principais descobertas
        print("\nPRINCIPAIS DESCOBERTAS:")
        print(f"• Dataset com {len(self.df)} observações")
        print(f"• {self.df['has_value'].sum()} atletas com valor de mercado positivo")
        print(f"• {(self.df['has_value'] == 0).mean()*100:.1f}% dos atletas têm valor zero")
        print(f"• Valor médio (log): {self.df['ln_value'].mean():.3f}")
        print(f"• Idade média: {self.df['age'].mean():.1f} anos")
        print(f"• {self.df['is_brazilian'].mean()*100:.1f}% são brasileiros")
        
        return {
            'correlacoes': corr_matrix,
            'pos_stats': pos_stats,
            'robustez': robustez,
            'tabelas': tabelas
        }

def main():
    """Função principal"""
    # Caminho do arquivo
    file_path = r'C:\Users\IGOR\Desktop\UFSC\TCC\dados\clubes\outcome\final_merged_fixed.csv'
    
    # Criar instância da análise
    analise = AnaliseEconometricaBasica(file_path)
    
    # Executar análise completa
    resultados = analise.executar_analise_completa()
    
    return analise, resultados

if __name__ == "__main__":
    analise, resultados = main()
