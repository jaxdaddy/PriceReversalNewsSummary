import google.generativeai as genai
import os
import json
from typing import List, Dict

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

def normalize_company_names(tickers_data: List[Dict]) -> List[Dict]:
    """
    Uses Gemini to normalize company names for better search results.
    Input: List of dicts with 'Ticker' and 'Company Name'
    Output: List of dicts with added 'SearchQuery'
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("Warning: GEMINI_API_KEY not found. Using raw names.")
        for item in tickers_data:
            item['SearchQuery'] = item.get('Company Name', '')
        return tickers_data

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('models/gemini-2.0-flash') # Or specific model from config

    prompt = f"""
    You are a financial data assistant. I will provide a list of companies. 
    Your task is to return a JSON list where each object has 'Symbol' and 'SearchQuery'.
    'SearchQuery' should be the best string to use for searching news about the company (e.g., removing 'Inc.', 'Corp.', adding common brand names).
    
    Input:
    {json.dumps(tickers_data, default=str)}
    
    Output JSON:
    """
    
    try:
        response = model.generate_content(prompt)
        
        # Write response to file for debugging
        with open("gemini_response.txt", "w") as f:
            f.write(response.text)
            
        # Basic cleanup to ensure JSON parsing
        text = response.text.replace("```json", "").replace("```", "").strip()
        normalized_data = json.loads(text)
        
        # Merge back results
        lookup = {}
        for item in normalized_data:
            lookup[item['Symbol']] = item['SearchQuery']
        
        for item in tickers_data:
            item['SearchQuery'] = lookup.get(item['Symbol'], item.get('Company Name', ''))
            
        return tickers_data
    except Exception as e:
        print(f"Error in LLM normalization: {e}")
        # Fallback
        for item in tickers_data:
            item['SearchQuery'] = item.get('Company Name', '')
        return tickers_data
