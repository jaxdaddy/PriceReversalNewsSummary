import logging
import os
from logging.handlers import RotatingFileHandler

def setup_logging():
    """
    Sets up a standardized logging configuration for the gmail_poller module.
    Logs messages to both console and a rotating file.
    """
    log_file_path = os.path.join(os.path.dirname(__file__), 'logs', 'gmail_poller.log')
    
    # Ensure the log directory exists
    os.makedirs(os.path.dirname(log_file_path), exist_ok=True)

    # Basic configuration
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),  # Console output
            RotatingFileHandler(
                log_file_path,
                maxBytes=10485760,  # 10 MB
                backupCount=5,
                encoding='utf8'
            )
        ]
    )
    
    # Set a more verbose level for specific modules if needed, e.g., for debugging IMAP
    # logging.getLogger('imaplib').setLevel(logging.DEBUG)

# Call setup_logging when this module is imported
setup_logging()
