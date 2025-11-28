import os
import sys
import asyncio
from unittest.mock import MagicMock, patch

# Add project root to path
sys.path.append(os.getcwd())

# Mock dependencies to avoid external calls and missing file errors
@patch('price_reversal_core.pdf_report_generator.genai')
@patch('price_reversal_core.news_fetcher.NewsApiClient')
@patch('price_reversal_core.llm_normalizer.genai')
@patch('price_reversal_core.pdf_report_generator.pypdf.PdfReader')
async def test_final_pipeline(mock_pdf_reader, mock_genai_norm, mock_newsapi, mock_genai_pdf):
    print("Starting final pipeline verification...")
    
    # Mock PDF Reader
    mock_page = MagicMock()
    mock_page.extract_text.return_value = "Mock PDF Content"
    mock_pdf_reader.return_value.pages = [mock_page]
    
    # Mock LLM Normalizer
    mock_model_norm = MagicMock()
    mock_model_norm.generate_content.return_value.text = '[{"Ticker": "AAPL", "SearchQuery": "Apple"}]'
    mock_genai_norm.GenerativeModel.return_value = mock_model_norm
    
    # Mock NewsAPI
    mock_news_client = MagicMock()
    mock_news_client.get_everything.return_value = {
        'status': 'ok',
        'articles': [{'title': 'Test', 'source': {'name': 'Src'}, 'publishedAt': '2025-01-01', 'url': 'url'}]
    }
    mock_newsapi.return_value = mock_news_client
    
    # Mock PDF Gen LLM
    mock_model_pdf = MagicMock()
    mock_model_pdf.generate_content.return_value.text = "Analysis Result"
    mock_genai_pdf.GenerativeModel.return_value = mock_model_pdf
    
    # Create dummy files if needed
    os.makedirs("files/uploads", exist_ok=True)
    import pandas as pd
    df = pd.DataFrame({'Ticker': ['AAPL'], 'Company Name': ['Apple'], 'Reversal Date': ['2025-07-18']})
    df.to_excel("files/uploads/test_final.xlsx", index=False)
    
    # Import main after mocks are set up (though imports inside function help too)
    from apps.api.main import run_analysis
    
    # Run
    result = await run_analysis(mode="default", file_path="files/uploads/test_final.xlsx")
    
    print("Result:", result)
    
    if result['status'] == 'completed' and result['report_path'].endswith('.pdf'):
        print("SUCCESS: Pipeline completed and returned PDF path.")
    else:
        print("FAILURE: Pipeline did not return expected result.")

if __name__ == "__main__":
    asyncio.run(test_final_pipeline())
