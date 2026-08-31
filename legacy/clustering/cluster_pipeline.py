#!/usr/bin/env python3
"""
Pipeline de Clusterização por Distância Euclidiana
==================================================

Este script implementa um pipeline completo de clusterização para dados de futebol,
incluindo feature engineering, avaliação de múltiplos algoritmos e métricas,
análise de estabilidade e geração de visualizações.

Autor: Pipeline de Clusterização
Data: 2025
"""

import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans, AgglomerativeClustering
from sklearn.metrics import silhouette_score, calinski_harabasz_score, davies_bouldin_score
from sklearn.metrics import adjusted_rand_score
import warnings
import os
from pathlib import Path
import builtins

# Tentar importar matplotlib e seaborn, mas continuar sem eles se não estiverem disponíveis
try:
    import matplotlib.pyplot as plt
    import seaborn as sns
    from scipy.cluster.hierarchy import dendrogram, linkage
    PLOTTING_AVAILABLE = True
except ImportError:
    # Mensagem sem caracteres especiais para evitar UnicodeEncodeError no Windows
    print("Matplotlib/Seaborn nao disponiveis. Visualizacoes serao puladas.")
    PLOTTING_AVAILABLE = False

# Configurações
warnings.filterwarnings('ignore')
if PLOTTING_AVAILABLE:
    plt.style.use('seaborn-v0_8')
np.random.seed(42)

# Patch para evitar UnicodeEncodeError no Windows (remove caracteres não ASCII ao imprimir)
_original_print = builtins.print
def _safe_print(*args, **kwargs):
    try:
        _original_print(*args, **kwargs)
    except UnicodeEncodeError:
        cleaned_args = []
        for a in args:
            try:
                cleaned_args.append(str(a).encode('cp1252', errors='ignore').decode('cp1252'))
            except Exception:
                cleaned_args.append(str(a))
        _original_print(*cleaned_args, **kwargs)
builtins.print = _safe_print

