import pandas as pd
import os

file_path = "files/uploads/SP500_2025-07-18.xlsx"

try:
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
    else:
        df = pd.read_excel(file_path)
        print(f"File: {file_path}")
        print(f"Shape: {df.shape}")
        print("\nColumns:")
        print(df.columns.tolist())
        print("\nFirst 5 rows:")
        print(df.head().to_string())
        print("\nData Types:")
        print(df.dtypes)
except Exception as e:
    print(f"Error reading file: {e}")
