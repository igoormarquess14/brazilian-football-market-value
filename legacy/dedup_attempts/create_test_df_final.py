import pandas as pd
import numpy as np

# Read the base CSV
df = pd.read_csv(r"C:\Users\IGOR\Desktop\UFSC\TCC\dados\clubes\outcome\final_merged_filtrado_dummies_clean.csv")

# Create simulated pos_rnc and pts_rnc for testing
# pos_rnc: 1-20 (simulating league positions)
# pts_rnc: correlated with position (higher position = more points)
np.random.seed(42)

# Get unique clubs
clubs = df['Clube'].unique()
n_clubs = len(clubs)

# Create position mapping (1 to n_clubs)
pos_mapping = {club: i+1 for i, club in enumerate(clubs)}
pts_mapping = {club: max(0, 20000 - (i+1)*500 + np.random.randint(-1000, 1000)) 
               for i, club in enumerate(clubs)}

# Add the new columns
df['pos_rnc'] = df['Clube'].map(pos_mapping)
df['pts_rnc'] = df['Clube'].map(pts_mapping)

# Save as df_final.csv
output_path = r"C:\Users\IGOR\Desktop\UFSC\TCC\dados\clubes\outcome\df_final.csv"
df.to_csv(output_path, index=False, encoding='utf-8')

print(f"Created df_final.csv with {len(df)} rows and {len(df.columns)} columns")
print(f"pos_rnc range: {df['pos_rnc'].min()} - {df['pos_rnc'].max()}")
print(f"pts_rnc range: {df['pts_rnc'].min()} - {df['pts_rnc'].max()}")
print(f"Unique clubs: {len(clubs)}")
