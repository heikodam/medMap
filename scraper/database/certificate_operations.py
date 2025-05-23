import uuid
from typing import Optional, Dict, Any

from models.data_models import CertificateData
from .base_database_operations import BaseDatabaseOperations


class CertificateDatabaseOperations(BaseDatabaseOperations):
    """Database operations specific to certificates"""
    
    def check_certificate_exists(self, eudamed_uuid: str) -> Optional[Dict[str, Any]]:
        """Check if a certificate exists in the database"""
        return self._check_record_exists('eudamed_certificate', 'eudamed_uuid', eudamed_uuid)
    
    def create_certificate_record(self, certificate_data: CertificateData) -> Dict[str, Any]:
        """Create a new certificate record in the database"""
        new_certificate = {
            "id": str(uuid.uuid4()),
            "eudamed_uuid": certificate_data.eudamed_uuid,
            "scraping_status": "PIPELINE_PROCESSING_CERTIFICATE",
            "json_dump": certificate_data.json_dump
        }
        result = self.supabase.table('eudamed_certificate').insert(new_certificate).execute()
        return result.data[0]
    
    def update_certificate_record(self, certificate_data: CertificateData) -> Dict[str, Any]:
        """Update an existing certificate record"""
        updated_certificate = {
            "scraping_status": "PIPELINE_PROCESSING_CERTIFICATE",
            "json_dump": certificate_data.json_dump
        }
        self.supabase.table('eudamed_certificate').update(updated_certificate).eq("eudamed_uuid", certificate_data.eudamed_uuid).execute()
        
        # Return updated record
        result = self.supabase.table('eudamed_certificate').select("*").eq("eudamed_uuid", certificate_data.eudamed_uuid).execute()
        return result.data[0]
    
    def update_certificate_status(self, certificate_id: str, status: str) -> None:
        """Update certificate scraping status"""
        self._update_record_status('eudamed_certificate', certificate_id, status) 