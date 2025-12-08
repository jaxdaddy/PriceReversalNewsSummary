# Price Reversal News Summary

This project automates the analysis of stock data for price reversal opportunities by combining market data with news sentiment analysis using Google Gemini and NewsAPI.

## Features

-   **Excel Data Ingestion**: Loads stock data from an Excel spreadsheet.
-   **Automated File Processing**: Automatically detects and processes the newest `.xlsx` file in the `files/uploads/` directory, moving it to a `files/uploads/completed/` subdirectory upon successful completion.
-   **Subset Selection**: Filters and selects relevant stock entries based on criteria (e.g., latest reversal dates).
-   **LLM Normalization**: Uses Google Gemini to normalize company names for more accurate news fetching.
-   **News Scraping**: Fetches news articles related to the selected companies using the NewsAPI.
-   **Metrics Calculation**: Calculates readability (Flesch-Kincaid Grade Level), word count, and a basic keyword-based relevance score for the generated news summaries.
-   **Metrics Storage**: Stores the input filename, output filename, and all calculated metrics in a SQLite database (`pipeline_metrics.db`) for historical tracking and analysis.
-   **PDF Report Generation**: Creates a human-readable PDF report summarizing the analysis, including formatted Gemini LLM responses and tables.
-   **CLI Interface**: Run the entire pipeline easily from the command line.
-   **Debug Mode**: A configurable debug mode to limit processing for testing and development.

## Setup

1.  **Clone the repository**:
    ```bash
    git clone [repository-url]
    cd PriceReversalNewsSummary
    ```

2.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

3.  **Configure API Keys**:
    -   Copy `.env.example` to `.env`:
        ```bash
        cp .env.example .env
        ```
    -   Open the newly created `.env` file and replace the placeholder values with your actual API keys:
        ```
        NEWSAPI_KEY=your_newsapi_key_here
        GEMINI_API_KEY=your_gemini_api_key_here
        ALPHA_VANTAGE_API_KEY=your_alpha_vantage_api_key_here # if applicable
        DEBUG_MODE=False # Set to True to enable debug mode (processes only 2 companies)
        ```
    **Note on NewsAPI**: The free tier of NewsAPI has strict rate limits (e.g., 100 requests per day). If you encounter `rateLimited` errors, consider upgrading your plan, waiting for the limit to reset, or using the debug mode.

## Usage

The pipeline is executed via a command-line interface.

```bash
python3 run_pipeline.py <mode> [file_path] [--limit-companies <number>]
```

**Arguments**:

-   `<mode>`: The analysis mode (e.g., `default`).
-   `[file_path]` (Optional): The path to the Excel file containing stock data. If not provided, the newest `.xlsx` file in the `files/uploads/` directory will be automatically detected and used.
-   `--limit-companies <number>` (Optional): Limits the number of companies processed. Useful for testing with a smaller dataset.

**Examples**:

To run the pipeline in `default` mode, automatically detecting the newest Excel file:
```bash
python3 run_pipeline.py default
```

To run the pipeline for a specific Excel file:
```bash
python3 run_pipeline.py default files/uploads/SP500_2025-07-18.xlsx
```

To run in debug mode (processing only the top 2 companies as defined in `.env`):
1.  Set `DEBUG_MODE=True` in your `.env` file.
2.  Run the pipeline:
    ```bash
    python3 run_pipeline.py default
    ```
    (The `--limit-companies` argument will be overridden by `DEBUG_MODE` if set to `True`.)

## Output

The pipeline generates a PDF report in the `files/reports/` directory, named `PRNS_Summary-YYYY-MM-DD.pdf`. It also prints calculated metrics to the console and stores them in a database.

### PDF Report
The PDF report includes:
-   A table of selected stock data (Symbol, Company Name, Reversal Date, Direction, Reversal Price, HR1 Value, Last Close Price).
-   News summaries for each company.
-   Analysis provided by the Gemini LLM, with improved formatting for readability.
-   A footer on each page displaying an advisory ("This content was created with Artificial Intelligence") and the generation date/time, centered and in italics.

### Metrics Output
The console output for each run will include:
-   **Word Count**: Total number of words in the generated news summary.
-   **Flesch-Kincaid Grade Level**: A readability score indicating the approximate grade level needed to understand the text.
-   **Relevance Score**: A basic keyword-based score indicating how many relevant company keywords were found in the summary.
-   **Cosine Relevance**: A score (0.0 to 1.0) indicating the cosine similarity between the processed PDF content and the combined company keywords.

### Database Storage
A SQLite database file named `pipeline_metrics.db` is created in the `price_reversal_core/` directory. Each successful pipeline run inserts a new record into this database, including:
-   `input_filename`: The name of the Excel file processed.
-   `output_filename`: The name of the generated PDF report.
-   `word_count`: Word count of the PDF content.
-   `flesch_kincaid_grade`: Readability score of the PDF content.
-   `cosine_relevance`: Cosine similarity score.
-   `relevance_keywords_found`: Number of relevant keywords found.
-   `created_at`: Timestamp of the run.