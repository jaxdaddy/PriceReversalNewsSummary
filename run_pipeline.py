
import argparse
import os
import uuid
import sys
import glob
import shutil
from datetime import datetime # Import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add project root to path
sys.path.append(os.getcwd())

# Import database manager
from price_reversal_core.database_manager import initialize_database, insert_metrics_record

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
        from price_reversal_core.pdf_report_generator import extract_pdf_text # Import extract_pdf_text
        
        primer_path = "price_reversal_primer.pdf"
        prompts_path = "prompts/PRNSPrompts.txt"
        
        print(f"\nTickers data being passed to PDF report generator: {tickers_data}\n")
        
        # Generate PDF
        report_path = generate_pdf_report(
            subset_data=tickers_data,
            news_summary_path=news_path,
            primer_pdf_path=primer_path,
            prompts_path=prompts_path,
            output_dir="files/reports"
        )
            
        print(f"Pipeline completed successfully. Report generated at: {report_path}")

        # 6. Calculate Metrics on the generated PDF content
        from price_reversal_core.metrics_calculator import calculate_text_metrics
        
        # Extract text from the generated PDF
        pdf_content = extract_pdf_text(report_path)
        
        print("\nCalculating metrics on PDF report content...")
        metrics = calculate_text_metrics(pdf_content, tickers_data)
        
        print("Metrics:")
        for key, value in metrics.items():
            print(f"  {key}: {value}")
        
        # 7. Store Metrics in Database
        input_filename = os.path.basename(file_path)
        output_filename = os.path.basename(report_path)
        insert_metrics_record(input_filename, output_filename, metrics)

        return True # Indicate success
        
    except Exception as e:
        print(f"Pipeline failed: {e}")
        return False # Indicate failure

if __name__ == "__main__":
    # Initialize database at the start of the script
    initialize_database()

    parser = argparse.ArgumentParser(description="Run the Price Reversal News Summary pipeline.")
    parser.add_argument("mode", type=str, help="The analysis mode (e.g., 'default').")
    parser.add_argument("file_path", type=str, nargs='?', default=None, help="The path to the Excel file. If not provided, the newest .xlsx in 'files/uploads' will be used.")
    parser.add_argument("--limit-companies", type=int, default=None, help="Limit the number of companies to process.")
    
    args = parser.parse_args()
    
    target_file_path = args.file_path
    
    if target_file_path is None:
        uploads_dir = "files/uploads"
        xlsx_files = glob.glob(os.path.join(uploads_dir, "*.xlsx"))
        
        if not xlsx_files:
            print(f"Error: No .xlsx files found in '{uploads_dir}'. Please provide a file path or ensure files exist.")
            sys.exit(1)
            
        # Sort by modification time (newest first)
        target_file_path = max(xlsx_files, key=os.path.getmtime)
        print(f"No file_path provided. Automatically selected newest file: '{target_file_path}'")
        
    # Run the pipeline
    success = run_pipeline(args.mode, target_file_path, limit_companies=args.limit_companies)
    
    if success:
        # Move processed file to 'completed' subdirectory
        uploads_dir = "files/uploads"
        completed_dir = os.path.join(uploads_dir, "completed")
        os.makedirs(completed_dir, exist_ok=True)
        
        try:
            original_filename = os.path.basename(target_file_path)
            destination_path = os.path.join(completed_dir, original_filename)
            
            # If file already exists in completed, append timestamp
            if os.path.exists(destination_path):
                timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
                name, ext = os.path.splitext(original_filename)
                new_filename = f"{name}_{timestamp}{ext}"
                destination_path = os.path.join(completed_dir, new_filename)
                print(f"File '{original_filename}' already exists in '{completed_dir}'. Renaming to '{new_filename}'.")

            shutil.move(target_file_path, destination_path)
            print(f"Successfully moved '{original_filename}' to '{destination_path}'")
        except Exception as e:
            print(f"Error moving file '{target_file_path}' to '{completed_dir}': {e}")




