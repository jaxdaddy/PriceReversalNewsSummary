import os
import logging

# Configure logging for this module
logger = logging.getLogger(__name__)

def save_attachment(message_part, filename, download_dir):
    """
    Saves an attachment from an email message part to the specified directory.

    Args:
        message_part: The email message part containing the attachment.
        filename (str): The desired filename for the attachment.
        download_dir (str): The directory where the attachment will be saved.

    Returns:
        str or None: The full path to the saved attachment if successful, otherwise None.
    """
    if not os.path.exists(download_dir):
        logger.info(f"Creating download directory: {download_dir}")
        os.makedirs(download_dir)

    filepath = os.path.join(download_dir, filename)
    try:
        with open(filepath, "wb") as f:
            f.write(message_part.get_payload(decode=True))
        logger.info(f"Attachment saved successfully to: {filepath}")
        return filepath
    except Exception as e:
        logger.error(f"Error saving attachment {filename} to {download_dir}: {e}")
        return None
