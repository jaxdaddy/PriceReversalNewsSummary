# Price Reversal News Summary

This project automates the analysis of stock data for price reversal opportunities by combining market data with news sentiment analysis using Google Gemini and NewsAPI. It features a Gmail poller to automatically fetch and process new data files sent via email, orchestrating the entire workflow via a `runner.py` script suitable for scheduled execution.

## Workflow

The entire workflow is orchestrated by `runner.py`:

1.  **Gmail Polling**: The `runner.py` initiates the Gmail poller, which polls a specified Gmail account for unread emails with "DOW30" in the subject.
2.  **Attachment Download**: Upon finding an email, the poller downloads the attached `.xlsx` file into the `files/uploads/` directory and marks the email as read.
3.  **Pipeline Trigger**: The downloaded Excel file is then passed to the main PRNS processing pipeline.
4.  **Data Ingestion & Analysis**: The pipeline loads, analyzes, and enriches the stock data with news sentiment using Google Gemini.
5.  **Report Generation**: A final PDF report is generated in the `files/reports/` directory.
6.  **Archiving**: The processed Excel file is moved to a `files/uploads/completed/` subdirectory.
7.  **Email Delivery**: The generated PDF report is emailed to a configurable list of recipients.
8.  **Metrics Tracking**: Key metrics from the run are saved to a local SQLite database.

## Features

-   **Orchestrated Execution**: A single `runner.py` script manages the end-to-end workflow, ideal for scheduled tasks.
-   **Gmail Polling**: Automatically polls a Gmail account for new data files using OAuth 2.0 for secure authentication.
-   **Automated File Processing**: Automatically detects and processes the newest `.xlsx` file, moving it to a `files/uploads/completed/` subdirectory upon successful completion.
-   **LLM Normalization**: Uses Google Gemini to normalize company names for more accurate news fetching.
-   **News Scraping**: Fetches news articles related to the selected companies using the NewsAPI.
-   **Metrics Calculation**: Calculates readability (Flesch-Kincaid), word count, and relevance scores.
-   **PDF Report Generation**: Creates a human-readable PDF report summarizing the analysis, with rich markdown formatting and footers.
-   **Email Delivery**: Automatically sends the generated PDF report to a configurable list of recipients.
-   **Metrics Storage**: Stores all run metrics in a SQLite database (`pipeline_metrics.db`).
-   **Debug Mode**: A configurable debug mode to limit processing for testing and development.

---

## Setup & Installation

#### 1. Clone the Repository
```bash
git clone [repository-url]
cd PriceReversalNewsSummary
```

#### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

#### 3. Configure API Keys & Environment
Create a `.env` file in the project root. You can copy the examples as a starting point. This file will hold your API keys and environment settings.

**For the main pipeline:**
-   Copy `.env.example` to your `.env` file.
-   Add your keys for `NEWSAPI_KEY` and `GEMINI_API_KEY`.
-   **Gemini Model Name**: It is highly recommended to explicitly set the Gemini model name to a known working version to avoid `404 Not Found` errors. Add the following to your `.env` file:
    ```
    GEMINI_MODEL_NAME=models/gemini-pro-latest
    ```
    Alternatively, `models/gemini-flash-latest` can be used for faster, but potentially less capable, responses.
-   Set `DEBUG_MODE=False` for full runs or `True` to process only 2 companies.

**For the Gmail Poller & Email Sender:**
-   Add the following variables from `.env.example_gmail_poller` to your `.env` file:
    ```
    # Directory where attachments from Gmail will be saved.
    DOWNLOAD_DIR=/path/to/PriceReversalNewsSummary/files/uploads

    # Time in minutes to wait between polling attempts.
    POLL_SLEEP_MINUTES=10

    # Number of times to retry polling if no email is found.
    MAX_RETRIES=3

    # Comma-separated list of recipient email addresses for PRNS reports.
    # Example: recipient1@example.com,recipient2@example.com
    PRNS_EMAIL_RECIPIENTS=
    ```
    **Note**: Ensure `DOWNLOAD_DIR` is set to the absolute path of the `files/uploads` directory.

