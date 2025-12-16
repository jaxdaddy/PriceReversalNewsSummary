import email
import time
import logging
import os
import base64
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from .config import DOWNLOAD_DIR, POLL_SLEEP_MINUTES, MAX_RETRIES
from .attachment_utils import save_attachment
# Removed import of run_pipeline as it will be called by runner.py

logger = logging.getLogger(__name__)

# Define the scopes for the Gmail API
SCOPES = ["https://www.googleapis.com/auth/gmail.modify", "https://www.googleapis.com/auth/gmail.send"]

def get_gmail_service_poller():
    """
    Authenticates with the Gmail API using OAuth 2.0 and returns a service object.
    This function will ensure the token.json has both modify and send scopes.
    """
    creds = None
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            logger.info("Gmail poller credentials expired. Refreshing...")
            creds.refresh(Request())
        else:
            if not os.path.exists("credentials.json"):
                logger.error("credentials.json not found. Please ensure it's in the project root.")
                return None
            logger.info("No valid Gmail poller credentials found. Starting authorization flow...")
            flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
            creds = flow.run_local_server(port=0)
        
        with open("token.json", "w") as token:
            token.write(creds.to_json())
            logger.info("Gmail poller credentials saved to token.json")
    
    try:
        service = build("gmail", "v1", credentials=creds)
        logger.info("Gmail API service for polling built successfully.")
        return service
    except HttpError as error:
        logger.error(f"An error occurred building the Gmail service for polling: {error}")
        return None

def run_poller() -> str or None:
    """
    Polls Gmail for unread emails with "DOW30" in the subject using the Gmail API,
    downloads attached .xlsx files, marks the email as read, and returns the path to the downloaded file.

    Returns:
        str: The full path to the downloaded .xlsx file if successful, otherwise None.
    """
    for attempt in range(1, MAX_RETRIES + 1):
        logger.info(f"Polling attempt {attempt}/{MAX_RETRIES}...")
        service = None
        try:
            service = get_gmail_service_poller()
            if not service:
                logger.warning(f"Could not get Gmail service on attempt {attempt}. Retrying...")
                time.sleep(POLL_SLEEP_MINUTES * 60)
                continue

            # Search for unread emails with "DOW30" in the subject
            query = "is:unread subject:DOW30"
            results = service.users().messages().list(userId="me", q=query).execute()
            messages = results.get("messages", [])

            if not messages:
                logger.info("No matching unread emails found.")
                # Only sleep if we're going to retry
                if attempt < MAX_RETRIES:
                    time.sleep(POLL_SLEEP_MINUTES * 60)
                continue

            for message_info in messages:
                msg_id = message_info["id"]
                msg = service.users().messages().get(userId="me", id=msg_id, format="raw").execute()
                
                raw_email = base64.urlsafe_b64decode(msg["raw"].encode("ASCII"))
                email_message = email.message_from_bytes(raw_email)
                
                subject = email_message["subject"]
                logger.info(f"Found matching email with subject: {subject}")

                saved_filepath = None
                for part in email_message.walk():
                    if part.get_content_type() == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet":
                        filename = part.get_filename()
                        if filename and filename.endswith(".xlsx"):
                            logger.info(f"Found .xlsx attachment: {filename}")
                            saved_filepath = save_attachment(part, filename, DOWNLOAD_DIR)
                            if not saved_filepath:
                                logger.error(f"Failed to save attachment {filename}.")
                            break  # Found the attachment, no need to look further

                if saved_filepath:
                    # Mark email as read first
                    logger.info(f"Marking email {msg_id} as read.")
                    service.users().messages().modify(
                        userId="me", id=msg_id, body={"removeLabelIds": ["UNREAD"]}
                    ).execute()
                    
                    logger.info(f"Successfully found, downloaded, and marked email as read: {saved_filepath}")
                    return saved_filepath # Return the path to the downloaded file

        except HttpError as error:
            logger.error(f"An HttpError occurred during polling attempt {attempt}: {error}")
        except Exception as e:
            logger.error(f"An unexpected error occurred during polling attempt {attempt}: {e}", exc_info=True)
        
        # Only sleep if an error occurred or no email was found AND we are retrying
        if attempt < MAX_RETRIES:
            logger.info(f"Sleeping for {POLL_SLEEP_MINUTES} minutes before retrying...")
            time.sleep(POLL_SLEEP_MINUTES * 60)

    logger.warning(f"No DOW30 email with .xlsx attachment found after {MAX_RETRIES} attempts.")
    return None # No file processed after all attempts

if __name__ == "__main__":
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    downloaded_file = run_poller()
    if downloaded_file:
        logger.info(f"Poller test successful: Downloaded {downloaded_file}")
    else:
        logger.error("Poller test failed or no new file found.")