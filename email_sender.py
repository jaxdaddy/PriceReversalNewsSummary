import os
import base64
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText # Added this import
from email import encoders
from datetime import datetime # Added for dynamic test PDF path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

logger = logging.getLogger(__name__)

# Scopes required for sending emails
SCOPES = ["https://www.googleapis.com/auth/gmail.send"]

def get_gmail_service_send():
    """
    Authenticates with the Gmail API using OAuth 2.0 and returns a service object
    with the necessary scope for sending emails.
    """
    creds = None
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            logger.info("Email sender credentials expired. Refreshing...")
            creds.refresh(Request())
        else:
            if not os.path.exists("credentials.json"):
                logger.error("credentials.json not found. Please ensure it's in the project root.")
                return None
            logger.info("No valid email sender credentials found. Starting authorization flow...")
            # Ensure the InstalledAppFlow uses the correct SCOPES
            flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
            creds = flow.run_local_server(port=0)
        
        with open("token.json", "w") as token:
            token.write(creds.to_json())
            logger.info("Email sender credentials saved to token.json")
    
    try:
        service = build("gmail", "v1", credentials=creds)
        logger.info("Gmail API service for sending emails built successfully.")
        return service
    except HttpError as error:
        logger.error(f"An error occurred building the Gmail service for sending: {error}")
        return None

def send_prns_report(pdf_path: str, recipients: list) -> bool:
    """
    Sends the generated PDF report via email to a list of recipients.

    Args:
        pdf_path (str): The full path to the PDF file to attach.
        recipients (list): A list of recipient email addresses.

    Returns:
        bool: True if the email was sent successfully, False otherwise.
    """
    if not os.path.exists(pdf_path):
        logger.error(f"PDF file not found at: {pdf_path}. Cannot send email.")
        return False
    
    if not recipients:
        logger.error("No recipient email addresses provided. Cannot send email.")
        return False

    service = get_gmail_service_send()
    if not service:
        logger.error("Failed to get Gmail service for sending email.")
        return False

    try:
        sender_email = "prnsemail@gmail.com" # As per specification
        email_subject = "PRNS Summary and Analysis" # As per specification
        email_body = "Please see the attached PDF document." # As per specification

        message = MIMEMultipart()
        message["to"] = ", ".join(recipients)
        message["from"] = sender_email
        message["subject"] = email_subject
        message.attach(MIMEText(email_body, "plain")) # Body as plain text

        # Attach PDF
        with open(pdf_path, "rb") as attachment:
            part = MIMEBase("application", "octet-stream")
            part.set_payload(attachment.read())
        encoders.encode_base64(part)
        part.add_header(
            "Content-Disposition",
            f"attachment; filename= {os.path.basename(pdf_path)}",
        )
        message.attach(part)

        # Encode message for Gmail API
        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode("utf-8")
        
        # Send the email
        send_message = (
            service.users()
            .messages()
            .send(userId="me", body={"raw": raw_message})
            .execute()
        )
        logger.info(f"Email sent successfully. Message Id: {send_message['id']}")
        return True

    except HttpError as error:
        logger.error(f"An API error occurred while sending email: {error}")
        return False
    except Exception as e:
        logger.error(f"An unexpected error occurred while sending email: {e}")
        return False

if __name__ == "__main__":
    # Example usage (for testing)
    # This block will require a token.json with the gmail.send scope,
    # and a valid credentials.json
    
    # Placeholder for a generated PDF - make it dynamic for testing
    test_pdf_path = os.path.join("files", "reports", f"PRNS_Summary-{datetime.now().strftime('%Y-%m-%d')}.pdf")
    
    test_recipients_str = os.getenv("PRNS_EMAIL_RECIPIENTS")
    
    if test_recipients_str:
        test_recipients = [r.strip() for r in test_recipients_str.split(',') if r.strip()]
    else:
        # Fallback for testing - replace with your own email for local testing
        test_recipients = ["your_email@example.com"] 

    if os.path.exists(test_pdf_path):
        logger.info(f"Attempting to send test email with PDF: {test_pdf_path} to {test_recipients}")
        if send_prns_report(test_pdf_path, test_recipients):
            logger.info("Test email sent successfully!")
        else:
            logger.error("Failed to send test email.")
    else:
        logger.warning(f"Test PDF not found at {test_pdf_path}. Cannot send test email.")