# Price Reversal News Summary

This project automates the analysis of stock data for price reversal opportunities by combining market data with news sentiment analysis using Google Gemini and NewsAPI. It features a Gmail poller to automatically fetch and process new data files sent via email.

## Workflow

1.  **Gmail Polling**: The application starts by polling a specified Gmail account for unread emails with "DOW30" in the subject.
2.  **Attachment Download**: Upon finding an email, it downloads the attached `.xlsx` file into the `files/uploads/` directory and marks the email as read.
3.  **Pipeline Trigger**: The downloaded file is then passed to the main processing pipeline.
4.  **Data Ingestion & Analysis**: The pipeline loads, analyzes, and enriches the stock data with news sentiment.
5.  **Report Generation**: A final PDF report is generated in the `files/reports/` directory.
6.  **Metrics Tracking**: Key metrics from the run are saved to a local SQLite database.

## Features

-   **Gmail Polling**: Automatically polls a Gmail account for new data files using OAuth 2.0 for secure authentication.
-   **Automated File Processing**: Automatically detects and processes the newest `.xlsx` file, moving it to a `files/uploads/completed/` subdirectory upon successful completion.
-   **Subset Selection**: Filters and selects relevant stock entries based on criteria (e.g., latest reversal dates).
-   **LLM Normalization**: Uses Google Gemini to normalize company names for more accurate news fetching.
-   **News Scraping**: Fetches news articles related to the selected companies using the NewsAPI.
-   **Metrics Calculation**: Calculates readability (Flesch-Kincaid), word count, and relevance scores.
-   **Metrics Storage**: Stores all run metrics in a SQLite database (`pipeline_metrics.db`).
-   **PDF Report Generation**: Creates a human-readable PDF report summarizing the analysis, with rich markdown formatting and footers.
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

**For the Gmail Poller:**
-   Add the following variables from `.env.example_gmail_poller` to your `.env` file:
    ```
    # Directory where attachments from Gmail will be saved.
    DOWNLOAD_DIR=/path/to/PriceReversalNewsSummary/files/uploads

    # Time in minutes to wait between polling attempts.
    POLL_SLEEP_MINUTES=10

    # Number of times to retry polling if no email is found.
    MAX_RETRIES=3
    ```
    **Note**: Ensure `DOWNLOAD_DIR` is set to the absolute path of the `files/uploads` directory.

#### 4. Configure Gmail API Access (OAuth 2.0)
The Gmail Poller uses OAuth 2.0 for secure authentication.

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
Before running the poller for the first time, you must authorize it:
1.  Place your `credentials.json` file in the project root.
2.  Run the poller script:
    ```bash
    python3 -m gmail_poller.gmail_poller
    ```
3.  A browser window will open. Log in to the Google account you want to poll and grant the requested permissions.
4.  The script will save a `token.json` file in the project root. This will be used for all future authentications.

#### 2. Running the Application (Gmail Poller)
To start the automated polling application, run the Gmail Poller module:
```bash
python3 -m gmail_poller.gmail_poller
```
The poller will now search for new emails. If an email is found, it will download the attachment and automatically trigger the `run_pipeline.py` script to process it.

#### 3. Running the Pipeline Manually
You can also bypass the email poller and run the pipeline directly with a local Excel file:
```bash
python3 run_pipeline.py default /path/to/your/file.xlsx
```

## Output

The application generates two primary outputs:
1.  **PDF Report**: A summary report saved to the `files/reports/` directory, including richly formatted LLM responses, tables, and footers.
2.  **Database Record**: A new entry in the `price_reversal_core/pipeline_metrics.db` SQLite database.