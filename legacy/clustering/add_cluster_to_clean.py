#!/usr/bin/env python3
"""
Adiciona a coluna 'cluster' gerada no artifacts_v2/df_out.csv ao dataset limpo
final_merged_filtrado_dummies_clean.csv, casando por 'Player' e 'Clube'.

Saída: final_merged_filtrado_dummies_clean_with_cluster_v2.csv
"""

import pandas as pd
from pathlib import Path


def main():
    clean_path = Path(r"C:\Users\IGOR\Desktop\UFSC\TCC\dados\clubes\outcome\final_merged_filtrado_dummies_clean.csv")
    clusters_path = Path(r"C:\Users\IGOR\Desktop\UFSC\TCC\codes\artifacts_v2\df_out.csv")
    out_path = clean_path.parent / "final_merged_filtrado_dummies_clean_with_cluster_v2.csv"

    if not clean_path.exists():
        print(f"ERRO: Nao encontrei o dataset limpo: {clean_path}")
        return
    if not clusters_path.exists():
        print(f"ERRO: Nao encontrei o df_out com clusters: {clusters_path}")
        return

    df_clean = pd.read_csv(clean_path)
    df_clusters = pd.read_csv(clusters_path)

    # Selecionar colunas de chave e cluster
    key_cols = [c for c in ['Player', 'Clube'] if c in df_clean.columns and c in df_clusters.columns]
    if not key_cols:
        print("ERRO: Nenhuma chave comum encontrada entre os arquivos (esperado: 'Player' e/ou 'Clube').")
        return

    cols_to_merge = key_cols + ['cluster']
    if 'cluster' not in df_clusters.columns:
        print("ERRO: Coluna 'cluster' nao encontrada no df_out.csv.")
        return

    merge_df = df_clusters[cols_to_merge].copy()

    # Remover duplicados no df_clusters pela chave
    merge_df = merge_df.drop_duplicates(subset=key_cols)

    # Merge left para manter todas as linhas do limpo
    df_final = df_clean.merge(merge_df, on=key_cols, how='left')

    # Relatorio basico
    matched = df_final['cluster'].notna().sum()
    total = len(df_final)
    print(f"Linhas com cluster associado: {matched}/{total} ({matched/total*100:.1f}%)")

    # Salvar
    df_final.to_csv(out_path, index=False)
    print(f"Arquivo salvo: {out_path}")


if __name__ == "__main__":
    main()



