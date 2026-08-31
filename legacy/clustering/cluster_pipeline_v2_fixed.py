#!/usr/bin/env python3

"""

Pipeline de Clusterização (v2): clusteriza df_final.csv usando ln_Value_Num e pos_rnc.

Método: K-means com distância euclidiana.

Restrição: cada cluster deve ter n>=40.

Saída: pasta 'dados/cluster/' com CSVs individuais por cluster.

"""



import pandas as pd

import numpy as np

import matplotlib.pyplot as plt

import seaborn as sns

from sklearn.preprocessing import StandardScaler

from sklearn.cluster import KMeans

from sklearn.metrics import silhouette_score, calinski_harabasz_score, davies_bouldin_score, silhouette_samples

from sklearn.decomposition import PCA

from scipy.cluster.hierarchy import dendrogram, linkage

import warnings

import os

from pathlib import Path

import builtins



# Configurações

warnings.filterwarnings('ignore')

np.random.seed(42)

plt.style.use('default')

sns.set_palette("husl")



# Patch para evitar UnicodeEncodeError no Windows

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



class ClusteringPipelineV2:

    def __init__(self, data_path, output_dir=None):

        self.data_path = data_path

        if output_dir is None:

            # Usar caminho absoluto baseado no diretório do projeto

            project_root = Path(__file__).parent.parent

            self.output_dir = project_root / 'dados' / 'cluster'

        else:
            self.output_dir = Path(output_dir)

        self.output_dir.mkdir(parents=True, exist_ok=True)



        # Carregar dados

        self.df = pd.read_csv(data_path)

        self.df_processed = None

        self.scaler = StandardScaler()



        print(f"Dataset carregado: {self.df.shape}")

        print(f"Colunas disponíveis: {list(self.df.columns)}")

    

    def prepare_data(self):

        """Prepara dados usando ln_Value_Num e pos_rnc."""

        print("\n=== PREPARAÇÃO DOS DADOS ===")

        

        # Verificar colunas necessárias

        required_cols = ['ln_Value_Num', 'pos_rnc']

        missing_cols = [col for col in required_cols if col not in self.df.columns]

        if missing_cols:

            raise KeyError(f"Colunas não encontradas: {missing_cols}")

        

        # Filtrar linhas com valores válidos

        df_clean = self.df[required_cols].dropna()

        print(f"Linhas válidas após limpeza: {len(df_clean)}")

        

        # Padronização z-score

        X_scaled = self.scaler.fit_transform(df_clean)

        

        print(f"Dados padronizados: {X_scaled.shape}")

        print(f"Média após padronização: {X_scaled.mean():.6f}")

        print(f"Desvio padrão após padronização: {X_scaled.std():.6f}")

        

        return X_scaled, df_clean.index

    

    def find_optimal_k(self, X_scaled, min_cluster_size=40):

        """Encontra k ótimo garantindo n>=40 por cluster."""

        print(f"\n=== SELEÇÃO DO K ÓTIMO (min_cluster_size={min_cluster_size}) ===")

        

        max_k = len(X_scaled) // min_cluster_size

        if max_k < 2:

            print(f"⚠️  Dados insuficientes para clusters com n>={min_cluster_size}")

            return 2

        

        print(f"Testando k de 2 a {max_k}")

        

        best_k = 2

        best_score = -1

        valid_ks = []

        

        for k in range(2, max_k + 1):

            try:

                kmeans = KMeans(n_clusters=k, random_state=42, n_init=50)

                labels = kmeans.fit_predict(X_scaled)

                

                # Verificar tamanho mínimo dos clusters

                cluster_counts = pd.Series(labels).value_counts()

                min_size = cluster_counts.min()

                

                if min_size < min_cluster_size:

                    print(f"  k={k}: min_cluster_size={min_size} < {min_cluster_size} (REJEITADO)")

                    continue

                

                # Calcular métricas

                silhouette = silhouette_score(X_scaled, labels)

                calinski = calinski_harabasz_score(X_scaled, labels)

                davies_bouldin = davies_bouldin_score(X_scaled, labels)

                

                # Score composto (maior é melhor)

                score = silhouette + (calinski / 1000) + (1 - davies_bouldin)

                

                valid_ks.append({

                    'k': k,

                    'silhouette': silhouette,

                    'calinski': calinski,

                    'davies_bouldin': davies_bouldin,

                    'score': score,

                    'min_cluster_size': min_size

                })

                

                print(f"  k={k}: silhouette={silhouette:.3f}, min_size={min_size} (VÁLIDO)")

                

                if score > best_score:

                    best_score = score

                    best_k = k

                    

            except Exception as e:

                print(f"  k={k}: ERRO - {e}")

                continue

        

        if not valid_ks:

            print("⚠️  Nenhum k válido encontrado. Usando k=2")

            return 2

        

        print(f"\n✓ K ótimo selecionado: {best_k}")

        best_metrics = next(k for k in valid_ks if k['k'] == best_k)

        print(f"  - Silhouette: {best_metrics['silhouette']:.3f}")

        print(f"  - Calinski-Harabasz: {best_metrics['calinski']:.1f}")

        print(f"  - Davies-Bouldin: {best_metrics['davies_bouldin']:.3f}")

        print(f"  - Min cluster size: {best_metrics['min_cluster_size']}")

        

        return best_k

    

    def create_elbow_and_silhouette_plots(self, X_scaled, max_k=12):

        """Cria gráficos de Elbow e Silhouette médio vs k."""

        print(f"\n=== CRIANDO GRÁFICOS ELBOW E SILHOUETTE ===")

        

        k_range = range(2, max_k + 1)

        inertias = []

        silhouette_scores = []

        

        for k in k_range:

            kmeans = KMeans(n_clusters=k, random_state=42, n_init=50)

            labels = kmeans.fit_predict(X_scaled)

            

            inertias.append(kmeans.inertia_)

            silhouette_scores.append(silhouette_score(X_scaled, labels))

        

        # Criar figura com subplots

        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))

        

        # Elbow plot

        ax1.plot(k_range, inertias, 'bo-', linewidth=2, markersize=8)

        ax1.set_xlabel('Número de Clusters (k)')

        ax1.set_ylabel('Inércia (SSE)')

        ax1.set_title('Método Elbow - Inércia vs k')

        ax1.grid(True, alpha=0.3)

        ax1.set_xticks(k_range)

        

        # Silhouette plot

        ax2.plot(k_range, silhouette_scores, 'ro-', linewidth=2, markersize=8)

        ax2.set_xlabel('Número de Clusters (k)')

        ax2.set_ylabel('Silhouette Score Médio')

        ax2.set_title('Silhouette Score Médio vs k')

        ax2.grid(True, alpha=0.3)

        ax2.set_xticks(k_range)

        

        plt.tight_layout()

        

        # Salvar gráficos

        elbow_path = self.output_dir / 'elbow_and_silhouette_plots.png'

        plt.savefig(elbow_path, dpi=300, bbox_inches='tight')

        print(f"✓ Gráficos Elbow e Silhouette salvos em: {elbow_path}")

        

        plt.show()

        

        return k_range, inertias, silhouette_scores

    

    def create_detailed_silhouette_plot(self, X_scaled, labels, k):

        """Cria silhouette plot detalhado para o k escolhido."""

        print(f"\n=== CRIANDO SILHOUETTE PLOT DETALHADO (k={k}) ===")

        

        # Calcular silhouette scores para cada amostra

        silhouette_vals = silhouette_samples(X_scaled, labels)

        silhouette_avg = silhouette_score(X_scaled, labels)

        

        # Criar figura

        fig, ax = plt.subplots(figsize=(10, 8))

        

        y_lower = 10

        colors = plt.cm.viridis(np.linspace(0, 1, k))

        

        for i in range(k):

            # Silhouette scores para cluster i

            cluster_silhouette_vals = silhouette_vals[labels == i]

            cluster_silhouette_vals.sort()

            

            size_cluster_i = cluster_silhouette_vals.shape[0]

            y_upper = y_lower + size_cluster_i

            

            color = colors[i]

            ax.fill_betweenx(np.arange(y_lower, y_upper),

                            0, cluster_silhouette_vals,

                            facecolor=color, edgecolor=color, alpha=0.7)

            

            # Label do cluster

            ax.text(-0.05, y_lower + 0.5 * size_cluster_i, str(i))

            y_lower = y_upper + 10

        

        ax.axvline(x=silhouette_avg, color="red", linestyle="--", 

                  label=f'Silhouette Score Médio: {silhouette_avg:.3f}')

        ax.set_xlabel('Silhouette Score')

        ax.set_ylabel('Cluster')

        ax.set_title(f'Silhouette Plot Detalhado (k={k})')

        ax.legend()

        ax.grid(True, alpha=0.3)

        

        plt.tight_layout()

        

        # Salvar gráfico

        silhouette_path = self.output_dir / 'detailed_silhouette_plot.png'

        plt.savefig(silhouette_path, dpi=300, bbox_inches='tight')

        print(f"✓ Silhouette plot detalhado salvo em: {silhouette_path}")

        

        plt.show()

        

        return silhouette_avg

    

    def create_pca_scatter_plot(self, X_scaled, labels, features):

        """Cria scatter plot 2D com PCA colorido pelos clusters."""

        print(f"\n=== CRIANDO SCATTER PLOT COM PCA ===")

        

        # Aplicar PCA

        pca = PCA(n_components=2)

        X_pca = pca.fit_transform(X_scaled)

        

        # Criar scatter plot

        plt.figure(figsize=(10, 8))

        scatter = plt.scatter(X_pca[:, 0], X_pca[:, 1], c=labels, cmap='viridis', alpha=0.7, s=50)

        

        plt.xlabel(f'PC1 ({pca.explained_variance_ratio_[0]:.1%} da variância)')

        plt.ylabel(f'PC2 ({pca.explained_variance_ratio_[1]:.1%} da variância)')

        plt.title('Clusters em 2D (PCA)')

        plt.colorbar(scatter, label='Cluster')

        plt.grid(True, alpha=0.3)

        

        # Adicionar informações sobre variância explicada

        total_variance = pca.explained_variance_ratio_.sum()

        plt.figtext(0.02, 0.02, f'Variância total explicada: {total_variance:.1%}', 

                   fontsize=10, bbox=dict(boxstyle="round,pad=0.3", facecolor="lightgray"))

        

        plt.tight_layout()

        

        # Salvar gráfico

        pca_path = self.output_dir / 'pca_scatter_plot.png'

        plt.savefig(pca_path, dpi=300, bbox_inches='tight')

        print(f"✓ Scatter plot PCA salvo em: {pca_path}")

        

        plt.show()

        

        return X_pca, pca.explained_variance_ratio_

    

    def create_centroids_heatmap(self, X_scaled, labels, features):

        """Cria heatmap dos centróides em z-score."""

        print(f"\n=== CRIANDO HEATMAP DOS CENTRÓIDES ===")

        

        # Calcular centróides

        centroids = []

        for i in range(len(np.unique(labels))):

            cluster_data = X_scaled[labels == i]

            centroid = cluster_data.mean(axis=0)

            centroids.append(centroid)

        

        centroids = np.array(centroids)

        

        # Criar DataFrame para heatmap

        centroids_df = pd.DataFrame(centroids, 

                                  index=[f'Cluster {i}' for i in range(len(centroids))],

                                  columns=features)

        

        # Criar heatmap

        plt.figure(figsize=(8, 6))

        sns.heatmap(centroids_df, annot=True, cmap='RdBu_r', center=0, 

                   fmt='.2f', cbar_kws={'label': 'Z-Score'})

        plt.title('Heatmap dos Centróides (Z-Score)')

        plt.xlabel('Variáveis')

        plt.ylabel('Clusters')

        plt.tight_layout()

        

        # Salvar gráfico

        heatmap_path = self.output_dir / 'centroids_heatmap.png'

        plt.savefig(heatmap_path, dpi=300, bbox_inches='tight')

        print(f"✓ Heatmap dos centróides salvo em: {heatmap_path}")

        

        plt.show()

        

        return centroids_df

    

    def create_cluster_size_bar_chart(self, labels):

        """Cria bar chart com tamanho dos clusters."""

        print(f"\n=== CRIANDO BAR CHART DOS TAMANHOS DOS CLUSTERS ===")

        

        # Contar tamanhos dos clusters

        cluster_counts = pd.Series(labels).value_counts().sort_index()

        

        # Criar bar chart

        plt.figure(figsize=(10, 6))

        bars = plt.bar(cluster_counts.index, cluster_counts.values, 

                      color=plt.cm.viridis(np.linspace(0, 1, len(cluster_counts))))

        

        plt.xlabel('Cluster')

        plt.ylabel('Número de Registros')

        plt.title('Tamanho dos Clusters')

        plt.grid(True, alpha=0.3, axis='y')

        

        # Adicionar valores nas barras

        for bar in bars:

            height = bar.get_height()

            plt.text(bar.get_x() + bar.get_width()/2., height,

                    f'{int(height)}', ha='center', va='bottom')

        

        plt.tight_layout()

        

        # Salvar gráfico

        bar_path = self.output_dir / 'cluster_sizes_bar_chart.png'

        plt.savefig(bar_path, dpi=300, bbox_inches='tight')

        print(f"✓ Bar chart dos tamanhos salvo em: {bar_path}")

        

        plt.show()

        

        return cluster_counts

    

    def create_boxplots_by_cluster(self, X_scaled, labels, features):

        """Cria boxplots por variável × cluster."""

        print(f"\n=== CRIANDO BOXPLOTS POR CLUSTER ===")

        

        # Criar DataFrame para boxplots

        df_plot = pd.DataFrame(X_scaled, columns=features)

        df_plot['cluster'] = labels

        

        # Criar figura com subplots

        n_features = len(features)

        fig, axes = plt.subplots(1, n_features, figsize=(6*n_features, 6))

        

        if n_features == 1:

            axes = [axes]

        

        for i, feature in enumerate(features):

            sns.boxplot(data=df_plot, x='cluster', y=feature, ax=axes[i])

            axes[i].set_title(f'{feature} por Cluster')

            axes[i].grid(True, alpha=0.3)

        

        plt.tight_layout()

        

        # Salvar gráfico

        boxplot_path = self.output_dir / 'boxplots_by_cluster.png'

        plt.savefig(boxplot_path, dpi=300, bbox_inches='tight')

        print(f"✓ Boxplots por cluster salvos em: {boxplot_path}")

        

        plt.show()

    

    def create_centroids_dendrogram(self, centroids):

        """Cria dendrograma dos centróides (hierárquico sobre centróides do k-means)."""

        print(f"\n=== CRIANDO DENDOGRAMA DOS CENTRÓIDES ===")

        

        # Calcular linkage matrix dos centróides

        linkage_matrix = linkage(centroids, method='ward')

        

        # Criar dendrograma

        plt.figure(figsize=(10, 6))

        dendrogram(linkage_matrix, 

                  labels=[f'Cluster {i}' for i in range(len(centroids))],

                  leaf_rotation=90,

                  leaf_font_size=12)

        

        plt.title('Dendrograma dos Centróides (Hierárquico sobre K-means)')

        plt.xlabel('Clusters')

        plt.ylabel('Distância')

        plt.grid(True, alpha=0.3)

        

        plt.tight_layout()

        

        # Salvar gráfico

        dendro_path = self.output_dir / 'centroids_dendrogram.png'

        plt.savefig(dendro_path, dpi=300, bbox_inches='tight')

        print(f"✓ Dendrograma dos centróides salvo em: {dendro_path}")

        

        plt.show()

    

    def save_clustering_results(self, k, inertias, silhouette_scores, optimal_k, 

                              silhouette_avg, centroids_df, cluster_counts, 

                              pca_variance_ratio, features):

        """Salva resultados dos cálculos em arquivo txt."""

        print(f"\n=== SALVANDO RESULTADOS DOS CÁLCULOS ===")

        

        results_path = self.output_dir / 'clustering_results.txt'

        

        with open(results_path, 'w', encoding='utf-8') as f:

            f.write("=== RESULTADOS DA CLUSTERIZAÇÃO ===\n\n")

            

            f.write(f"Data: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

            f.write(f"Dataset: {self.data_path}\n")

            f.write(f"Variáveis utilizadas: {', '.join(features)}\n\n")

            

            f.write("=== ANÁLISE DE K ÓTIMO ===\n")

            f.write("k\tInércia\tSilhouette\n")

            f.write("-" * 30 + "\n")

            for i, (inertia, sil) in enumerate(zip(inertias, silhouette_scores)):

                f.write(f"{i+2}\t{inertia:.2f}\t{sil:.3f}\n")

            

            f.write(f"\nK ótimo selecionado: {optimal_k}\n")

            f.write(f"Silhouette score médio: {silhouette_avg:.3f}\n\n")

            

            f.write("=== CENTRÓIDES (Z-SCORE) ===\n")

            f.write(centroids_df.to_string())

            f.write("\n\n")

            

            f.write("=== DISTRIBUIÇÃO DOS CLUSTERS ===\n")

            f.write("Cluster\tTamanho\tPercentual\n")

            f.write("-" * 35 + "\n")

            total = cluster_counts.sum()

            for cluster, count in cluster_counts.items():

                percent = (count / total) * 100

                f.write(f"{cluster}\t{count}\t{percent:.1f}%\n")

            

            f.write(f"\nTotal de registros: {total}\n\n")

            

            f.write("=== PCA - VARIÂNCIA EXPLICADA ===\n")

            f.write(f"PC1: {pca_variance_ratio[0]:.1%}\n")

            f.write(f"PC2: {pca_variance_ratio[1]:.1%}\n")

            f.write(f"Total: {pca_variance_ratio.sum():.1%}\n\n")

            

            f.write("=== INTERPRETAÇÃO DOS CLUSTERS ===\n")

            f.write("Baseado nos centróides em z-score:\n")

            for i, row in centroids_df.iterrows():

                f.write(f"\n{row.name}:\n")

                for var, value in row.items():

                    if value > 0.5:

                        f.write(f"  - {var}: Alto (z={value:.2f})\n")

                    elif value < -0.5:

                        f.write(f"  - {var}: Baixo (z={value:.2f})\n")

        else:

                        f.write(f"  - {var}: Médio (z={value:.2f})\n")

        

        print(f"✓ Resultados salvos em: {results_path}")

    

    def perform_clustering(self, X_scaled, k, valid_indices):

        """Executa clusterização final."""

        print(f"\n=== CLUSTERIZAÇÃO FINAL (k={k}) ===")

        

        kmeans = KMeans(n_clusters=k, random_state=42, n_init=50)

        labels = kmeans.fit_predict(X_scaled)

        

        # Adicionar labels ao dataset original

        self.df_processed = self.df.copy()

        self.df_processed['cluster'] = np.nan

        self.df_processed.loc[valid_indices, 'cluster'] = labels

        

        # Calcular métricas finais

        silhouette = silhouette_score(X_scaled, labels)

        calinski = calinski_harabasz_score(X_scaled, labels)

        davies_bouldin = davies_bouldin_score(X_scaled, labels)

        

        print(f"✓ Clusterização concluída")

        print(f"  - Silhouette: {silhouette:.3f}")

        print(f"  - Calinski-Harabasz: {calinski:.1f}")

        print(f"  - Davies-Bouldin: {davies_bouldin:.3f}")

        

        # Distribuição dos clusters

        cluster_counts = pd.Series(labels).value_counts().sort_index()

        print(f"  - Distribuição dos clusters: {dict(cluster_counts)}")

        

        return labels



    def save_cluster_csvs(self):

        """Salva CSVs individuais por cluster."""

        print(f"\n=== SALVANDO CSVs POR CLUSTER ===")

        

        if 'cluster' not in self.df_processed.columns:

            raise ValueError("Coluna 'cluster' não encontrada. Execute clusterização primeiro.")

        

        clusters = sorted(self.df_processed['cluster'].unique())

        

        for cluster_id in clusters:

            cluster_data = self.df_processed[self.df_processed['cluster'] == cluster_id]

            filename = f"cluster_{cluster_id}.csv"

            filepath = self.output_dir / filename

            

            cluster_data.to_csv(filepath, index=False, encoding='utf-8')

            print(f"  Cluster {cluster_id}: {len(cluster_data)} registros -> {filepath}")

        

        # Salvar dataset completo com clusters

        full_path = self.output_dir / "df_final_with_clusters.csv"

        self.df_processed.to_csv(full_path, index=False, encoding='utf-8')

        print(f"  Dataset completo: {len(self.df_processed)} registros -> {full_path}")

        

        print(f"\n✓ Todos os CSVs salvos em: {self.output_dir}")

    

    def run(self):

        """Executa pipeline completo."""

        print("=== INICIANDO PIPELINE DE CLUSTERIZAÇÃO V2 ===")

        

        # Preparar dados

        X_scaled, valid_indices = self.prepare_data()

        features = ['ln_Value_Num', 'pos_rnc']

        

        # Criar gráficos de análise de k

        k_range, inertias, silhouette_scores = self.create_elbow_and_silhouette_plots(X_scaled, max_k=12)

        

        # Encontrar k ótimo

        optimal_k = self.find_optimal_k(X_scaled)

        

        # Executar clusterização

        labels = self.perform_clustering(X_scaled, optimal_k, valid_indices)

        

        # Criar visualizações detalhadas

        silhouette_avg = self.create_detailed_silhouette_plot(X_scaled, labels, optimal_k)

        

        # Scatter plot com PCA

        X_pca, pca_variance_ratio = self.create_pca_scatter_plot(X_scaled, labels, features)

        

        # Heatmap dos centróides

        centroids_df = self.create_centroids_heatmap(X_scaled, labels, features)

        

        # Bar chart dos tamanhos

        cluster_counts = self.create_cluster_size_bar_chart(labels)

        

        # Boxplots por cluster

        self.create_boxplots_by_cluster(X_scaled, labels, features)

        

        # Dendrograma dos centróides

        centroids = centroids_df.values

        self.create_centroids_dendrogram(centroids)

        

        # Salvar resultados em txt

        self.save_clustering_results(k_range, inertias, silhouette_scores, optimal_k, 

                                   silhouette_avg, centroids_df, cluster_counts, 

                                   pca_variance_ratio, features)

        

        # Salvar CSVs

        self.save_cluster_csvs()

        

        print("\n=== PIPELINE CONCLUÍDO ===")

        return self.df_processed



def main():

    """Função principal."""

    data_path = r"C:\Users\IGOR\Desktop\UFSC\TCC\dados\clubes\outcome\df_final.csv"

    

    print(f"Starting cluster pipeline with data: {data_path}")

    pipeline = ClusteringPipelineV2(data_path)

    result = pipeline.run()



    print(f"Pipeline completed. Result shape: {result.shape}")

    return result



if __name__ == "__main__":

    result = main()