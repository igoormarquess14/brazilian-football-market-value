#!/usr/bin/env python3
r"""
Divide o CSV em dois arquivos: um com linhas contendo missing values e outro limpo (sem missing),
para uso na modelagem.

Entrada:  C:\\Users\\IGOR\\Desktop\\UFSC\\TCC\\dados\\clubes\\outcome\\final_merged_filtrado_dummies.csv
Saídas:   - final_merged_filtrado_dummies_only_missing.csv (apenas linhas com algum missing)
          - final_merged_filtrado_dummies_clean.csv        (linhas completas, sem missing)
"""

import pandas as pd
import numpy as np
from pathlib import Path


def main():
    input_path = Path(r"C:\Users\IGOR\Desktop\UFSC\TCC\dados\clubes\outcome\final_merged_filtrado_dummies.csv")
    if not input_path.exists():
        print(f"ERRO: Arquivo não encontrado: {input_path}")
        return

    out_dir = input_path.parent
    missing_out = out_dir / "final_merged_filtrado_dummies_only_missing.csv"
    clean_out = out_dir / "final_merged_filtrado_dummies_clean.csv"

    # Carregar
    df = pd.read_csv(input_path)

    # Normalizar marcadores de missing comuns para NaN
    df = df.replace({"?": np.nan, "-": np.nan, "": np.nan})

    # Identificar linhas com qualquer missing
    has_missing_mask = df.isna().any(axis=1)

    df_missing = df.loc[has_missing_mask].copy()
    df_clean = df.loc[~has_missing_mask].copy()

    # Salvar
    df_missing.to_csv(missing_out, index=False)
    df_clean.to_csv(clean_out, index=False)

    # Relatório
    total = len(df)
    n_missing = len(df_missing)
    n_clean = len(df_clean)
    print("Divisão concluída.")
    print(f"Total de linhas:   {total}")
    print(f"Com missing:       {n_missing} -> {missing_out}")
    print(f"Sem missing:       {n_clean} -> {clean_out}")


if __name__ == "__main__":
    main()


