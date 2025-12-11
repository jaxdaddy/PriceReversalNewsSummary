import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

DOWNLOAD_DIR = os.getenv("DOWNLOAD_DIR")
POLL_SLEEP_MINUTES = int(os.getenv("POLL_SLEEP_MINUTES", 10))
MAX_RETRIES = int(os.getenv("MAX_RETRIES", 3))

# Ensure essential variables are set
if not all([DOWNLOAD_DIR]):
    raise ValueError("The essential environment variable DOWNLOAD_DIR is not set.")
