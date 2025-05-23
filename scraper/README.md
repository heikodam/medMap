# EUDAMED Scraper Pipeline - Modular Architecture

This is a refactored, modular version of the EUDAMED scraping pipeline following clean code principles and best practices.

## 🏗️ Architecture Overview

The pipeline is now organized into clear, focused modules with single responsibilities:

```
scraper_v2/
├── config/                    # Configuration and settings
│   ├── __init__.py
│   └── settings.py           # Environment variables, API URLs, constants
├── models/                    # Data models and types
│   ├── __init__.py
│   └── data_models.py        # Dataclasses for companies, devices, certificates
├── database/                  # Database operations
│   ├── __init__.py
│   └── operations.py         # Centralized Supabase operations
├── ui/                        # User interface and progress tracking
│   ├── __init__.py
│   └── progress_tracker.py   # Rich console display and progress tracking
├── pipeline/                  # Core processing logic
│   ├── __init__.py
│   ├── company_processor.py  # Company-specific processing
│   ├── device_processor.py   # Device-specific processing
│   ├── certificate_processor.py # Certificate-specific processing
│   └── orchestrator.py       # Main pipeline coordination
└── run_scraper_pipeline_new.py # Simplified main entry point
```

## 🎯 Key Improvements

### 1. **Separation of Concerns**
- **Database operations** are centralized in `database/operations.py`
- **UI logic** is separated into `ui/progress_tracker.py`
- **Business logic** is split into focused processors
- **Configuration** is centralized in `config/settings.py`

### 2. **Modularity**
- Each module has a single, clear responsibility
- Easy to test individual components
- Easy to modify or replace components

### 3. **Clean Code Principles**
- Descriptive class and method names
- Clear documentation and docstrings
- Consistent error handling
- Type hints throughout

### 4. **Maintainability**
- Much smaller, focused files
- Clear dependencies between modules
- Easy to understand the flow
- Easy to add new features

## 🚀 Usage

### Basic Usage
```bash
# Process all companies, devices, and certificates for Ukraine
python run_scraper_pipeline_new.py UA

# Process max 5 companies, 5 devices per company, 5 certificates
python run_scraper_pipeline_new.py UA 5
```

### Pipeline Types
The orchestrator supports three types of pipelines:

1. **Company Pipeline**: Processes companies and their devices only
2. **Certificate Pipeline**: Processes certificates only
3. **Complete Pipeline**: Processes both companies and certificates

## 📊 Module Details

### `config/settings.py`
- Environment variable management
- API URL configuration
- Default settings and constants
- Supabase client factory

### `models/data_models.py`
- `CompanyData`: Company information structure
- `DeviceData`: Device information structure
- `CertificateData`: Certificate information structure
- `ProcessingStats`: Progress tracking statistics
- `PipelineConfig`: Configuration for pipeline runs

### `database/operations.py`
- Centralized database operations
- CRUD operations for companies, devices, certificates
- Status management
- City management

### `ui/progress_tracker.py`
- Rich console interface
- Progress tracking and statistics
- Status updates and summaries
- Beautiful terminal output

### `pipeline/` Processors
Each processor handles a specific domain:

- **CompanyProcessor**: Fetches and processes company data
- **DeviceProcessor**: Fetches and processes device data  
- **CertificateProcessor**: Fetches and processes certificate data
- **Orchestrator**: Coordinates all processors and manages pipeline flow

## 🔄 Migration from Old Pipeline

The old `run_scraper_pipeline.py` file is preserved for reference. The new pipeline:

1. **Maintains the same functionality** - all features are preserved
2. **Uses the same database schema** - no database changes needed
3. **Provides the same CLI interface** - same command-line usage
4. **Improves performance** - better error handling and progress tracking

## 🧪 Testing

To test individual components:

```python
# Test company processing
from pipeline.company_processor import CompanyProcessor
from ui.progress_tracker import ProgressTracker

progress = ProgressTracker()
processor = CompanyProcessor(progress)
companies = processor.fetch_companies_for_country("UA")
```

## 🔧 Configuration

Environment variables (set in `.env`):
- `SUPABASE_URL`: Your Supabase project URL
- `SUPABASE_KEY`: Your Supabase API key

Default settings can be modified in `config/settings.py`:
- `DEFAULT_PAGE_SIZE`: API pagination size (default: 300)
- `MAX_RETRY_ATTEMPTS`: Retry attempts for failed requests (default: 3)
- `RETRY_DELAY_SECONDS`: Delay between retries (default: 5)

## 🚨 Error Handling

The new architecture provides robust error handling:
- **Graceful degradation**: Individual failures don't crash the entire pipeline
- **Detailed logging**: Clear error messages with context
- **Status tracking**: Database records track processing status
- **Retry logic**: Automatic retries for transient failures

## 📈 Performance

Performance improvements in the new architecture:
- **Better memory management**: Processing one item at a time
- **Clearer progress tracking**: Real-time progress updates
- **Optimized database operations**: Batch operations where possible
- **Async processing**: Non-blocking operations throughout

## 🤝 Contributing

When adding new features:
1. Follow the modular architecture
2. Add appropriate error handling
3. Include progress tracking
4. Update this README
5. Use snake_case for naming
6. Add type hints
7. Include docstrings 