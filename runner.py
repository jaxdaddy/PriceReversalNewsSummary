import os
import sys
import logging
import shutil
from datetime import datetime
from dotenv import load_dotenv

# Ensure the project root is in the path for module imports
sys.path.append(os.getcwd())

# Load environment variables from .env file
load_dotenv()

# --- Configure Logging ---
# This logger will be used by runner.py itself
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout) # Log to stdout
    ]
)
logger = logging.getLogger("runner")

# Import the core components
from gmail_poller.gmail_poller import run_poller
from run_pipeline import execute_pipeline
from email_sender import send_prns_report

def main():
    """
    Orchestrates the entire PRNS workflow: polling Gmail, running the pipeline, and emailing the report.
    Exits with status 0 on success, >0 on failure.
    """
    run_start_time = datetime.now()
    logger.info(f"PRNS Runner started at {run_start_time.strftime('%Y-%m-%d %H:%M:%S')}")

    # --- Configuration ---
    DOWNLOAD_DIR = os.getenv("DOWNLOAD_DIR")
    if not DOWNLOAD_DIR:
        logger.error("DOWNLOAD_DIR environment variable is not set. Exiting.")
        sys.exit(1)
    
    PRNS_EMAIL_RECIPIENTS_STR = os.getenv("PRNS_EMAIL_RECIPIENTS")
    if PRNS_EMAIL_RECIPIENTS_STR:
        recipients = [r.strip() for r in PRNS_EMAIL_RECIPIENTS_STR.split(',') if r.strip()]
    else:
        logger.warning("PRNS_EMAIL_RECIPIENTS not set in .env. Email will not be sent.")
        recipients = []

    # Ensure necessary directories exist
    uploads_dir = os.path.join(os.getcwd(), "files", "uploads")
    completed_dir = os.path.join(uploads_dir, "completed")
    reports_dir = os.path.join(os.getcwd(), "files", "reports")
    os.makedirs(uploads_dir, exist_ok=True)
    os.makedirs(completed_dir, exist_ok=True)
    os.makedirs(reports_dir, exist_ok=True)


    excel_file_path = None
    pdf_report_path = None
    try:
        # --- Stage 1: Gmail Poller ---
        logger.info("Attempting to poll Gmail for new Excel files...")
        excel_file_path = run_poller()
        
        if not excel_file_path:
            logger.warning("No new Excel file retrieved from Gmail. Skipping pipeline execution and email sending.")
            # This is a warning, not a hard error, as per spec (log warning, not necessarily exit non-zero if no file is found)
            # However, the spec also says: "If no file is found after retries: Log warning, Exit with non-zero status"
            # So we will exit non-zero if no file is found.
            sys.exit(2) # Exit code for "no new file"
        
        logger.info(f"Successfully retrieved Excel file: {excel_file_path}")

        # --- Stage 2: PRNS Processing Pipeline ---
        logger.info(f"Executing PRNS pipeline for: {excel_file_path}")
        pdf_report_path = execute_pipeline(excel_file_path)
        
        if not pdf_report_path:
            logger.error(f"PRNS pipeline failed for {excel_file_path}. Exiting.")
            sys.exit(3) # Exit code for "pipeline failed"
        
        logger.info(f"Successfully generated PDF report: {pdf_report_path}")

        # --- Archiving the processed Excel file ---
        try:
            original_filename = os.path.basename(excel_file_path)
            destination_path = os.path.join(completed_dir, original_filename)
            
            # If file already exists in completed, append timestamp
            if os.path.exists(destination_path):
                timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
                name, ext = os.path.splitext(original_filename)
                new_filename = f"{name}_{timestamp}{ext}"
                destination_path = os.path.join(completed_dir, new_filename)
                logger.info(f"File '{original_filename}' already exists in '{completed_dir}'. Renaming to '{new_filename}'.")

            shutil.move(excel_file_path, destination_path)
            logger.info(f"Successfully moved '{original_filename}' to '{destination_path}'")
        except Exception as e:
            logger.error(f"Error archiving processed Excel file '{excel_file_path}': {e}", exc_info=True)
            # Continue, as pipeline succeeded, but log this issue. Not a critical exit.


        # --- Stage 3: Email Sender ---
        if recipients:
            logger.info(f"Attempting to email report {pdf_report_path} to {', '.join(recipients)}")
            if not send_prns_report(pdf_report_path, recipients):
                logger.error("Failed to send email report. Exiting.")
                sys.exit(4) # Exit code for "email failed"
            logger.info("Email report sent successfully.")
        else:
            logger.warning("No recipients configured, skipping email sending.")

    except Exception as e:
        logger.critical(f"An unhandled error occurred in the runner: {e}", exc_info=True)
        sys.exit(5) # Generic unhandled error

    logger.info("PRNS Runner completed successfully.")
    sys.exit(0) # Success

if __name__ == "__main__":
    main()
