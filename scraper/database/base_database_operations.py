from typing import Optional
from abc import ABC

from config.settings import get_supabase_client


class BaseDatabaseOperations(ABC):
    """Base class for all database operations providing common functionality"""
    
    def __init__(self):
        self.supabase = get_supabase_client()
    
    def _filter_none_values(self, data_dict: dict) -> dict:
        """Remove None values from a dictionary"""
        return {k: v for k, v in data_dict.items() if v is not None}
    
    def _check_record_exists(self, table_name: str, field_name: str, field_value: str) -> Optional[dict]:
        """Generic method to check if a record exists"""
        result = self.supabase.table(table_name).select("*").eq(field_name, field_value).execute()
        return result.data[0] if result.data else None
    
    def _update_record_status(self, table_name: str, record_id: str, status: str) -> None:
        """Generic method to update record status"""
        self.supabase.table(table_name).update({"scraping_status": status}).eq('id', record_id).execute() 