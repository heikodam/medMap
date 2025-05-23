import asyncio
import aiohttp
from typing import List, Dict, Any, Callable, Optional, Awaitable
from dataclasses import dataclass

from config.settings import DEFAULT_PAGE_SIZE, DEFAULT_CONCURRENT_REQUESTS
from .api_client import EudamedApiClient, RequestConfig


@dataclass
class BatchConfig:
    """Configuration for batch processing"""
    batch_size: int = DEFAULT_CONCURRENT_REQUESTS
    page_size: int = DEFAULT_PAGE_SIZE
    max_batches: Optional[int] = None  # Limit total number of batches processed


class BatchProcessor:
    """
    Common batch processing utilities for scraper operations.
    
    This class extracts the common patterns for fetching and processing
    records in batches from the database and API.
    """
    
    def __init__(self, api_client: Optional[EudamedApiClient] = None, 
                 config: Optional[BatchConfig] = None):
        self.api_client = api_client or EudamedApiClient()
        self.config = config or BatchConfig()
    
    async def process_records_in_batches(self, 
                                       fetch_records_func: Callable[[int, int], Any],
                                       process_record_func: Callable[[aiohttp.ClientSession, Dict[str, Any]], Awaitable[None]],
                                       record_type: str = "records") -> Dict[str, int]:
        """
        Generic method to process records in batches.
        
        Args:
            fetch_records_func: Function to fetch records from database (batch_size, from_)
            process_record_func: Async function to process individual record (session, record)
            record_type: Type of records being processed (for logging)
            
        Returns:
            Dictionary with processing statistics
        """
        stats = {"total_processed": 0, "batches_processed": 0, "errors": 0}
        from_ = 0
        batch_count = 0
        
        async with self.api_client.create_session() as session:
            while True:
                # Check batch limit
                if self.config.max_batches and batch_count >= self.config.max_batches:
                    print(f"Reached maximum batch limit of {self.config.max_batches}")
                    break
                
                # Fetch next batch of records
                try:
                    response = fetch_records_func(self.config.batch_size, from_)
                    records = response.data if hasattr(response, 'data') else response
                    
                    if not records:
                        print(f"No more {record_type} found.")
                        break
                    
                    # Process batch
                    await self._process_batch(session, records, process_record_func, record_type)
                    
                    # Update statistics
                    stats["total_processed"] += len(records)
                    stats["batches_processed"] += 1
                    batch_count += 1
                    from_ += self.config.batch_size
                    
                    print(f"Processed {stats['total_processed']} {record_type} so far.")
                    
                    # Check if this was a partial batch (end of data)
                    if len(records) < self.config.batch_size:
                        break
                        
                except Exception as e:
                    print(f"Error fetching batch {batch_count}: {str(e)}")
                    stats["errors"] += 1
                    break
        
        print(f"Finished processing {record_type}. Total processed: {stats['total_processed']}")
        return stats
    
    async def _process_batch(self, session: aiohttp.ClientSession, records: List[Dict[str, Any]], 
                           process_func: Callable[[aiohttp.ClientSession, Dict[str, Any]], Awaitable[None]],
                           record_type: str) -> None:
        """Process a batch of records concurrently"""
        tasks = []
        
        for record in records:
            task = self._safe_process_record(session, record, process_func, record_type)
            tasks.append(task)
        
        # Use return_exceptions to prevent one failure from stopping all tasks
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Log any exceptions that occurred
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                record_id = records[i].get('id', records[i].get('eudamed_uuid', 'unknown'))
                print(f"Failed to process {record_type} {record_id}: {result}")
    
    async def _safe_process_record(self, session: aiohttp.ClientSession, record: Dict[str, Any], 
                                 process_func: Callable[[aiohttp.ClientSession, Dict[str, Any]], Awaitable[None]],
                                 record_type: str) -> None:
        """Safely process a single record with error handling"""
        try:
            await process_func(session, record)
        except Exception as e:
            record_id = record.get('id', record.get('eudamed_uuid', 'unknown'))
            print(f"Error processing {record_type} {record_id}: {str(e)}")
            raise  # Re-raise to be caught by gather()
    
    async def process_paginated_api_data(self, 
                                       fetch_page_func: Callable[[aiohttp.ClientSession, int], Awaitable[Optional[Dict[str, Any]]]],
                                       process_items_func: Callable[[List[Dict[str, Any]]], Awaitable[None]],
                                       data_type: str = "items") -> Dict[str, int]:
        """
        Process paginated data from an API endpoint.
        
        Args:
            fetch_page_func: Function to fetch a page of data (session, page_number)
            process_items_func: Function to process items from a page
            data_type: Type of data being processed (for logging)
            
        Returns:
            Dictionary with processing statistics
        """
        stats = {"total_processed": 0, "pages_processed": 0, "errors": 0}
        page = 0
        
        async with self.api_client.create_session() as session:
            while True:
                try:
                    # Fetch page data
                    data = await fetch_page_func(session, page)
                    
                    if not data:
                        print(f"No data returned for page {page}")
                        break
                    
                    # Extract items based on common response formats
                    items = self._extract_items_from_response(data)
                    
                    if not items:
                        print(f"No {data_type} found on page {page}")
                        break
                    
                    # Process items
                    await process_items_func(items)
                    
                    # Update statistics
                    stats["total_processed"] += len(items)
                    stats["pages_processed"] += 1
                    
                    print(f"Processed page {page}: {len(items)} {data_type}")
                    
                    # Check if this is the last page
                    if self._is_last_page(data, items):
                        break
                    
                    page += 1
                    
                except Exception as e:
                    print(f"Error processing page {page}: {str(e)}")
                    stats["errors"] += 1
                    break
        
        print(f"Finished processing {data_type}. Total processed: {stats['total_processed']}")
        return stats
    
    def _extract_items_from_response(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract items from API response based on common formats"""
        # Handle different response formats
        if 'content' in data:
            return data['content']
        elif 'data' in data:
            return data['data']
        elif 'items' in data:
            return data['items']
        elif isinstance(data, list):
            return data
        else:
            # If data is a dict but doesn't match expected formats, return empty list
            return []
    
    def _is_last_page(self, data: Dict[str, Any], items: List[Dict[str, Any]]) -> bool:
        """Determine if this is the last page of data"""
        # Check common pagination indicators
        if 'last' in data:
            return data['last']
        elif 'hasMore' in data:
            return not data['hasMore']
        elif 'totalPages' in data and 'number' in data:
            return data['number'] >= data['totalPages'] - 1
        else:
            # If items length is less than expected page size, assume last page
            return len(items) < self.config.page_size 