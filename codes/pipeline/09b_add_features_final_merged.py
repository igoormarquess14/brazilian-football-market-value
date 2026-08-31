from pathlib import Path
# computes age_sq and ln_Value_Num for final_merged_filtrado_dummies_clean.csv
import os
import math
import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]

PATH_IN = str(PROJECT_ROOT / "dados" / "clubes" / "outcome" / "final_merged_filtrado_dummies_clean.csv")
OUT_PATH = PATH_IN  # overwrite original

# Read CSV
df = pd.read_csv(PATH_IN, encoding="utf-8")

# Ensure numeric
df["age_num"] = pd.to_numeric(df.get("age"), errors="coerce")
df["value_num_num"] = pd.to_numeric(df.get("Value_Num"), errors="coerce")

# Center age and create squared term
age_mean = df["age_num"].mean(skipna=True)
df["age_centered"] = df["age_num"] - age_mean
df["age_sq"] = df["age_centered"] ** 2

# Natural log of Value_Num (NaN for non-positive)
with np.errstate(divide='ignore', invalid='ignore'):
    df["ln_Value_Num"] = np.where(df["value_num_num"] > 0, np.log(df["value_num_num"]), np.nan)

# Drop helper numeric columns, keep original 'age' and 'Value_Num'
df.drop(columns=["age_num", "value_num_num"], inplace=True)

# Save (overwrite original)
df.to_csv(OUT_PATH, index=False, encoding="utf-8")
print(f"Overwrote file: {OUT_PATH}")
print(f"age mean used for centering: {age_mean:.6f}")