#### 4. Configure Gmail API Access (OAuth 2.0)
Both the Gmail Poller and the Email Sender use OAuth 2.0 for secure authentication.

1.  **Create a Google Cloud Project:** If you don't have one, create one at the [Google Cloud Console](https://console.cloud.google.com/).
2.  **Enable the Gmail API:** In your project, search for and enable the "Gmail API".
3.  **Configure the OAuth Consent Screen:**
    -   Go to the "OAuth consent screen" page.
    -   Choose **External** user type and click Create.
    -   Fill in the required app information (app name, user support email, etc.). Save and continue through the rest of the steps.
4.  **Create Credentials:**
    -   Go to the "Credentials" page.
    -   Click **+ CREATE CREDENTIALS** and select **OAuth client ID**.
    -   Set the **Application type** to **Desktop app**.
    -   Click **Create**.
    -   Click **DOWNLOAD JSON**. Rename the file to `credentials.json` and place it in the project root. This file is sensitive and is already in `.gitignore`.

---

## Usage

#### 1. First-Time Authorization for Gmail
Before running the `runner.py` script for the first time (or after changing Gmail API scopes), you must authorize it:
1.  Place your `credentials.json` file in the project root.
2.  Run the `runner.py` script (it will automatically trigger the authorization flow if `token.json` is missing or invalid):
    ```bash
    python3 runner.py
    ```
3.  A browser window will open. Log in to the Google account (`prnsemail@gmail.com`) and grant the requested permissions (for both `gmail.modify` and `gmail.send` scopes).
4.  The script will save a `token.json` file in the project root. This will be used for all future authentications.

#### 2. Running the PRNS Orchestrator (`runner.py`)
This is the primary entry point for the entire automated workflow.
```bash
python3 runner.py
```
The `runner.py` script will:
1.  Poll Gmail for new Excel files.
2.  Process any downloaded files through the PRNS pipeline.
3.  Generate a PDF report.
4.  Email the PDF report to the configured recipients.
5.  Archive the processed Excel file.

#### 3. Running the Pipeline Manually
You can bypass the email poller and run the analysis pipeline directly with a local Excel file:
```bash
python3 run_pipeline.py default /path/to/your/file.xlsx
```

## Output

The application generates two primary outputs:
1.  **PDF Report**: A summary report saved to the `files/reports/` directory, including richly formatted LLM responses, tables, and footers.
2.  **Database Record**: A new entry in the `price_reversal_core/pipeline_metrics.db` SQLite database.

---

## Scheduling & Daemonization

The `runner.py` script is designed for unattended execution via schedulers like `cron` (Linux) or `launchd` (macOS).

**Key considerations for scheduling:**
-   **Absolute Paths**: Ensure `runner.py` is called using its absolute path, and all internal file references within the project resolve correctly.
-   **Environment Variables**: The daemon/cron job must have access to the environment variables defined in your `.env` file (e.g., `GEMINI_API_KEY`, `NEWSAPI_KEY`, `DOWNLOAD_DIR`, `PRNS_EMAIL_RECIPIENTS`). You might need to load these explicitly in your cron/launchd script.
-   **No User Interaction**: The script does not require user interaction after the initial OAuth 2.0 authorization.
-   **Exit Codes**: `runner.py` exits with status `0` for complete success, and a non-zero status (`>0`) if any stage fails (e.g., no Excel file found, pipeline failure, email sending failure). This allows schedulers to monitor job status.

#### Example Cron Entry (Linux)
To run `runner.py` every weekday at 9:00 AM (adjust path as needed):
```cron
0 9 * * 1-5 /usr/bin/python3 /path/to/PriceReversalNewsSummary/runner.py >> /path/to/PriceReversalNewsSummary/runner.log 2>&1
```
This example assumes `/usr/bin/python3` is your Python 3 interpreter and logs all output to `runner.log`.

**Important**: Ensure the user account running the cron/launchd job has the necessary permissions to read/write files and access the internet.
