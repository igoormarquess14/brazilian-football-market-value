import pandas as pd
import os

SRC = r"C:\Users\IGOR\Desktop\UFSC\TCC\dados\df_final.csv"
DST = r"C:\Users\IGOR\Desktop\UFSC\TCC\dados\df_final_no_na.csv"


def main():
    if not os.path.exists(SRC):
        print(f"Arquivo não encontrado: {SRC}")
        return
    df = pd.read_csv(SRC)
    before = len(df)
    df_clean = df.dropna().copy()
    after = len(df_clean)
    removed = before - after
    df_clean.to_csv(DST, index=False)
    print(f"Linhas originais: {before}")
    print(f"Linhas após dropna: {after}")
    print(f"Removidas: {removed}")
    print(f"Salvo em: {DST}")


if __name__ == "__main__":
    main()


