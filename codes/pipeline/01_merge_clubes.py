from pathlib import Path
# merges all club CSVs into a single file
# works
import pandas as pd
import os
import glob

PROJECT_ROOT = Path(__file__).resolve().parents[2]

def juntar_csvs_clubes():
    """
    Merges all CSVs from the clubs folder into a single file,
    adding a 'Clube' column to identify the origin of each row.
    """

    # Path to the folder with the CSVs
    pasta_csvs = str(PROJECT_ROOT / "dados" / "clubes")

    # List to hold the DataFrames
    dataframes = []

    # Get all CSV files in the folder
    arquivos_csv = glob.glob(os.path.join(pasta_csvs, "*.csv"))

    print(f"Found {len(arquivos_csv)} CSV files:")

    for arquivo in arquivos_csv:
        # Extract the club name from the file name
        nome_arquivo = os.path.basename(arquivo)
        nome_clube = nome_arquivo.replace("_2024.csv", "").replace("_2024_table_only.csv", "")

        print(f"Processing: {nome_arquivo} -> Club: {nome_clube}")

        try:
            # Read the CSV
            df = pd.read_csv(arquivo)

            # Add the club-name column
            df['Clube'] = nome_clube

            # Add to the list
            dataframes.append(df)

        except Exception as e:
            print(f"Error processing {arquivo}: {e}")

    if not dataframes:
        print("No CSV file was processed successfully!")
        return

    # Concatenate all DataFrames
    print("\nConcatenating all DataFrames...")
    df_final = pd.concat(dataframes, ignore_index=True)

    # Reorder columns to put 'Clube' first
    colunas = ['Clube'] + [col for col in df_final.columns if col != 'Clube']
    df_final = df_final[colunas]

    # Save the final file
    pasta_saida = PROJECT_ROOT / "dados" / "clubes" / "outcome"
    pasta_saida.mkdir(parents=True, exist_ok=True)
    arquivo_saida = str(pasta_saida / "todos_clubes_2024.csv")
    df_final.to_csv(arquivo_saida, index=False, encoding='utf-8')

    print(f"\nFinal file saved as: {arquivo_saida}")
    print(f"Total rows: {len(df_final)}")
    print(f"Total columns: {len(df_final.columns)}")
    print(f"Columns: {list(df_final.columns)}")

    # Show per-club stats
    print("\nStats per club:")
    print(df_final['Clube'].value_counts().sort_index())

    return df_final

if __name__ == "__main__":
    df_resultado = juntar_csvs_clubes()
