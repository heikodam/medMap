# Enrichment Pipeline Documentation

## Overview

The enrichment pipeline adds additional data to companies after the main scraping process. It consists of two main steps:

1. **Website Fetching**: Finding company websites using Perplexity AI
2. **URL Cleaning**: Normalizing website URLs using OpenAI GPT

## Architecture

### Core Components

```
pipeline/processors/
├── enrichment_processor.py     # Main enrichment coordinator
└── services/
    └── url_cleaning_service.py # URL cleaning and normalization
```

### Flow Diagram

```
Company Data
     ↓
┌─────────────────────────────────────────────┐
│           Enrichment Processor              │
│                                             │
│  ┌─────────────────┐  ┌───────────────────┐ │
│  │ Website Fetching│  │   URL Cleaning    │ │
│  │   (Perplexity)  │  │    (OpenAI)       │ │
│  │  → website      │  │original_website   │ │
│  │                 │  │  → website        │ │
│  └─────────────────┘  └───────────────────┘ │
└─────────────────────────────────────────────┘
     ↓
Updated Company Data

Flow Logic:
- No original_website? → Perplexity → website field
- Has original_website? → OpenAI cleaning → website field (preserve original_website)
```

## Usage

### Command Line

```bash
# Enable enrichment for all companies
python run_scraper.py UA --enrichment

# Enable enrichment with limits
python run_scraper.py UA 10 --enrichment

# Test enrichment integration
python test_url_cleaning_integration.py UA 5
```

### Programmatic Usage

```python
from pipeline.processors.enrichment_processor import EnrichmentProcessor
from ui.progress_tracker import ProgressTracker

# Initialize
progress = ProgressTracker()
enrichment = EnrichmentProcessor(progress)

# Process a single company
enriched_company = await enrichment.process_company_enrichment(company_data)
```

## Configuration

### Required Environment Variables

```bash
# For URL cleaning (required)
OPENAI_API_KEY=your_openai_api_key

# For website fetching (optional)
PERPLEXITY_API_KEY=your_perplexity_api_key

# Database access
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key
```

### API Costs

- **OpenAI GPT-4o-mini**: ~$0.00015 per URL cleaning request
- **Perplexity Sonar**: ~$0.005 per website search request

## Processing Logic

### Website Fetching

**Conditions for execution:**
- Company has no `original_website` field (is null or empty)
- Perplexity API key is available

**Process:**
1. Query Perplexity API for company website
2. Extract domain from response
3. Store directly in `website` field (not original_website)
4. Update `scraping_status` to `FETCHED_WEBSITE_PERPLEXITY`

**Skip conditions:**
- Company already has `original_website` (from EUDAMED)
- No Perplexity API key available

### URL Cleaning

**Conditions for execution:**
- Company has `original_website` field (from EUDAMED, not from Perplexity)
- Company not already marked as `CLEANED_WEBSITE`
- OpenAI API key is available

**Process:**
1. Send `original_website` to OpenAI GPT for cleaning
2. Normalize URL format (e.g., "domain.com")
3. Store cleaned URL in `website` field
4. Preserve original in `original_website` field
5. Update `scraping_status` to `CLEANED_WEBSITE`

**Skip conditions:**
- Company has no `original_website` (either never had one or was enriched with Perplexity)
- Already processed (`scraping_status` = `CLEANED_WEBSITE`)
- No OpenAI API key available

## Database Schema

### Fields Used

| Field | Type | Description |
|-------|------|-------------|
| `website` | text | Cleaned, normalized website URL |
| `original_website` | text | Original website URL (from API or scraping) |
| `scraping_status` | text | Processing status tracker |

### Status Values

| Status | Description |
|--------|-------------|
| `FETCHED_WEBSITE_PERPLEXITY` | Website found using Perplexity API |
| `ERROR_WEBSITE_SEARCH` | Website search failed |
| `CLEANED_WEBSITE` | URL cleaning completed |

## Error Handling

### Website Fetching Errors
- **API failures**: Marked as `ERROR_WEBSITE_SEARCH`
- **Invalid responses**: Gracefully handled, no website stored
- **Rate limiting**: Automatic retry with exponential backoff

### URL Cleaning Errors
- **API failures**: Original URL preserved, status updated
- **Invalid responses**: Original URL kept as fallback
- **Missing API key**: Process skipped with warning

### Graceful Degradation
- Missing API keys don't crash the pipeline
- Individual failures don't affect other companies
- Clear logging for all error conditions

## Performance Considerations

### Batching
- Companies are processed one at a time
- Each company goes through both enrichment steps sequentially
- Database updates are atomic per company

### Rate Limiting
- Perplexity API: ~60 requests per minute
- OpenAI API: ~3500 requests per minute (tier 1)
- Built-in retry logic for rate limit errors

### Memory Usage
- Minimal memory footprint (processes one company at a time)
- No large data structures held in memory
- Database connections are managed efficiently

## Testing

### Unit Testing

```bash
# Test URL cleaning service
python -c "
from pipeline.processors.services.url_cleaning_service import UrlCleaningService
from ui.progress_tracker import ProgressTracker
service = UrlCleaningService(ProgressTracker())
print('Service initialized successfully')
"
```

### Integration Testing

```bash
# Test complete enrichment flow
python test_url_cleaning_integration.py UA 3
```

### Manual Testing

```python
# Test individual components
from pipeline.processors.enrichment_processor import EnrichmentProcessor
from ui.progress_tracker import ProgressTracker

progress = ProgressTracker()
enrichment = EnrichmentProcessor(progress)

# Mock company data
company = {
    'id': 'test-id',
    'name': 'Test Company',
    'original_website': 'https://www.example.com/',
    'scraping_status': 'FETCHED_WEBSITE_PERPLEXITY'
}

# Test enrichment
result = await enrichment.process_company_enrichment(company)
print(f"Cleaned website: {result.get('website')}")
```

## Monitoring and Logging

### Progress Tracking
- Real-time progress updates via rich console
- Color-coded status messages
- Success/failure indicators

### Status Messages
- 🔍 `Fetching website for {company_name}`
- ✅ `Found website for {company_name}: {website}`
- ❌ `Could not find website for {company_name}`
- 🧹 `Cleaning URL for {company_name}`
- ✅ `Cleaned URL for {company_name}: {old} → {new}`

### Database Tracking
- All companies have updated `scraping_status`
- Easy to query processed vs unprocessed companies
- Supports resume functionality

## Best Practices

### Development
1. Always test with small batches first
2. Monitor API usage and costs
3. Handle missing API keys gracefully
4. Use type hints throughout
5. Follow snake_case naming convention

### Production
1. Set reasonable rate limits
2. Monitor API costs
3. Use proper logging
4. Handle errors gracefully
5. Validate API responses

### Maintenance
1. Regular testing of API integrations
2. Monitor API deprecation notices
3. Update models as needed (e.g., GPT versions)
4. Clean up test data regularly

## Troubleshooting

### Common Issues

**"Import error: No module named 'services'"**
- Ensure `__init__.py` files exist in all directories
- Check Python path includes the scraper directory

**"OpenAI API error: Invalid API key"**
- Verify `OPENAI_API_KEY` environment variable
- Check API key has sufficient credits

**"Perplexity API error: Rate limit exceeded"**
- Reduce batch size or add delays
- Check API plan limits

**"Database connection error"**
- Verify Supabase credentials
- Check network connectivity

### Debug Mode

Enable detailed logging:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Performance Issues

Monitor API response times:
```python
import time
start = time.time()
# ... API call ...
print(f"API call took {time.time() - start:.2f} seconds")
``` 