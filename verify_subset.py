import pandas as pd
from price_reversal_core.subsets import get_subset
import datetime

def test_date_filtering():
    # Create dummy data with mixed dates
    data = {
        'Ticker': ['A', 'B', 'C', 'D'],
        'Reversal Date': [
            '2025-07-18', 
            '2025-07-17', 
            '2025-07-18', 
            '2025-07-10'
        ],
        'Expected Magnitude %': [5.0, 3.0, 2.0, 10.0]
    }
    df = pd.DataFrame(data)
    
    print("Original DataFrame:")
    print(df)
    
    # Test filtering
    subset = get_subset(df)
    
    print("\nFiltered Subset (Latest Date):")
    print(subset)
    
    # Verification
    expected_date = pd.to_datetime('2025-07-18')
    assert len(subset) == 2
    assert all(subset['Reversal Date'] == expected_date)
    print("\nSUCCESS: Filtered correctly for latest date.")

if __name__ == "__main__":
    test_date_filtering()
