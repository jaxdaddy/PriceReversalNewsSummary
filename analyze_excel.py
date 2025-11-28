import pandas as pd
import os

file_path = "files/uploads/test_data.xlsx"

try:
    df = pd.read_excel(file_path)
    print("Columns found:")
    for col in df.columns:
        print(f"- {col}")
except Exception as e:
    print(f"Error reading file: {e}")
