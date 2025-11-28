import pandas as pd
import os


def load_excel(file_path: str) -> pd.DataFrame:
    """Load an Excel file into a pandas DataFrame and report progress."""
    print(f"Loading Excel file: {file_path}")
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")
    try:
        df = pd.read_excel(file_path)
        print(f"Loaded {len(df)} rows and columns: {list(df.columns)}")
        # missing_cols = [col for col in required_columns if col not in df.columns]
        # if missing_cols:
        #     raise ValueError(f"Missing columns: {missing_cols}")
        return df
    except Exception as e:
        raise ValueError(f"Error reading Excel file: {str(e)}")

