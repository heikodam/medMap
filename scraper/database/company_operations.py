import uuid
from typing import Optional, Dict, Any

from models.data_models import CompanyData
from .base_database_operations import BaseDatabaseOperations


class CompanyDatabaseOperations(BaseDatabaseOperations):
    """Database operations specific to companies"""
    
    def check_company_exists(self, eudamed_uuid: str) -> Optional[Dict[str, Any]]:
        """Check if a company exists in the database"""
        return self._check_record_exists('eudamed_company', 'eudamed_uuid', eudamed_uuid)
    
    def create_company_record(self, company_data: CompanyData) -> Dict[str, Any]:
        """Create a new company record in the database"""
        company_id = str(uuid.uuid4())
        
        new_record = {
            "id": company_id,
            "eudamed_uuid": company_data.eudamed_uuid,
            "name": company_data.name,
            "scraping_status": "PIPELINE_CREATED",
            "iso_code": company_data.iso_code,
            "eudamed_identifier": company_data.eudamed_identifier
        }
        
        result = self.supabase.table('eudamed_company').insert(new_record).execute()
        return result.data[0]
    
    def update_company_status(self, company_id: str, status: str) -> None:
        """Update company scraping status"""
        self._update_record_status('eudamed_company', company_id, status)
    
    def update_company_srn(self, company_id: str, srn: str) -> None:
        """Update company SRN (eudamed_identifier)"""
        self.supabase.table('eudamed_company').update({"eudamed_identifier": srn}).eq('id', company_id).execute() 