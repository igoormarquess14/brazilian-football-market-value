from pathlib import Path
# processes the clubs CSV, applying the following transformations:
# 1. Splits the Age column into 'nasc' (date of birth) and 'age' (age)
# 2. Creates a mapping from positions to numbers
# 3. Cleans the Height column (removes 'm', swaps comma for dot)
# 4. Converts monetary values to integers
import pandas as pd
import re

PROJECT_ROOT = Path(__file__).resolve().parents[2]

def processar_csv_clubes():
    """
    Processes the clubs CSV, applying the following transformations:
    1. Splits the Age column into 'nasc' (date of birth) and 'age' (age)
    2. Creates a mapping from positions to numbers
    3. Cleans the Height column (removes 'm', swaps comma for dot)
    4. Converts monetary values to integers
    """

    # File path
    arquivo_entrada = str(PROJECT_ROOT / "dados" / "clubes" / "outcome" / "todos_clubes_2024.csv")
    arquivo_saida = str(PROJECT_ROOT / "dados" / "clubes" / "outcome" / "todos_clubes_2024_processado.csv")

    print("Loading CSV file...")
    df = pd.read_csv(arquivo_entrada)

    print(f"File loaded with {len(df)} rows and {len(df.columns)} columns")

    # 1. Split Age column into 'nasc' and 'age'
    print("\n1. Splitting Age column into 'nasc' and 'age'...")

    def separar_idade(age_str):
        if pd.isna(age_str) or age_str == '':
            return '', ''

        # Pattern to capture date and age: DD/MM/YYYY (XX)
        match = re.match(r'(\d{2}/\d{2}/\d{4})\s*\((\d+)\)', str(age_str))
        if match:
            data_nasc = match.group(1)
            idade = match.group(2)
            return data_nasc, idade
        else:
            return '', ''

    # Apply the function and create the new columns
    df[['nasc', 'age']] = df['Age'].apply(lambda x: pd.Series(separar_idade(x)))

    # 2. Create position-to-number mapping
    print("\n2. Creating position mapping...")

    # Position mapping (based on Brazilian football; keys match the
    # Portuguese position labels as scraped — do not translate them)
    mapeamento_posicoes = {
        'Goleiro': 1,
        'Lateral Dir.': 2,
        'Lateral Esq.': 3,
        'Zagueiro': 4,
        'Volante': 5,
        'Meio-Campo': 6,
        'Meia-Atacante': 7,
        'Ponta Dir.': 8,
        'Ponta Esq.': 9,
        'Atacante': 10,
        'Centroavante': 11,
        'Segundo Atacante': 10,
        # Positions found in the file
        'Meia Central': 6,
        'Meia Ofensivo': 7,
        'Ponta Direita': 8,
        'Ponta Esquerda': 9,
        'Seg. Atacante': 10
    }
    
    # Create column with the position numbers
    df['Position_Num'] = df['Position'].map(mapeamento_posicoes)

    # Show the unique positions found
    posicoes_unicas = df['Position'].unique()
    print(f"Positions found: {sorted(posicoes_unicas)}")

    # 3. Clean Height column
    print("\n3. Cleaning Height column...")

    def limpar_altura(height_str):
        if pd.isna(height_str) or height_str == '':
            return ''

        # Remove 'm' and swap comma for dot
        altura_limpa = str(height_str).replace('m', '').replace(',', '.')
        return altura_limpa

    df['Height'] = df['Height'].apply(limpar_altura)

    # 4. Convert monetary values to integers
    print("\n4. Converting monetary values...")

    def converter_valor(valor_str):
        if pd.isna(valor_str) or valor_str == '' or valor_str == '-':
            return 0

        valor_str = str(valor_str)

        # Remove symbols and spaces
        valor_limpo = valor_str.replace('€', '').replace(' ', '').replace('.', '').replace(',', '')

        # Identify thousands, millions, or billions
        if 'mil' in valor_limpo.lower():
            # Remove 'mil' (thousand) and multiply by 1000
            numero = re.findall(r'[\d,]+', valor_limpo)
            if numero:
                return int(float(numero[0].replace(',', '.')) * 1000)
        elif 'mi' in valor_limpo.lower():
            # Remove 'mi' (million) and multiply by 1000000
            numero = re.findall(r'[\d,]+', valor_limpo)
            if numero:
                return int(float(numero[0].replace(',', '.')) * 1000000)
        elif 'bi' in valor_limpo.lower():
            # Remove 'bi' (billion) and multiply by 1000000000
            numero = re.findall(r'[\d,]+', valor_limpo)
            if numero:
                return int(float(numero[0].replace(',', '.')) * 1000000000)
        else:
            # Try to extract just the number
            numero = re.findall(r'[\d,]+', valor_limpo)
            if numero:
                return int(float(numero[0].replace(',', '.')))

        return 0

    df['Value_Num'] = df['Value (€)'].apply(converter_valor)

    # Reorder columns
    colunas_finais = [
        'Clube', 'Player', 'nasc', 'age', 'Position', 'Position_Num',
        'Height', 'Nation', 'Ex Club', 'Value (€)', 'Value_Num'
    ]

    df_final = df[colunas_finais]

    # Save the processed file
    print(f"\nSaving processed file: {arquivo_saida}")
    df_final.to_csv(arquivo_saida, index=False, encoding='utf-8')

    print(f"\nProcessing complete!")
    print(f"File saved with {len(df_final)} rows and {len(df_final.columns)} columns")

    # Show stats
    print(f"\nStats:")
    print(f"- Positions mapped: {df_final['Position_Num'].notna().sum()}")
    print(f"- Monetary values converted: {df_final['Value_Num'].sum():,}")
    print(f"- Heights processed: {df_final['Height'].notna().sum()}")

    # Show a few sample rows
    print(f"\nFirst 5 rows of the processed file:")
    print(df_final.head())
    
    return df_final

if __name__ == "__main__":
    df_resultado = processar_csv_clubes()
