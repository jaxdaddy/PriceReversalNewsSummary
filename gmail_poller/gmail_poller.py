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
from .run_pipeline_wrapper import run_pipeline

logger = logging.getLogger(__name__)

# Define the scopes for the Gmail API
SCOPES = ["https://www.googleapis.com/auth/gmail.modify"]

def get_gmail_service():
    """
    Authenticates with the Gmail API using OAuth 2.0 and returns a service object.
    """
    creds = None
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            logger.info("Credentials expired. Refreshing...")
            creds.refresh(Request())
        else:
            if not os.path.exists("credentials.json"):
                logger.error("credentials.json not found. Please run oauth_test.py first.")
                return None
            logger.info("No valid credentials found. Starting authorization flow...")
            flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
            creds = flow.run_local_server(port=0)
        
        with open("token.json", "w") as token:
            token.write(creds.to_json())
            logger.info("Credentials saved to token.json")
    
    try:
        service = build("gmail", "v1", credentials=creds)
        logger.info("Gmail API service built successfully.")
        return service
    except HttpError as error:
        logger.error(f"An error occurred building the Gmail service: {error}")
        return None

def poll_for_DOW30_and_process():
    """
    Polls Gmail for unread emails with "DOW30" in the subject using the Gmail API,
    downloads attached .xlsx files, and triggers the processing pipeline.
    """
    for attempt in range(1, MAX_RETRIES + 1):
        logger.info(f"Polling attempt {attempt}/{MAX_RETRIES}...")
        service = None
        try:
            service = get_gmail_service()
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
                time.sleep(POLL_SLEEP_MINUTES * 60)
                continue

            found_and_processed = False
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
                    
                    # Now that all Gmail operations are done, run the pipeline
                    logger.info(f"Attempting to run pipeline for: {saved_filepath}")
                    if run_pipeline(saved_filepath):
                        found_and_processed = True
                        break  # Exit after processing one email successfully
                    else:
                        logger.error(f"Pipeline failed for {saved_filepath}. The email was already marked as read.")
                        # Decide on error handling: maybe re-mark as unread? For now, just log and stop.
                        break
            
            if found_and_processed:
                logger.info("Successfully found, downloaded, and processed one email.")
                return

        except HttpError as error:
            logger.error(f"An HttpError occurred during polling attempt {attempt}: {error}")
        except Exception as e:
            logger.error(f"An unexpected error occurred during polling attempt {attempt}: {e}", exc_info=True)
        
        if attempt < MAX_RETRIES:
            logger.info(f"No matching email found or processed on attempt {attempt}. Sleeping for {POLL_SLEEP_MINUTES} minutes before retrying...")
            time.sleep(POLL_SLEEP_MINUTES * 60)

    logger.warning(f"No DOW30_ email with .xlsx attachment found after {MAX_RETRIES} attempts.")

if __name__ == "__main__":
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    poll_for_DOW30_and_process()