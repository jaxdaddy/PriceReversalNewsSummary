from newsapi import NewsApiClient
import os
from datetime import datetime, timedelta
from typing import List, Dict
import time # Import the time module
# Load environment variables
from dotenv import load_dotenv
load_dotenv()
def fetch_news(companies: List[Dict], days_back: int = 7) -> str:
    """
    Fetches news for a list of companies.
    Returns a formatted string summary.
    """
    api_key = os.getenv("NEWSAPI_KEY")
    if not api_key:
        print("NEWSAPI_KEY not found. News fetching skipped.")
        return "Error: NEWSAPI_KEY not found."

    print("Initializing NewsAPI client...")
    newsapi = NewsApiClient(api_key=api_key)
    
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days_back)
    
    summary_text = f"News Summary generated on {end_date.strftime('%Y-%m-%d')}\n"
    summary_text += "=" * 50 + "\n\n"
    
    print(f"Fetching news for {len(companies)} companies from {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}...")
    
    for company in companies:
        query = company.get('SearchQuery', company.get('Company Name', company.get('Symbol')))
        symbol = company.get('Symbol', 'Unknown')
        
        print(f"  Fetching news for {symbol} with query: '{query}'...")
        
        try:
            # Add a small delay or check rate limits if necessary in production
            articles = newsapi.get_everything(q=query,
                                              from_param=start_date.strftime('%Y-%m-%d'),
                                              to=end_date.strftime('%Y-%m-%d'),
                                              language='en',
                                              sort_by='relevancy',
                                              page_size=5)
            
            if articles['status'] == 'ok' and articles['articles']:
                print(f"    Found {len(articles['articles'])} articles for {symbol}.")
                summary_text += f"\n## News for {symbol} ({query})\n"
                for article in articles['articles']:
                    summary_text += f"- **{article['title']}** ({article['source']['name']}) - {article['publishedAt'][:10]}\n"
                    summary_text += f"  {article['url']}\n"
            else:
                print(f"    No news found for {symbol}.")
                summary_text += f"\n## No news found for {symbol} ({query})\n"
                
            time.sleep(1) # Add a 1-second delay to avoid rate limiting
                
        except Exception as e:
            print(f"    Error fetching news for {symbol}: {str(e)}")
            summary_text += f"\nError fetching news for {symbol}: {str(e)}\n"
            
    print("News fetching complete.")
    return summary_text

def save_news_summary(companies: List[Dict], output_dir: str = "files") -> str:
    """
    Fetches news and saves it to a file named NewsSummary-yyyy-mm-dd.txt.
    Returns the path to the saved file.
    """
    summary_content = fetch_news(companies)
    
    current_date = datetime.now().strftime('%Y-%m-%d')
    filename = f"NewsSummary-{current_date}.txt"
    
    os.makedirs(output_dir, exist_ok=True)
    file_path = os.path.join(output_dir, filename)
    
    with open(file_path, "w") as f:
        f.write(summary_content)
        
    return file_path
