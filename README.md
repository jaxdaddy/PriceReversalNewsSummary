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
-   Add the following variables from `.env.example_gmail_poller` to your `.env` file and configure them:
    -   `DOWNLOAD_DIR`: The absolute path where email attachments will be saved.
        -   **On Windows**, use double backslashes (e.g., `C:\\Users\\YourUser\\path\\to\\files\\uploads`).
        -   **On macOS/Linux**, use forward slashes (e.g., `/Users/YourUser/path/to/files/uploads`).
    -   `POLL_SLEEP_MINUTES`: Time in minutes to wait between polling attempts.
    -   `MAX_RETRIES`: Number of times to retry polling if no email is found.
    -   `PRNS_EMAIL_RECIPIENTS`: A comma-separated list of recipient email addresses.
    ```
    # Example for .env
    DOWNLOAD_DIR=C:\\Users\\YourUser\\PriceReversalNewsSummary\\files\\uploads
    POLL_SLEEP_MINUTES=10
    MAX_RETRIES=3
    PRNS_EMAIL_RECIPIENTS=recipient1@example.com,recipient2@example.com
    ```
    **Note**: The rest of the documentation will assume a macOS/Linux path structure for brevity. Please adjust paths accordingly for your operating system.


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

#### Example for Windows Task Scheduler
On Windows, you can use the Task Scheduler to run the script on a schedule.

1.  **Open Task Scheduler**: Press `Win + R`, type `taskschd.msc`, and press Enter.
2.  **Create a New Task**: In the "Actions" pane, click "Create Task...".
3.  **General Tab**: Give the task a name (e.g., "Run PRNS") and description.
4.  **Triggers Tab**:
    -   Click "New..." to add a trigger.
    -   Configure the schedule (e.g., "Daily" or "Weekly" at a specific time).
5.  **Actions Tab**:
    -   Click "New..." to create an action.
    -   **Action**: Select "Start a program".
    -   **Program/script**: Enter the full path to your Python interpreter (e.g., `C:\Python39\python.exe`).
    -   **Add arguments (optional)**: Enter `runner.py`.
    -   **Start in (optional)**: Enter the full path to the project directory (e.g., `C:\Users\YourUser\PriceReversalNewsSummary`). This is important so the script can find the `.env` file and other resources.
6.  **Conditions/Settings Tabs**: Review and adjust power settings or other conditions as needed.
7.  **Save**: Click "OK" to save the task.

**Important**: Ensure the user account running the cron/launchd job has the necessary permissions to read/write files and access the internet.
---

## Docker Usage

This application can be containerized using Docker, which simplifies dependency management and ensures a consistent runtime environment.

### Prerequisites
-   [Docker](https://www.docker.com/get-started) installed on your machine.

### 1. First-Time Authorization (One-Time Step)
The Google API authentication requires an interactive, browser-based flow. This cannot be done inside the Docker container directly. You must perform this step once on your host machine.

1.  Complete the setup steps in the "Setup & Installation" section on your local machine (install dependencies, configure `.env`, and download `credentials.json`).
2.  Run the authorization flow:
    ```bash
    python3 runner.py
    ```
3.  This will open a browser, ask for authentication, and create a `token.json` file in your project root. **This file is essential for the Docker container.**

### 2. Configure for Docker
Before building the image, ensure your `.env` file is configured for the container's environment. The key change is the `DOWNLOAD_DIR`:

```
# .env file for Docker
DOWNLOAD_DIR=/app/files/uploads
GEMINI_API_KEY=your_gemini_key
NEWSAPI_KEY=your_newsapi_key
PRNS_EMAIL_RECIPIENTS=your_email@example.com
# ... other variables
```

### 3. Build the Docker Image
From the project root directory, run the following command:

```bash
docker build -t prns-app .
```

### 4. Run the Docker Container
To run the application, you need to mount the Google API credentials and provide the environment variables.

-   **`--env-file ./.env`**: Passes all variables from your `.env` file to the container.
-   **`-v ./credentials.json:/app/credentials.json:ro`**: Mounts your `credentials.json` file in read-only mode.
-   **`-v ./token.json:/app/token.json:ro`**: Mounts the `token.json` you generated, giving the container authentication.

Run the container with the following command:

```bash
docker run --rm --name prns-runner --env-file ./.env -v ./credentials.json:/app/credentials.json:ro -v ./token.json:/app/token.json:ro prns-app
```

When the container runs, it will execute `python runner.py` and begin the workflow. Any generated reports or downloaded files will be stored *inside the container*. To access them, you can use `docker cp` or mount additional volumes for the `files/reports` and `files/uploads` directories.

**Example with output volumes:**

```bash
# Create local directories to store outputs
mkdir -p ./files/reports ./files/uploads

# Run with volumes for reports and uploads
docker run --rm --name prns-runner \
  --env-file ./.env \
  -v ./credentials.json:/app/credentials.json:ro \
  -v ./token.json:/app/token.json:ro \
  -v ./files/reports:/app/files/reports \
  -v ./files/uploads:/app/files/uploads \
  prns-app
```

