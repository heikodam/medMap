import asyncio
import aiohttp
from typing import Optional, Dict, Any
from dataclasses import dataclass

from config.settings import EUDAMED_BASE_URLS


@dataclass
class RequestConfig:
    """Configuration for API requests"""
    max_retries: int = 3
    retry_delay_base: int = 2  # Base for exponential backoff
    timeout_total: int = 120
    timeout_connect: int = 60


class EudamedApiClient:
    """
    Common API client for EUDAMED endpoints with retry logic and error handling.
    
    This class extracts the common patterns from individual scraper files
    to reduce code duplication and provide consistent behavior.
    """
    
    def __init__(self, config: Optional[RequestConfig] = None):
        self.config = config or RequestConfig()
    
    async def fetch_json(self, session: aiohttp.ClientSession, url: str, 
                        params: Optional[Dict[str, Any]] = None, 
                        description: str = "request") -> Optional[Dict[str, Any]]:
        """
        Fetch JSON data from an API endpoint with retry logic.
        
        Args:
            session: aiohttp session to use for the request
            url: URL to fetch from
            params: Query parameters
            description: Description of the request for logging
            
        Returns:
            JSON response data or None if failed
        """
        for attempt in range(self.config.max_retries):
            try:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        print(f"HTTP {response.status} for {description}: {url}")
                        if attempt < self.config.max_retries - 1:
                            await self._wait_before_retry(attempt, description)
                        else:
                            return None
                            
            except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                if attempt < self.config.max_retries - 1:
                    print(f"Connection error for {description}. Retrying in {self._get_retry_delay(attempt)} seconds...")
                    await self._wait_before_retry(attempt, description)
                else:
                    print(f"Failed to fetch {description} after {self.config.max_retries} attempts: {str(e)}")
                    return None
        
        return None
    
    async def fetch_company_details(self, session: aiohttp.ClientSession, eudamed_uuid: str) -> Optional[Dict[str, Any]]:
        """Fetch company details from EUDAMED API"""
        url = f"{EUDAMED_BASE_URLS['actors']}/{eudamed_uuid}/publicInformation?languageIso2Code=en"
        return await self.fetch_json(session, url, description=f"company details for {eudamed_uuid}")
    
    async def fetch_certificate_details(self, session: aiohttp.ClientSession, eudamed_uuid: str) -> Optional[Dict[str, Any]]:
        """Fetch certificate details from EUDAMED API"""
        url = f"{EUDAMED_BASE_URLS['certificates']}/{eudamed_uuid}?languageIso2Code=en"
        return await self.fetch_json(session, url, description=f"certificate details for {eudamed_uuid}")
    
    async def fetch_device_details(self, session: aiohttp.ClientSession, eudamed_uuid: str) -> Optional[Dict[str, Any]]:
        """Fetch device details from EUDAMED API"""
        url = f"{EUDAMED_BASE_URLS['device_details']}/{eudamed_uuid}?languageIso2Code=en"
        return await self.fetch_json(session, url, description=f"device details for {eudamed_uuid}")
    
    async def fetch_company_devices(self, session: aiohttp.ClientSession, srn: str, 
                                  page: int = 0, page_size: int = 300) -> Optional[Dict[str, Any]]:
        """Fetch devices for a company by SRN"""
        params = {
            "page": page,
            "pageSize": page_size,
            "size": page_size,
            "iso2Code": "en",
            "srn": srn,
            "languageIso2Code": "en"
        }
        return await self.fetch_json(session, EUDAMED_BASE_URLS['devices'], params, 
                                   description=f"devices for SRN {srn} (page {page})")
    
    async def fetch_certificates_search(self, session: aiohttp.ClientSession, 
                                      page: int = 0, size: int = 1000) -> Optional[Dict[str, Any]]:
        """Fetch certificates from search endpoint"""
        params = {
            "page": page,
            "size": size,
            "languageIso2Code": "en"
        }
        return await self.fetch_json(session, EUDAMED_BASE_URLS['certificates_search'], params,
                                   description=f"certificates search (page {page})")
    
    def _get_retry_delay(self, attempt: int) -> int:
        """Calculate retry delay using exponential backoff"""
        return self.config.retry_delay_base ** attempt
    
    async def _wait_before_retry(self, attempt: int, description: str) -> None:
        """Wait before retrying with exponential backoff"""
        delay = self._get_retry_delay(attempt)
        print(f"Retrying {description} in {delay} seconds (attempt {attempt + 1}/{self.config.max_retries})")
        await asyncio.sleep(delay)
    
    @staticmethod
    def create_session(config: Optional[RequestConfig] = None) -> aiohttp.ClientSession:
        """Create a configured aiohttp session"""
        req_config = config or RequestConfig()
        timeout = aiohttp.ClientTimeout(
            total=req_config.timeout_total,
            connect=req_config.timeout_connect,
            sock_connect=req_config.timeout_connect,
            sock_read=req_config.timeout_connect
        )
        return aiohttp.ClientSession(timeout=timeout) 