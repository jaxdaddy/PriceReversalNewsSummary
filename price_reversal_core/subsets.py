import pandas as pd

def get_subset(df: pd.DataFrame, mode: str = "default", limit_companies: int = None) -> pd.DataFrame:
    """
    Selects a subset of the dataframe based on the mode.
    Default behavior: Filter for records with the latest 'Reversal Date'.
    If limit_companies is specified, returns only that many companies.
    """
    if df.empty:
        print("Dataframe is empty. No records to process.")
        return df

    # Ensure Reversal Date is datetime
    if 'Reversal Date' in df.columns:
        df['Reversal Date'] = pd.to_datetime(df['Reversal Date'])
        latest_date = df['Reversal Date'].max()
        print(f"Filtering for latest Reversal Date: {latest_date}")
        df = df[df['Reversal Date'] == latest_date]
        print(f"Selected {len(df)} records after date filter.")
        # Show a preview of the subset
        print("Subset preview:")
        print(df.head().to_string(index=False))
    else:
        print("'Reversal Date' column not found. Skipping date filter.")

    if mode == "big_movers":
        # Example: Filter by % Change if column exists (using Expected Magnitude % as proxy based on file analysis)
        if 'Expected Magnitude %' in df.columns:
            df = df.sort_values(by='Expected Magnitude %', ascending=False).head(10)
    
    # Apply limit if specified
    if limit_companies is not None and len(df) > limit_companies:
        df = df.head(limit_companies)
        print(f"Limited to {limit_companies} companies.")

    # Select only the required columns
    required_columns = [
        'Symbol', 
        'Company Name', 
        'Reversal Date', 
        'Reversal Price', 
        'HR1 Value', 
        'Last Close Price'
    ]
    
    # Filter out columns that do not exist in the DataFrame
    existing_columns = [col for col in required_columns if col in df.columns]
    df = df[existing_columns]
    
    return df
