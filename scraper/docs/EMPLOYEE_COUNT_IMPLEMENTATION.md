# Employee Count Enrichment Implementation

## Overview

The Employee Count Enrichment service fetches employee count information for companies using the Perplexity AI API. This service is integrated into the enrichment pipeline and runs after the URL cleaning process to utilize cleaned website information.

## Architecture

The implementation follows the established modular pattern used by other services in the scraper:

```
scraper/
├── pipeline/
│   └── processors/
│       ├── enrichment_processor.py          # Updated to include employee count step
│       └── services/
│           ├── employee_count_service.py    # New service for employee count fetching
│           ├── url_cleaning_service.py      # Existing URL cleaning service
│           └── __init__.py                  # Updated with new service
└── run_employee_count_enrichment.py        # Standalone runner script
```

## Service Components

### EmployeeCountService

**Location**: `scraper/pipeline/processors/services/employee_count_service.py`

**Purpose**: Handles fetching employee count information for companies using Perplexity AI.

**Key Features**:
- Uses Perplexity's Sonar model to find employee count information
- Supports both companies with and without websites
- Handles various number formats (with/without commas)
- Robust error handling and status tracking
- Follows the same pattern as other services

**Status Codes**:
- `GOT_EMPL_WEBSITE_PERPLEXITY`: Employee count fetched successfully (with website)
- `GOT_EMPL_WEBSITE_PERPLEXITY_NO_SITE`: Employee count fetched successfully (without website)
- `ERROR_EMPLOYEE_COUNT_FETCH`: Error occurred during fetching

### Integration with Enrichment Pipeline

The service is integrated into the existing enrichment pipeline as **Step 3**, executing after:
1. Website fetching (if needed)
2. URL cleaning

This order ensures that the employee count service uses the cleaned website information when available.

## Database Schema

The service updates the following fields in the `eudamed_company` table:

- `empl_website`: Integer field storing the employee count
- `scraping_status`: Status field tracking the processing state

## Usage

### Via Main Pipeline

When using the main scraper with enrichment enabled:

```bash
python run_scraper.py UA --enrichment
```

This will run the complete pipeline including:
1. Data scraping
2. Website fetching
3. URL cleaning
4. **Employee count enrichment** (new)

### Standalone Runner

For running only employee count enrichment:

```bash
python run_employee_count_enrichment.py <iso_code>
```

Examples:
```bash
python run_employee_count_enrichment.py UA
python run_employee_count_enrichment.py DE
```

## Configuration

### Required Environment Variables

- `PERPLEXITY_API_KEY`: Required for fetching employee count information
- `SUPABASE_URL`: Database connection URL
- `SUPABASE_KEY`: Database authentication key

### Processing Logic

The service will process companies that:
1. Have a website field (from URL cleaning or website fetching)
2. Don't already have employee count data
3. Haven't been marked with an error status

## Error Handling

The service includes comprehensive error handling:
- API failures are logged and marked appropriately
- Network timeouts are handled gracefully
- Invalid responses are parsed with fallback logic
- Companies without websites are skipped with appropriate logging

## Performance Considerations

- Includes a 1-second delay between API calls to avoid rate limiting
- Uses pagination for large datasets
- Processes companies sequentially to manage API load
- Progress tracking provides real-time status updates

## Number Extraction Logic

The service uses multiple regex patterns to extract employee counts:
- Handles comma-separated numbers (e.g., "1,000")
- Supports various text formats (e.g., "approximately 500")
- Returns None for "Unknown" or similar responses

## Testing

The service can be tested by:
1. Running the standalone script on a small dataset
2. Checking the database for updated `empl_website` values
3. Verifying appropriate status codes are set

## Future Enhancements

Potential improvements include:
- Support for additional AI models
- Caching mechanisms for previously fetched data
- Batch processing for improved performance
- More sophisticated number extraction logic 