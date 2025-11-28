# Price Reversal News Summary

This project automates the analysis of stock data for price reversal opportunities by combining market data with news sentiment analysis using Google Gemini and NewsAPI.

## Features

-   **Excel Data Ingestion**: Loads stock data from an Excel spreadsheet.
-   **Subset Selection**: Filters and selects relevant stock entries based on criteria (e.g., latest reversal dates).
-   **LLM Normalization**: Uses Google Gemini to normalize company names for more accurate news fetching.
-   **News Scraping**: Fetches news articles related to the selected companies using the NewsAPI.
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
python3 run_pipeline.py <mode> <file_path> [--limit-companies <number>]
```

**Arguments**:

-   `<mode>`: The analysis mode (e.g., `default`).
-   `<file_path>`: The path to the Excel file containing stock data (e.g., `files/uploads/SP500_2025-07-18.xlsx`).
-   `--limit-companies <number>` (Optional): Limits the number of companies processed. Useful for testing with a smaller dataset.

**Example**:

To run the pipeline in `default` mode with the provided sample data:
```bash
python3 run_pipeline.py default files/uploads/SP500_2025-07-18.xlsx
```

To run in debug mode (processing only the top 2 companies as defined in `.env`):
1.  Set `DEBUG_MODE=True` in your `.env` file.
2.  Run the pipeline:
    ```bash
    python3 run_pipeline.py default files/uploads/SP500_2025-07-18.xlsx
    ```
    (The `--limit-companies` argument will be overridden by `DEBUG_MODE` if set to `True`.)

## Output

The pipeline generates a PDF report in the `files/reports/` directory, named `PRNS_Summary-YYYY-MM-DD.pdf`. This report includes:
-   A table of selected stock data (Symbol, Company Name, Reversal Date, Reversal Price, HR1 Value, Last Close Price).
-   News summaries for each company.
-   Analysis provided by the Gemini LLM, with improved formatting for readability.