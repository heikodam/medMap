from typing import List, Dict, Any, Optional
from supabase import Client

from common.api_client import EudamedApiClient
from config.settings import get_supabase_client


class CompanyFetcher:
    """Handles fetching company data from database and EUDAMED API"""
    
    def __init__(self, api_client: Optional[EudamedApiClient] = None):
        self.supabase: Client = get_supabase_client()
        self.api_client = api_client or EudamedApiClient()
    
    def fetch_companies_for_processing(self, batch_size: int = 1000, from_: int = 0, 
                                     status: str = "CREATED") -> List[Dict[str, Any]]:
        """
        Fetch companies from database that need processing.
        
        Args:
            batch_size: Number of companies to fetch
            from_: Starting offset
            status: Scraping status to filter by
            
        Returns:
            List of company records
        """
        result = self.supabase.table('eudamed_company')\
            .select("*")\
            .eq("scraping_status", status)\
            .range(from_, from_ + batch_size - 1)\
            .execute()
        
        return result.data or []
    
    def fetch_companies_by_ids(self, company_ids: List[str]) -> List[Dict[str, Any]]:
        """Fetch specific companies by their IDs"""
        result = self.supabase.table('eudamed_company')\
            .select("*")\
            .in_("id", company_ids)\
            .execute()
        
        return result.data or []
    
    def fetch_companies_by_uuid(self, eudamed_uuids: List[str]) -> List[Dict[str, Any]]:
        """Fetch companies by their EUDAMED UUIDs"""
        result = self.supabase.table('eudamed_company')\
            .select("*")\
            .in_("eudamed_uuid", eudamed_uuids)\
            .execute()
        
        return result.data or [] 