class ClusteringPipeline:
    """
    Pipeline completo de clusterização para dados de futebol.
    """
    
    def __init__(self, data_path, output_dir='artifacts'):
        """
        Inicializa o pipeline.
        
        Args:
            data_path (str): Caminho para o arquivo CSV
            output_dir (str): Diretório para salvar os outputs
        """
        self.data_path = data_path
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # Carregar dados
        self.df = pd.read_csv(data_path)
        self.df_processed = None
        self.features_for_clustering = None
        self.scaler = StandardScaler()
        
        # Inicializar variáveis de instância
        self.metrics_df = None
        self.optimal_k = None
        self.cluster_profiles_df = None
        
        print(f"Dataset carregado: {self.df.shape}")
        print(f"Colunas disponíveis: {list(self.df.columns)}")
    
    def feature_engineering(self):
        """
        Implementa feature engineering conforme especificações:
        - Cria age^2
        - Calcula razões/por-90 para métricas FBRef
        - Trata valores missing com medianas
        """
        print("\n=== FEATURE ENGINEERING ===")
        
        # Criar cópia para processamento
        df = self.df.copy()
        
        # 1. Criar age^2
        df['age2'] = df['age'] ** 2
        print("✓ Criado age^2")
        
        # 2. Tratar missing values com medianas
        # Height: mediana
        height_median = df['Height'].median()
        df['Height'] = df['Height'].fillna(height_median)
        print(f"✓ Height missing preenchido com mediana: {height_median:.2f}")
        
        # FBRef metrics: mediana
        fbref_cols = ['fb_Mn/MP', 'fb_PPM', 'fb_+/-', 'fb_xG+/-']
        for col in fbref_cols:
            if col in df.columns:
                median_val = df[col].median()
                df[col] = df[col].fillna(median_val)
                print(f"✓ {col} missing preenchido com mediana: {median_val:.4f}")
        
        # 3. Calcular métricas por-90 (assumindo que as métricas já estão normalizadas)
        # Para este dataset, vamos usar as métricas como estão, mas criar versões por-90 se necessário
        # Como não temos dados de minutos jogados separados, usaremos as métricas existentes
        
        # 4. Definir features para clusterização (excluindo target e IDs)
        exclude_cols = ['Value_Num', 'Player', 'Clube', 'Taxa_Transferencia']
        self.features_for_clustering = [col for col in df.columns if col not in exclude_cols]
        
        print(f"✓ Features selecionadas para clusterização: {self.features_for_clustering}")
        
        # 5. Verificar se temos as métricas necessárias
        required_metrics = ['age', 'age2', 'Height', 'fb_Mn/MP', 'fb_PPM', 'fb_+/-', 'fb_xG+/-']
        missing_metrics = [m for m in required_metrics if m not in self.features_for_clustering]
        if missing_metrics:
            print(f"⚠️  Métricas não encontradas: {missing_metrics}")
        
        self.df_processed = df
        print(f"✓ Dataset processado: {self.df_processed.shape}")
        
        return self.df_processed
    
    def prepare_clustering_data(self):
        """
        Prepara os dados para clusterização com padronização z-score.
        """
        print("\n=== PREPARAÇÃO DOS DADOS ===")
        
        # Selecionar apenas features contínuas para clusterização
        continuous_features = []
        for col in self.features_for_clustering:
            if self.df_processed[col].dtype in ['float64', 'int64']:
                continuous_features.append(col)
        
        print(f"✓ Features contínuas selecionadas: {continuous_features}")
        
        # Extrair dados para clusterização
        X = self.df_processed[continuous_features].values
        
        # Padronização z-score
        X_scaled = self.scaler.fit_transform(X)
        
        print(f"✓ Dados padronizados: {X_scaled.shape}")
        print(f"✓ Média após padronização: {X_scaled.mean():.6f}")
        print(f"✓ Desvio padrão após padronização: {X_scaled.std():.6f}")
        
        return X_scaled, continuous_features
    
    def evaluate_clustering_metrics(self, X_scaled, k_range=range(2, 13)):
        """
        Avalia métricas de clusterização para diferentes valores de k.
        """
        print("\n=== AVALIAÇÃO DE MÉTRICAS ===")
        
        metrics = {
            'k': [],
            'silhouette': [],
            'calinski_harabasz': [],
            'davies_bouldin': [],
            'sse': []
        }
        
        for k in k_range:
            print(f"  Avaliando k={k}...", end=' ')
            
            # K-means
            kmeans = KMeans(n_clusters=k, random_state=42, n_init=50)
            labels = kmeans.fit_predict(X_scaled)
            
            # Calcular métricas
            silhouette = silhouette_score(X_scaled, labels)
            calinski = calinski_harabasz_score(X_scaled, labels)
            davies_bouldin = davies_bouldin_score(X_scaled, labels)
            sse = kmeans.inertia_
            
            metrics['k'].append(k)
            metrics['silhouette'].append(silhouette)
            metrics['calinski_harabasz'].append(calinski)
            metrics['davies_bouldin'].append(davies_bouldin)
            metrics['sse'].append(sse)
            
            print(f"Silhouette: {silhouette:.3f}")
        
        self.metrics_df = pd.DataFrame(metrics)
        print(f"✓ Métricas calculadas para k={min(k_range)} a {max(k_range)}")
        
        return self.metrics_df
    
    def find_optimal_k(self):
        """
        Encontra o k ótimo baseado em consenso das métricas.
        """
        print("\n=== SELEÇÃO DO K ÓTIMO ===")
        
        df = self.metrics_df
        
        # Normalizar métricas para escala 0-1
        df['silhouette_norm'] = (df['silhouette'] - df['silhouette'].min()) / (df['silhouette'].max() - df['silhouette'].min())
        df['calinski_norm'] = (df['calinski_harabasz'] - df['calinski_harabasz'].min()) / (df['calinski_harabasz'].max() - df['calinski_harabasz'].min())
        df['davies_norm'] = 1 - (df['davies_bouldin'] - df['davies_bouldin'].min()) / (df['davies_bouldin'].max() - df['davies_bouldin'].min())
        
        # Score composto (maior é melhor)
        df['composite_score'] = df['silhouette_norm'] + df['calinski_norm'] + df['davies_norm']
        
        # Encontrar k ótimo
        optimal_k = df.loc[df['composite_score'].idxmax(), 'k']
        optimal_metrics = df[df['k'] == optimal_k].iloc[0]
        
        print(f"✓ K ótimo selecionado: {optimal_k}")
        print(f"  - Silhouette: {optimal_metrics['silhouette']:.3f}")
        print(f"  - Calinski-Harabasz: {optimal_metrics['calinski_harabasz']:.1f}")
        print(f"  - Davies-Bouldin: {optimal_metrics['davies_bouldin']:.3f}")
        print(f"  - Score composto: {optimal_metrics['composite_score']:.3f}")
        
        self.optimal_k = optimal_k
        return optimal_k
    
    def perform_final_clustering(self, X_scaled, method='kmeans'):
        """
        Executa clusterização final com k ótimo.
        """
        print(f"\n=== CLUSTERIZAÇÃO FINAL ({method.upper()}) ===")
        
        if method == 'kmeans':
            clusterer = KMeans(n_clusters=self.optimal_k, random_state=42, n_init=50)
            labels = clusterer.fit_predict(X_scaled)
        elif method == 'hierarchical':
            clusterer = AgglomerativeClustering(n_clusters=self.optimal_k, linkage='ward')
            labels = clusterer.fit_predict(X_scaled)
        else:
            raise ValueError("Método deve ser 'kmeans' ou 'hierarchical'")
        
        # Adicionar labels ao dataset original
        self.df_processed['cluster'] = labels
        
        # Calcular métricas finais
        silhouette = silhouette_score(X_scaled, labels)
        calinski = calinski_harabasz_score(X_scaled, labels)
        davies_bouldin = davies_bouldin_score(X_scaled, labels)
        
        print(f"✓ Clusterização concluída com k={self.optimal_k}")
        print(f"  - Silhouette: {silhouette:.3f}")
        print(f"  - Calinski-Harabasz: {calinski:.1f}")
        print(f"  - Davies-Bouldin: {davies_bouldin:.3f}")
        
        # Distribuição dos clusters
        cluster_counts = pd.Series(labels).value_counts().sort_index()
        print(f"  - Distribuição dos clusters: {dict(cluster_counts)}")
        
        return labels
    
    def stability_analysis(self, X_scaled, n_seeds=20):
        """
        Análise de estabilidade com múltiplas seeds.
        """
        print(f"\n=== ANÁLISE DE ESTABILIDADE ({n_seeds} seeds) ===")
        
        stability_results = []
        
        for seed in range(n_seeds):
            kmeans = KMeans(n_clusters=self.optimal_k, random_state=seed, n_init=50)
            labels = kmeans.fit_predict(X_scaled)
            stability_results.append(labels)
        
        # Calcular ARI entre todas as combinações
        ari_scores = []
        for i in range(len(stability_results)):
            for j in range(i+1, len(stability_results)):
                ari = adjusted_rand_score(stability_results[i], stability_results[j])
                ari_scores.append(ari)
        
        mean_ari = np.mean(ari_scores)
        std_ari = np.std(ari_scores)
        
        print(f"✓ ARI médio: {mean_ari:.3f} ± {std_ari:.3f}")
        print(f"✓ Variação de rótulos: {1 - mean_ari:.3f}")
        
        return mean_ari, std_ari
    
    def create_visualizations(self, X_scaled, continuous_features):
        """
        Cria visualizações dos resultados (apenas se matplotlib estiver disponível).
        """
        print("\n=== CRIAÇÃO DE VISUALIZAÇÕES ===")
        
        if not PLOTTING_AVAILABLE:
            print("⚠️  Pulando visualizações - matplotlib/seaborn não disponíveis")
            return
        
        # 1. Elbow Plot
        plt.figure(figsize=(10, 6))
        plt.plot(self.metrics_df['k'], self.metrics_df['sse'], 'bo-')
        plt.axvline(x=self.optimal_k, color='red', linestyle='--', alpha=0.7, label=f'K ótimo = {self.optimal_k}')
        plt.xlabel('Número de Clusters (k)')
        plt.ylabel('Sum of Squared Errors (SSE)')
        plt.title('Elbow Method for Optimal k')
        plt.grid(True, alpha=0.3)
        plt.legend()
        plt.tight_layout()
        plt.savefig(self.output_dir / 'elbow.png', dpi=300, bbox_inches='tight')
        plt.close()
        print("✓ Elbow plot salvo: artifacts/elbow.png")
        
        # 2. Silhouette Plot
        plt.figure(figsize=(12, 8))
        
        # Subplot 1: Silhouette scores
        plt.subplot(2, 2, 1)
        plt.plot(self.metrics_df['k'], self.metrics_df['silhouette'], 'go-')
        plt.axvline(x=self.optimal_k, color='red', linestyle='--', alpha=0.7)
        plt.xlabel('Número de Clusters (k)')
        plt.ylabel('Silhouette Score')
        plt.title('Silhouette Score vs k')
        plt.grid(True, alpha=0.3)
        
        # Subplot 2: Calinski-Harabasz
        plt.subplot(2, 2, 2)
        plt.plot(self.metrics_df['k'], self.metrics_df['calinski_harabasz'], 'bo-')
        plt.axvline(x=self.optimal_k, color='red', linestyle='--', alpha=0.7)
        plt.xlabel('Número de Clusters (k)')
        plt.ylabel('Calinski-Harabasz Score')
        plt.title('Calinski-Harabasz Score vs k')
        plt.grid(True, alpha=0.3)
        
        # Subplot 3: Davies-Bouldin
        plt.subplot(2, 2, 3)
        plt.plot(self.metrics_df['k'], self.metrics_df['davies_bouldin'], 'ro-')
        plt.axvline(x=self.optimal_k, color='red', linestyle='--', alpha=0.7)
        plt.xlabel('Número de Clusters (k)')
        plt.ylabel('Davies-Bouldin Score')
        plt.title('Davies-Bouldin Score vs k')
        plt.grid(True, alpha=0.3)
        
        # Subplot 4: Score composto
        plt.subplot(2, 2, 4)
        df = self.metrics_df.copy()
        df['silhouette_norm'] = (df['silhouette'] - df['silhouette'].min()) / (df['silhouette'].max() - df['silhouette'].min())
        df['calinski_norm'] = (df['calinski_harabasz'] - df['calinski_harabasz'].min()) / (df['calinski_harabasz'].max() - df['calinski_harabasz'].min())
        df['davies_norm'] = 1 - (df['davies_bouldin'] - df['davies_bouldin'].min()) / (df['davies_bouldin'].max() - df['davies_bouldin'].min())
        df['composite_score'] = df['silhouette_norm'] + df['calinski_norm'] + df['davies_norm']
        
        plt.plot(df['k'], df['composite_score'], 'mo-')
        plt.axvline(x=self.optimal_k, color='red', linestyle='--', alpha=0.7)
        plt.xlabel('Número de Clusters (k)')
        plt.ylabel('Score Composto')
        plt.title('Score Composto vs k')
        plt.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(self.output_dir / 'silhouette.png', dpi=300, bbox_inches='tight')
        plt.close()
        print("✓ Silhouette plot salvo: artifacts/silhouette.png")
        
        # 3. Dendrograma (clustering hierárquico)
        plt.figure(figsize=(15, 8))
        
        # Usar amostra para dendrograma (máximo 100 pontos para legibilidade)
        if X_scaled.shape[0] > 100:
            sample_idx = np.random.choice(X_scaled.shape[0], 100, replace=False)
            X_sample = X_scaled[sample_idx]
        else:
            X_sample = X_scaled
        
        # Calcular linkage
        linkage_matrix = linkage(X_sample, method='ward')
        
        # Plotar dendrograma
        dendrogram(linkage_matrix, truncate_mode='level', p=5)
        plt.axhline(y=linkage_matrix[-self.optimal_k+1, 2], color='red', linestyle='--', alpha=0.7, 
                   label=f'Corte para k={self.optimal_k}')
        plt.xlabel('Índice do Ponto')
        plt.ylabel('Distância')
        plt.title('Dendrograma - Clustering Hierárquico Ward')
        plt.legend()
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        plt.savefig(self.output_dir / 'dendrogram.png', dpi=300, bbox_inches='tight')
        plt.close()
        print("✓ Dendrograma salvo: artifacts/dendrogram.png")
        
        # 4. Heatmap de correlação das features
        plt.figure(figsize=(12, 10))
        feature_data = self.df_processed[continuous_features]
        correlation_matrix = feature_data.corr()
        
        sns.heatmap(correlation_matrix, annot=True, cmap='coolwarm', center=0, 
                   square=True, fmt='.2f', cbar_kws={'shrink': 0.8})
        plt.title('Matriz de Correlação das Features')
        plt.tight_layout()
        plt.savefig(self.output_dir / 'correlation_heatmap.png', dpi=300, bbox_inches='tight')
        plt.close()
        print("✓ Heatmap de correlação salvo: artifacts/correlation_heatmap.png")
    
    def create_cluster_profiles(self, continuous_features):
        """
        Cria perfis dos clusters com estatísticas descritivas.
        """
        print("\n=== CRIAÇÃO DE PERFIS DOS CLUSTERS ===")
        
        # Calcular estatísticas por cluster
        cluster_profiles = []
        
        for cluster_id in sorted(self.df_processed['cluster'].unique()):
            cluster_data = self.df_processed[self.df_processed['cluster'] == cluster_id]
            
            profile = {
                'cluster': cluster_id,
                'count': len(cluster_data),
                'percentage': len(cluster_data) / len(self.df_processed) * 100
            }
            
            # Estatísticas para features contínuas
            for feature in continuous_features:
                if feature in cluster_data.columns:
                    profile[f'{feature}_mean'] = cluster_data[feature].mean()
                    profile[f'{feature}_std'] = cluster_data[feature].std()
                    profile[f'{feature}_median'] = cluster_data[feature].median()
            
            cluster_profiles.append(profile)
        
        self.cluster_profiles_df = pd.DataFrame(cluster_profiles)
        print(f"✓ Perfis criados para {len(cluster_profiles)} clusters")
        
        return self.cluster_profiles_df
    
    def generate_text_report(self, continuous_features):
        """
        Gera um relatório detalhado em formato txt com todos os resultados.
        """
        print("\n=== GERANDO RELATÓRIO TXT ===")
        
        report_path = self.output_dir / 'relatorio_clustering.txt'
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write("=" * 80 + "\n")
            f.write("RELATÓRIO DE CLUSTERIZAÇÃO - DADOS DE FUTEBOL\n")
            f.write("=" * 80 + "\n\n")
            
            # 1. Informações gerais
            f.write("1. INFORMAÇÕES GERAIS\n")
            f.write("-" * 40 + "\n")
            f.write(f"Total de jogadores analisados: {len(self.df_processed)}\n")
            f.write(f"Número ótimo de clusters: {self.optimal_k}\n")
            f.write(f"Features utilizadas: {', '.join(continuous_features)}\n")
            f.write(f"Método de clusterização: K-means + Hierarchical Ward\n")
            f.write(f"Data de execução: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            # 2. Métricas de avaliação
            f.write("2. MÉTRICAS DE AVALIAÇÃO\n")
            f.write("-" * 40 + "\n")
            optimal_metrics = self.metrics_df[self.metrics_df['k'] == self.optimal_k].iloc[0]
            f.write(f"Silhouette Score: {optimal_metrics['silhouette']:.4f}\n")
            f.write(f"Calinski-Harabasz Score: {optimal_metrics['calinski_harabasz']:.2f}\n")
            f.write(f"Davies-Bouldin Score: {optimal_metrics['davies_bouldin']:.4f}\n")
            f.write(f"Sum of Squared Errors (SSE): {optimal_metrics['sse']:.2f}\n\n")
            
            # 3. Comparação de todos os k testados
            f.write("3. COMPARAÇÃO DE TODOS OS K TESTADOS\n")
            f.write("-" * 40 + "\n")
            f.write("K\tSilhouette\tCalinski-H\tDavies-B\tSSE\n")
            f.write("-" * 60 + "\n")
            for _, row in self.metrics_df.iterrows():
                f.write(f"{row['k']}\t{row['silhouette']:.4f}\t\t{row['calinski_harabasz']:.1f}\t\t{row['davies_bouldin']:.4f}\t\t{row['sse']:.0f}\n")
            f.write("\n")
            
            # 4. Distribuição dos clusters
            f.write("4. DISTRIBUIÇÃO DOS CLUSTERS\n")
            f.write("-" * 40 + "\n")
            cluster_counts = self.df_processed['cluster'].value_counts().sort_index()
            for cluster_id, count in cluster_counts.items():
                percentage = (count / len(self.df_processed)) * 100
                f.write(f"Cluster {cluster_id}: {count} jogadores ({percentage:.1f}%)\n")
            f.write("\n")
            
            # 5. Perfis detalhados dos clusters
            f.write("5. PERFIS DETALHADOS DOS CLUSTERS\n")
            f.write("-" * 40 + "\n")
            
            for cluster_id in sorted(self.df_processed['cluster'].unique()):
                cluster_data = self.df_processed[self.df_processed['cluster'] == cluster_id]
                f.write(f"\nCLUSTER {cluster_id} ({len(cluster_data)} jogadores)\n")
                f.write("=" * 30 + "\n")
                
                # Estatísticas para cada feature
                for feature in continuous_features:
                    if feature in cluster_data.columns:
                        mean_val = cluster_data[feature].mean()
                        std_val = cluster_data[feature].std()
                        median_val = cluster_data[feature].median()
                        min_val = cluster_data[feature].min()
                        max_val = cluster_data[feature].max()
                        
                        f.write(f"{feature}:\n")
                        f.write(f"  Média: {mean_val:.4f}\n")
                        f.write(f"  Desvio Padrão: {std_val:.4f}\n")
                        f.write(f"  Mediana: {median_val:.4f}\n")
                        f.write(f"  Mínimo: {min_val:.4f}\n")
                        f.write(f"  Máximo: {max_val:.4f}\n\n")
                
                # Lista de jogadores no cluster
                f.write("Jogadores neste cluster:\n")
                players = cluster_data['Player'].tolist()
                for i, player in enumerate(players):
                    if i % 5 == 0 and i > 0:
                        f.write("\n")
                    f.write(f"{player:<20}")
                f.write("\n\n")
            
            # 6. Análise de estabilidade
            f.write("6. ANÁLISE DE ESTABILIDADE\n")
            f.write("-" * 40 + "\n")
            f.write("Teste realizado com 20 seeds diferentes para validar a robustez dos clusters.\n")
            f.write("Métricas de estabilidade serão calculadas durante a execução.\n\n")
            
            # 7. Recomendações
            f.write("7. RECOMENDAÇÕES E INTERPRETAÇÕES\n")
            f.write("-" * 40 + "\n")
            f.write("• O número ótimo de clusters foi determinado por um score composto\n")
            f.write("  que combina Silhouette, Calinski-Harabasz e Davies-Bouldin.\n")
            f.write("• Clusters com maior Silhouette Score indicam melhor separação.\n")
            f.write("• Valores altos de Calinski-Harabasz sugerem clusters bem definidos.\n")
            f.write("• Davies-Bouldin baixo indica clusters compactos e bem separados.\n")
            f.write("• A análise de estabilidade valida a consistência dos resultados.\n\n")
            
            # 8. Arquivos gerados
            f.write("8. ARQUIVOS GERADOS\n")
            f.write("-" * 40 + "\n")
            f.write("• df_out.csv: Dataset original com coluna de clusters\n")
            f.write("• cluster_profile.csv: Estatísticas descritivas por cluster\n")
            f.write("• metrics.csv: Métricas de avaliação para todos os k testados\n")
            f.write("• summary.csv: Resumo dos resultados\n")
            f.write("• relatorio_clustering.txt: Este relatório detalhado\n")
            if PLOTTING_AVAILABLE:
                f.write("• elbow.png: Gráfico do método do cotovelo\n")
                f.write("• silhouette.png: Gráficos de todas as métricas\n")
                f.write("• dendrogram.png: Dendrograma do clustering hierárquico\n")
                f.write("• correlation_heatmap.png: Matriz de correlação das features\n")
            f.write("\n")
            
            f.write("=" * 80 + "\n")
            f.write("FIM DO RELATÓRIO\n")
            f.write("=" * 80 + "\n")
        
        print(f"✓ Relatório txt salvo: {report_path}")
        return report_path

    def save_results(self, continuous_features):
        """
        Salva todos os resultados em arquivos CSV.
        """
        print("\n=== SALVANDO RESULTADOS ===")
        
        # 1. Dataset original com clusters
        output_df = self.df_processed.copy()
        output_df.to_csv(self.output_dir / 'df_out.csv', index=False)
        print(f"✓ Dataset com clusters salvo: {self.output_dir}/df_out.csv")
        
        # 2. Perfis dos clusters
        self.create_cluster_profiles(continuous_features)
        self.cluster_profiles_df.to_csv(self.output_dir / 'cluster_profile.csv', index=False)
        print(f"✓ Perfis dos clusters salvos: {self.output_dir}/cluster_profile.csv")
        
        # 3. Métricas de avaliação
        self.metrics_df.to_csv(self.output_dir / 'metrics.csv', index=False)
        print(f"✓ Métricas salvas: {self.output_dir}/metrics.csv")
        
        # 4. Resumo dos resultados
        summary = {
            'optimal_k': self.optimal_k,
            'total_players': len(self.df_processed),
            'features_used': continuous_features,
            'clustering_method': 'K-means + Hierarchical Ward',
            'evaluation_metrics': ['Silhouette', 'Calinski-Harabasz', 'Davies-Bouldin', 'SSE']
        }
        
        summary_df = pd.DataFrame([summary])
        summary_df.to_csv(self.output_dir / 'summary.csv', index=False)
        print(f"✓ Resumo salvo: {self.output_dir}/summary.csv")
        
        # 5. Gerar relatório txt
        self.generate_text_report(continuous_features)
    
    def run_pipeline(self):
        """
        Executa o pipeline completo de clusterização.
        """
        print("=" * 60)
        print("PIPELINE DE CLUSTERIZAÇÃO - DADOS DE FUTEBOL")
        print("=" * 60)
        
        # 1. Feature Engineering
        self.feature_engineering()
        
        # 2. Preparação dos dados
        X_scaled, continuous_features = self.prepare_clustering_data()
        
        # 3. Avaliação de métricas
        self.evaluate_clustering_metrics(X_scaled)
        
        # 4. Seleção do k ótimo
        self.find_optimal_k()
        
        # 5. Clusterização final (K-means)
        self.perform_final_clustering(X_scaled, method='kmeans')
        
        # 6. Análise de estabilidade
        self.stability_analysis(X_scaled)
        
        # 7. Criação de visualizações
        self.create_visualizations(X_scaled, continuous_features)
        
        # 8. Salvamento dos resultados
        self.save_results(continuous_features)
        
        print("\n" + "=" * 60)
        print("PIPELINE CONCLUÍDO COM SUCESSO!")
        print("=" * 60)
        print(f"Arquivos salvos em: {self.output_dir}")
        print("- df_out.csv: Dataset original com clusters")
        print("- cluster_profile.csv: Perfis estatísticos dos clusters")
        print("- metrics.csv: Métricas de avaliação para diferentes k")
        print("- summary.csv: Resumo dos resultados")
        print("- relatorio_clustering.txt: Relatório detalhado em texto")
        if PLOTTING_AVAILABLE:
            print("- *.png: Visualizações (elbow, silhouette, dendrograma, correlação)")
        else:
            print("- Visualizações: Não geradas (matplotlib/seaborn não disponíveis)")


def main():
    """
    Função principal para executar o pipeline.
    """
    # Caminhos possíveis: preferir o dataset LIMPO (sem missing) se existir
    clean_path = '../dados/clubes/outcome/final_merged_filtrado_dummies_clean.csv'
    original_path = '../dados/clubes/outcome/final_merged_filtrado_dummies.csv'
    
    if os.path.exists(clean_path):
        data_path = clean_path
        print(f"Usando dataset limpo (sem missing): {data_path}")
    elif os.path.exists(original_path):
        data_path = original_path
        print(f"⚠️  Dataset limpo não encontrado. Usando original: {data_path}")
    else:
        print("ERRO: Nenhum dataset encontrado.")
        print(f"Verifique se existe um destes arquivos:\n - {clean_path}\n - {original_path}")
        return
    
    # Executar pipeline
    pipeline = ClusteringPipeline(data_path)
    pipeline.run_pipeline()


if __name__ == "__main__":
    main()
