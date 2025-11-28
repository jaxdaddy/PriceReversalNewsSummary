import os
import json
from unittest.mock import MagicMock, patch
from price_reversal_core.pdf_report_generator import generate_pdf_report

@patch('price_reversal_core.pdf_report_generator.genai')
def test_pdf_gen(mock_genai):
    print("Starting PDF generator verification...")
    
    # Mock Gemini
    mock_model = MagicMock()
    mock_model.generate_content.return_value.text = "This is a mock response from Gemini.\n\nIt analyzes the data and news."
    mock_genai.GenerativeModel.return_value = mock_model
    
    # Dummy Data
    subset_data = [
        {
            'Ticker': 'AAPL', 
            'Company Name': 'Apple Inc.', 
            'Reversal Date': '2025-07-18', 
            'Direction': 'down', 
            'Expected Magnitude %': 5.0
        }
    ]
    
    # Create dummy news summary
    news_path = "files/dummy_news.txt"
    with open(news_path, "w") as f:
        f.write("News for AAPL: Stock is down.")
        
    # Use existing files
    primer_path = "price_reversal_primer.pdf"
    prompts_path = "prompts/PRNSPrompts.txt"
    
    # Run generator
    # Mock env var
    with patch.dict(os.environ, {'GEMINI_API_KEY': 'dummy_key'}):
        output_path = generate_pdf_report(
            subset_data,
            news_path,
            primer_path,
            prompts_path
        )
        
    print(f"PDF generated at: {output_path}")
    
    if os.path.exists(output_path):
        print("SUCCESS: PDF file created.")
    else:
        print("FAILURE: PDF file not found.")

if __name__ == "__main__":
    test_pdf_gen()
