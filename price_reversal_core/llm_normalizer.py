import google.generativeai as genai
import os
import json
from typing import List, Dict
from tenacity import retry, stop_after_attempt, wait_exponential
from google.api_core.exceptions import ResourceExhausted

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=2, min=5, max=60),
    reraise=True  # Reraise the final exception after retries are exhausted
)
def _generate_with_retry(model, prompt: str):
    """Internal function to call the Gemini API with retry logic."""
    print("Generating content with Gemini...")
    return model.generate_content(prompt)

def normalize_company_names(tickers_data: List[Dict]) -> List[Dict]:
    """
    Uses Gemini to normalize company names for better search results.
    Input: List of dicts with 'Ticker' and 'Company Name'
    Output: List of dicts with added 'SearchQuery'
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("Warning: GEMINI_API_KEY not found. Using raw company names.")
        for item in tickers_data:
            item['SearchQuery'] = item.get('Company Name', '')
        return tickers_data

    genai.configure(api_key=api_key)
    # Use 'gemini-pro-latest' which is a standard, generally available model.
    model = genai.GenerativeModel('models/gemini-pro-latest')

    prompt = f"""
    You are a financial data assistant. I will provide a list of companies. 
    Your task is to return a JSON list where each object has 'Symbol' and 'SearchQuery'.
    'SearchQuery' should be the best string to use for searching news about the company (e.g., removing 'Inc.', 'Corp.', adding common brand names).
    
    Input:
    {json.dumps(tickers_data, default=str)}
    
    Output JSON:
    """
    
    try:
        response = _generate_with_retry(model, prompt)
        
        with open("gemini_response.txt", "w") as f:
            f.write(response.text)
            
        text = response.text.replace("```json", "").replace("```", "").strip()
        normalized_data = json.loads(text)
        
        lookup = {item['Symbol']: item['SearchQuery'] for item in normalized_data}
        
        for item in tickers_data:
            item['SearchQuery'] = lookup.get(item['Symbol'], item.get('Company Name', ''))
            
        return tickers_data
        
    except (ResourceExhausted, Exception) as e:
        print(f"LLM normalization failed after multiple retries: {e}")
        print("Falling back to using raw company names for news search.")
        for item in tickers_data:
            item['SearchQuery'] = item.get('Company Name', '')
        return tickers_data
