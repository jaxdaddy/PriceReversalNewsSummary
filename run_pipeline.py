import argparse
import os
# import uuid # Removed as runner.py will manage run_id
import sys
import glob
import shutil
from datetime import datetime
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()

# Add project root to path
sys.path.append(os.getcwd())

# Import database manager
from price_reversal_core.database_manager import initialize_database, insert_metrics_record

logger = logging.getLogger(__name__)

def execute_pipeline(file_path: str, mode: str = 'default', limit_companies: int = None) -> str or None:
    """
    Executes the price reversal analysis pipeline for a given Excel file.

    Args:
        file_path (str): The path to the Excel file containing stock data.
        mode (str): The analysis mode (e.g., 'default'). Defaults to 'default'.
        limit_companies (int, optional): Limits the number of companies to process. Defaults to None.

    Returns:
        str: The full path to the generated PDF report if successful, otherwise None.
    """
    # run_id = str(uuid.uuid4()) # Managed by runner.py if needed
    
    try:
        # Check for debug mode from .env
        debug_mode_env = os.getenv("DEBUG_MODE", "False").lower() == "true"
        if debug_mode_env:
            logger.info("Debug mode active. Limiting companies to 2.")
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
        from price_reversal_core.pdf_report_generator import extract_pdf_text
        
        primer_path = "price_reversal_primer.pdf"
        prompts_path = "prompts/PRNSPrompts.txt"
        
        logger.info(f"Tickers data being passed to PDF report generator: {tickers_data}")
        
        # Generate PDF
        report_path = generate_pdf_report(
            subset_data=tickers_data,
            news_summary_path=news_path,
            primer_pdf_path=primer_path,
            prompts_path=prompts_path,
            output_dir="files/reports"
        )
            
        logger.info(f"Pipeline completed successfully. Report generated at: {report_path}")

        # 6. Calculate Metrics on the generated PDF content
        from price_reversal_core.metrics_calculator import calculate_text_metrics
        
        # Extract text from the generated PDF
        pdf_content = extract_pdf_text(report_path)
        
        logger.info("Calculating metrics on PDF report content...")
        metrics = calculate_text_metrics(pdf_content, tickers_data)
        
        logger.info("Metrics:")
        for key, value in metrics.items():
            logger.info(f"  {key}: {value}")
        
        # 7. Store Metrics in Database
        input_filename = os.path.basename(file_path)
        output_filename = os.path.basename(report_path)
        insert_metrics_record(input_filename, output_filename, metrics)

        return report_path # Return the path to the generated PDF
        
    except Exception as e:
        logger.error(f"Pipeline failed for file {file_path}: {e}", exc_info=True)
        return None # Indicate failure

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
        uploads_dir = os.path.join(os.getcwd(), "files", "uploads")
        xlsx_files = glob.glob(os.path.join(uploads_dir, "*.xlsx"))
        
        if not xlsx_files:
            logger.error(f"Error: No .xlsx files found in '{uploads_dir}'. Please provide a file path or ensure files exist.")
            sys.exit(1)
            
        # Sort by modification time (newest first)
        target_file_path = max(xlsx_files, key=os.path.getmtime)
        logger.info(f"No file_path provided. Automatically selected newest file: '{target_file_path}'")
    
    # Run the pipeline
    pdf_report_path = execute_pipeline(target_file_path, args.mode, limit_companies=args.limit_companies)
    
    if pdf_report_path:
        logger.info(f"Pipeline executed successfully. PDF report: {pdf_report_path}")
        
        # Move processed file to 'completed' subdirectory (for standalone testing)
        uploads_dir = os.path.join(os.getcwd(), "files", "uploads")
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
                logger.info(f"File '{original_filename}' already exists in '{completed_dir}'. Renaming to '{new_filename}'.")

            shutil.move(target_file_path, destination_path)
            logger.info(f"Successfully moved '{original_filename}' to '{destination_path}'")
        except Exception as e:
            logger.error(f"Error moving file '{target_file_path}' to '{completed_dir}': {e}", exc_info=True)
        
    else:
        logger.error("Pipeline execution failed.")
        sys.exit(1)