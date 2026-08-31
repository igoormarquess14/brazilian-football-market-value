import pandas as pd
import os
import sys
from pathlib import Path

def format_number(value):
    """Formats numbers for LaTeX"""
    if pd.isna(value):
        return '--'
    try:
        if isinstance(value, (int, float)):
            # If it's a very large number, format with a thousands separator
            if abs(value) >= 1000:
                return f"{value:,.0f}".replace(',', '.')
            elif isinstance(value, float):
                # For decimals, show up to 2 places
                formatted = f"{value:.2f}".rstrip('0').rstrip('.')
                return formatted if formatted else '0'
            else:
                return str(value)
        return str(value)
    except Exception as e:
        print(f"Error formatting {value}: {e}", file=sys.stderr)
        return str(value)

def csv_to_latex(csv_path, output_path, caption, label):
    """Converts a CSV to a LaTeX table"""
    df = pd.read_csv(csv_path)

    # Drop the last row if it's empty
    df = df.dropna(how='all')

    # Escape LaTeX special characters
    def escape_latex(text):
        if pd.isna(text):
            return '--'
        text = str(text)
        text = text.replace('\\', '\\textbackslash{}')
        text = text.replace('&', '\\&')
        text = text.replace('%', '\\%')
        text = text.replace('$', '\\$')
        text = text.replace('#', '\\#')
        text = text.replace('^', '\\textasciicircum{}')
        text = text.replace('_', '\\_')
        text = text.replace('{', '\\{')
        text = text.replace('}', '\\}')
        text = text.replace('~', '\\textasciitilde{}')
        return text
    
    # Apply escaping to all cells
    for col in df.columns:
        df[col] = df[col].apply(lambda x: escape_latex(format_number(x)))

    # Build the LaTeX code
    latex_code = []
    latex_code.append("\\begin{longtable}{" + "l" * len(df.columns) + "}")
    latex_code.append("\\caption{" + caption + "}")
    latex_code.append("\\label{" + label + "}")
    latex_code.append("\\\\")
    latex_code.append("\\toprule")

    # Header
    header = " & ".join([escape_latex(col) for col in df.columns])
    latex_code.append(header + " \\\\")
    latex_code.append("\\midrule")
    latex_code.append("\\endfirsthead")

    # Header for continuation pages
    latex_code.append("\\multicolumn{" + str(len(df.columns)) + "}{c}{\\tablename\\ \\thetable\\ -- \\textit{Continued}} \\\\")
    latex_code.append("\\toprule")
    latex_code.append(header + " \\\\")
    latex_code.append("\\midrule")
    latex_code.append("\\endhead")

    # Footer
    latex_code.append("\\bottomrule")
    latex_code.append("\\endfoot")
    latex_code.append("\\bottomrule")
    latex_code.append("\\endlastfoot")

    # Data
    for _, row in df.iterrows():
        row_data = " & ".join([str(val) for val in row.values])
        latex_code.append(row_data + " \\\\")

    latex_code.append("\\end{longtable}")

    # Save the file
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(latex_code))

    print(f"LaTeX file created: {output_path}")
    print(f"Total rows: {len(df)}")
    print(f"Total columns: {len(df.columns)}")

# Paths
PROJECT_ROOT = Path(__file__).resolve().parents[2]
base_dir = str(PROJECT_ROOT / "dados")
output_dir = str(PROJECT_ROOT / "outputs")
Path(output_dir).mkdir(exist_ok=True)

try:
    # Convert df_mc.csv
    print("Converting df_mc.csv...")
    csv_to_latex(
        os.path.join(base_dir, "df_mc.csv"),
        os.path.join(output_dir, "df_mc.tex"),
        "Midfielder dataset, 2025 Brazilian Serie A",
        "tab:df_mc"
    )

    # Convert df_final.csv
    print("\nConverting df_final.csv...")
    csv_to_latex(
        os.path.join(base_dir, "df_final.csv"),
        os.path.join(output_dir, "df_final.tex"),
        "Full player dataset, 2025 Brazilian Serie A",
        "tab:df_final"
    )

    print("\nConversion complete!")
except Exception as e:
    print(f"Error: {e}", file=sys.stderr)
    import traceback
    traceback.print_exc()
    sys.exit(1)

