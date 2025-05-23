"""
Common utilities for the EUDAMED scraper.

This module contains reusable components that extract common patterns
from individual scraper files to reduce code duplication.
"""

from .api_client import EudamedApiClient, RequestConfig
from .batch_processor import BatchProcessor, BatchConfig

__all__ = [
    'EudamedApiClient',
    'RequestConfig', 
    'BatchProcessor',
    'BatchConfig'
] 