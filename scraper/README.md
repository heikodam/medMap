# EUDAMED Scraper Pipeline

A modular, production-ready pipeline for scraping and enriching medical device data from the EUDAMED database.

## 🚀 Quick Start

```bash
# Basic scraping for Ukraine
python run_scraper.py UA

# Scrape with enrichment (website fetching, URL cleaning, employee count)
python run_scraper.py UA --enrichment

# Limit processing to 5 companies
python run_scraper.py UA 5 --enrichment
```

## 🏗️ Architecture

```
scraper/
├── config/          # Configuration and settings
├── models/          # Data models and types
├── database/        # Database operations
├── ui/              # Progress tracking and console interface
├── pipeline/        # Core processing logic
│   ├── processors/  # Processing modules
│   │   └── services/  # Specialized enrichment services
│   └── orchestrators/  # Pipeline coordination
├── common/          # Shared utilities
├── scrapers/        # Data fetching modules
└── docs/            # Detailed documentation
```

## 🎯 Key Features

- **Modular Design**: Each component has a single responsibility
- **Enrichment Pipeline**: Automatic website discovery and data enrichment
- **Progress Tracking**: Rich console interface with real-time updates
- **Error Handling**: Graceful degradation and comprehensive logging
- **Configurable**: Environment-based configuration for different deployments

## 🔗 Enrichment Services

### Website Fetching
Uses Perplexity AI to discover company websites automatically.

### URL Cleaning  
Normalizes and cleans website URLs using OpenAI GPT for consistency.

### Employee Count
Fetches employee count information from company websites.

## ⚙️ Configuration

Required environment variables:

```bash
# Database
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key

# Enrichment APIs (optional)
OPENAI_API_KEY=your_openai_key        # For URL cleaning
PERPLEXITY_API_KEY=your_perplexity_key # For website fetching
```

## 📊 Pipeline Types

- **Company Pipeline**: Processes companies and their devices
- **Certificate Pipeline**: Processes certificates only  
- **Complete Pipeline**: Processes both companies and certificates
- **Enrichment Pipeline**: Adds data enrichment to company processing

## 🧪 Development

### Testing Components

```python
# Test individual processors
from pipeline.processors.company_processor import CompanyProcessor
from ui.progress_tracker import ProgressTracker

progress = ProgressTracker()
processor = CompanyProcessor(progress)
companies = processor.fetch_companies_for_country("UA")
```

### Adding New Services

1. Create service in `pipeline/processors/services/`
2. Add to `services/__init__.py`
3. Use in appropriate processor

## 📚 Documentation

For detailed documentation, see the [`docs/`](./docs/) folder:

- **Implementation Details**: Detailed technical documentation
- **Architecture Decisions**: Design rationale and patterns
- **API References**: Service and processor documentation

## 🔄 Migration

This pipeline maintains full compatibility with the existing database schema and provides the same CLI interface as previous versions, with added enrichment capabilities.

---

**Need help?** Check the [detailed documentation](./docs/) or examine the example usage in `example_usage.py`. 