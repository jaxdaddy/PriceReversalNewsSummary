
import argparse
import os
import uuid
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add project root to path
sys.path.append(os.getcwd())

def run_pipeline(mode: str, file_path: str, limit_companies: int = None):
    """
    Runs the price reversal analysis pipeline.
    """
    run_id = str(uuid.uuid4())
    
    try:
        # Check for debug mode from .env
        debug_mode_env = os.getenv("DEBUG_MODE", "False").lower() == "true"
        if debug_mode_env:
            print("Debug mode active. Limiting companies to 2.")
            limit_companies = 2 # Override if debug mode is active
            
        # 1. Ingestion
        from price_reversal_core.ingestion import load_excel
        df = load_excel(file_path)
        
        # 2. Subset Selection
        from price_reversal_core.subsets import get_subset
        subset_df = get_subset(df, mode, limit_companies=limit_companies)
        
        # Convert to list of dicts
        tickers_data = subset_df.to_dict(orient='records')
        
        # 3. LLM Normalization
        from price_reversal_core.llm_normalizer import normalize_company_names
        normalized_data = normalize_company_names(tickers_data)
        
        # 4. News Fetching & Saving
        from price_reversal_core.news_fetcher import save_news_summary
        news_path = save_news_summary(normalized_data, output_dir="files")
        
        # 5. PDF Report Generation
        from price_reversal_core.pdf_report_generator import generate_pdf_report
        
        primer_path = "price_reversal_primer.pdf"
        prompts_path = "prompts/PRNSPrompts.txt"
        
        # Generate PDF
        report_path = generate_pdf_report(
            subset_data=tickers_data,
            news_summary_path=news_path,
            primer_pdf_path=primer_path,
            prompts_path=prompts_path,
            output_dir="files/reports"
        )
            
        print(f"Pipeline completed successfully. Report generated at: {report_path}")
        
    except Exception as e:
        print(f"Pipeline failed: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the Price Reversal News Summary pipeline.")
    parser.add_argument("mode", type=str, help="The analysis mode (e.g., 'default').")
    parser.add_argument("file_path", type=str, help="The path to the Excel file.")
    parser.add_argument("--limit-companies", type=int, default=None, help="Limit the number of companies to process.")
    
    args = parser.parse_args()
    
    run_pipeline(args.mode, args.file_path, limit_companies=args.limit_companies)


