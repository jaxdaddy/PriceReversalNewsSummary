import os
import pandas as pd
from unittest.mock import MagicMock, patch
import sys

# Add project root to path
sys.path.append(os.getcwd())
print(f"Python executable: {sys.executable}")
print(f"Sys path: {sys.path}")
try:
    import fastapi
    print(f"FastAPI found at: {fastapi.__file__}")
except ImportError as e:
    print(f"FastAPI import failed: {e}")

from apps.api.main import run_analysis

# Mock data
def create_dummy_excel():
    df = pd.DataFrame({
        'Ticker': ['AAPL', 'MSFT'],
        'Company Name': ['Apple Inc.', 'Microsoft Corporation'],
        '% Change': [-5.0, 2.0]
    })
    os.makedirs("files/uploads", exist_ok=True)
    file_path = "files/uploads/test_data.xlsx"
    df.to_excel(file_path, index=False)
    return file_path

@patch('price_reversal_core.llm_normalizer.os.getenv')
@patch('price_reversal_core.llm_normalizer.openai.OpenAI')
@patch('price_reversal_core.news_fetcher.NewsApiClient')
@patch('price_reversal_core.report_generator.genai')
async def test_pipeline(mock_genai_report, mock_newsapi, mock_openai_class, mock_getenv):
    print("Starting pipeline verification...")
    
    # Setup mocks
    # 0. Environment Mock
    mock_getenv.return_value = "dummy_api_key"

    # 1. LLM Normalizer Mock
    mock_openai_client = MagicMock()
    mock_openai_client.chat.completions.create.return_value.choices[0].message.content = '''
    [
        {"Ticker": "AAPL", "SearchQuery": "Apple"},
        {"Ticker": "MSFT", "SearchQuery": "Microsoft"}
    ]
    '''
    mock_openai_class.return_value = mock_openai_client
    
    # 2. NewsAPI Mock
    mock_news_client = MagicMock()
    mock_news_client.get_everything.return_value = {
        'status': 'ok',
        'articles': [
            {
                'title': 'Apple Stock Falls',
                'source': {'name': 'TechCrunch'},
                'publishedAt': '2023-10-27T10:00:00Z',
                'url': 'http://example.com'
            }
        ]
    }
    mock_newsapi.return_value = mock_news_client
    
    # 3. Report Generator Mock
    mock_model_report = MagicMock()
    mock_model_report.generate_content.return_value.text = "# Price Reversal Report\n\nAAPL shows signs of reversal..."
    mock_genai_report.GenerativeModel.return_value = mock_model_report
    
    # Run pipeline
    file_path = create_dummy_excel()
    result = await run_analysis(mode="default", file_path=file_path)
    
    print("Pipeline result:", result)
    
    if result['status'] == 'completed' and os.path.exists(result['report_path']):
        print("Verification SUCCESS: Report generated.")
    else:
        print("Verification FAILED.")

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_pipeline())
