import os
import datetime
from unittest.mock import MagicMock, patch
from price_reversal_core.news_fetcher import save_news_summary

@patch('price_reversal_core.news_fetcher.NewsApiClient')
def test_news_saver(mock_newsapi):
    print("Starting news saver verification...")
    
    # Mock NewsAPI
    mock_client = MagicMock()
    mock_client.get_everything.return_value = {
        'status': 'ok',
        'articles': [
            {
                'title': 'Test Article',
                'source': {'name': 'Test Source'},
                'publishedAt': '2025-11-28T10:00:00Z',
                'url': 'http://test.com'
            }
        ]
    }
    mock_newsapi.return_value = mock_client
    
    # Dummy data
    companies = [{'Ticker': 'TEST', 'Company Name': 'Test Corp'}]
    
    # Run saver
    # We need to mock env var if not present, but let's assume it handles missing key gracefully or we patch os.environ
    with patch.dict(os.environ, {'NEWSAPI_KEY': 'dummy_key'}):
        file_path = save_news_summary(companies)
    
    print(f"File saved to: {file_path}")
    
    # Verify file existence and name
    expected_date = datetime.datetime.now().strftime('%Y-%m-%d')
    expected_filename = f"NewsSummary-{expected_date}.txt"
    
    if os.path.basename(file_path) == expected_filename and os.path.exists(file_path):
        print("SUCCESS: File created with correct name.")
        
        with open(file_path, 'r') as f:
            content = f.read()
            print("File Content Preview:")
            print(content[:200])
            
            if "Test Article" in content:
                print("SUCCESS: Content contains expected article.")
            else:
                print("FAILURE: Content missing expected article.")
    else:
        print(f"FAILURE: File not found or incorrect name. Expected {expected_filename}, got {os.path.basename(file_path)}")

if __name__ == "__main__":
    test_news_saver()
