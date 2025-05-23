# Legacy Scraper Files

This directory contains the **original individual scraper files** that were used before the modular refactoring.

## Files Overview

- `get_company_id.py` - Original script to fetch company IDs for a country
- `get_company_details.py` - Original script to fetch and process company details
- `get_company_devices.py` - Original script to fetch devices for a company
- `get_company_devices_details.py` - Original script to fetch and process device details
- `get_certificates.py` - Original script to fetch certificates
- `get_certificate_details.py` - Original script to fetch and process certificate details

## Status

These files have been **superseded** by the new modular architecture:

- **New Pipeline**: Use `run_scraper.py` in the root directory
- **Modular Components**: See `pipeline/`, `scrapers/`, `database/`, and `common/` directories
- **API Client**: Replaced by `common/api_client.py`
- **Database Operations**: Replaced by `database/operations.py`

## Purpose

These files are kept for:
- **Reference** - Understanding the original implementation
- **Backup** - Fallback if needed during transition
- **Documentation** - Historical context of the refactoring

## Migration Status

✅ **Company Processing**: Migrated to `pipeline/processors/company_processor.py`  
✅ **Device Processing**: Migrated to `pipeline/processors/device_processor.py`  
✅ **Certificate Processing**: Migrated to `pipeline/processors/certificate_processor.py`  
✅ **API Client**: Migrated to `common/api_client.py`  
✅ **Database Operations**: Migrated to `database/operations.py`  

## Usage

**❌ Don't use these files directly anymore**

**✅ Use the new pipeline instead:**
```bash
python run_scraper.py UA 5
```

See the main README.md for current usage instructions. 