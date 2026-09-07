from pathlib import Path
# processes the 'Ex Club' column, extracting:
# 1. Club name
# 2. Transfer type (transfer, loan, after_loan)
# 3. Transfer fee (numeric value or text)
import pandas as pd
import re

PROJECT_ROOT = Path(__file__).resolve().parents[2]

def processar_ex_club():
    """
    Processes the 'Ex Club' column, extracting:
    1. Club name
    2. Transfer type (transfer, loan, after_loan)
    3. Transfer fee (numeric value or text)
    """

    # File path
    arquivo_entrada = str(PROJECT_ROOT / "dados" / "clubes" / "outcome" / "todos_clubes_2025_processado.csv")
    arquivo_saida = str(PROJECT_ROOT / "dados" / "clubes" / "outcome" / "todos_clubes_2025_final.csv")

    print("Loading CSV file...")
    df = pd.read_csv(arquivo_entrada)

    print(f"File loaded with {len(df)} rows and {len(df.columns)} columns")

    def extrair_informacoes_ex_club(ex_club_str):
        if pd.isna(ex_club_str) or ex_club_str == '':
            return '', '', ''

        ex_club_str = str(ex_club_str)

        # 1. Extract club name (before the colon)
        clube = ''
        if ':' in ex_club_str:
            clube = ex_club_str.split(':')[0].strip()

        # 2. Identify transfer type
        # (the strings below are matched verbatim against the scraped
        # Transfermarkt page text — do not translate them)
        transferencia = ''
        if 'Ablöse' in ex_club_str:
            transferencia = 'transfer'
        elif 'Reforço contratado do' in ex_club_str:
            transferencia = 'transfer'
        elif 'Emprestado do' in ex_club_str:
            transferencia = 'loan'
        elif 'Regresso após empréstimo' in ex_club_str:
            transferencia = 'after_loan'

        # 3. Extract transfer fee
        taxa = ''

        # Look for monetary values (€ X.XX mi, € X mil, etc.)
        valor_match = re.search(r'€\s*([\d,]+(?:\.[\d]+)?)\s*(mi|mil)', ex_club_str)
        if valor_match:
            valor = valor_match.group(1).replace(',', '.')
            unidade = valor_match.group(2)

            if unidade == 'mi':
                taxa = str(int(float(valor) * 1000000))
            elif unidade == 'mil':
                taxa = str(int(float(valor) * 1000))
        else:
            # Look for other information (again, matched verbatim
            # against the scraped page text)
            if 'custo zero' in ex_club_str:
                taxa = '0'
            elif '-' in ex_club_str and '€' not in ex_club_str:
                taxa = '-'
            elif '?' in ex_club_str:
                taxa = '?'

        return clube, transferencia, taxa

    print("\nProcessing 'Ex Club' column...")

    # Apply the function to extract the information
    df[['Ex_Club_Limpo', 'Transferencia', 'Taxa_Transferencia']] = df['Ex Club'].apply(
        lambda x: pd.Series(extrair_informacoes_ex_club(x))
    )

    # Reorder columns
    colunas_finais = [
        'Clube', 'Player', 'nasc', 'age', 'Position', 'Position_Num',
        'Height', 'Nation', 'Ex_Club_Limpo', 'Transferencia', 'Taxa_Transferencia',
        'Ex Club', 'Value (€)', 'Value_Num'
    ]

    df_final = df[colunas_finais]

    # Save the processed file
    print(f"\nSaving final file: {arquivo_saida}")
    df_final.to_csv(arquivo_saida, index=False, encoding='utf-8')

    print(f"\nProcessing complete!")
    print(f"File saved with {len(df_final)} rows and {len(df_final.columns)} columns")

    # Show stats
    print(f"\nStats:")
    print(f"- Clubs extracted: {df_final['Ex_Club_Limpo'].notna().sum()}")
    print(f"- Transfer types identified:")
    print(df_final['Transferencia'].value_counts())
    print(f"\n- Transfer fees:")
    print(df_final['Taxa_Transferencia'].value_counts().head(10))

    # Show a few sample rows
    print(f"\nFirst 5 rows of the processed file:")
    print(df_final[['Player', 'Ex_Club_Limpo', 'Transferencia', 'Taxa_Transferencia']].head())
    
    return df_final

if __name__ == "__main__":
    df_resultado = processar_ex_club()
