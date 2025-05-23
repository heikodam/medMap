import uuid
from typing import Optional, Dict, Any

from models.data_models import DeviceData
from .base_database_operations import BaseDatabaseOperations


class DeviceDatabaseOperations(BaseDatabaseOperations):
    """Database operations specific to devices"""
    
    def check_device_exists(self, eudamed_uuid: str) -> Optional[Dict[str, Any]]:
        """Check if a device exists in the database"""
        return self._check_record_exists('eudamed_product', 'eudamed_uuid', eudamed_uuid)
    
    def create_device_record(self, device_data: DeviceData) -> Dict[str, Any]:
        """Create a new device record in the database"""
        new_device = {
            "id": str(uuid.uuid4()),
            "name": device_data.name,
            "company_id": device_data.company_id,
            "eudamed_uuid": device_data.eudamed_uuid,
            "scraping_status": "PIPELINE_PROCESSING_DEVICE"
        }
        result = self.supabase.table('eudamed_product').insert(new_device).execute()
        return result.data[0]
    
    def update_device_record(self, device_data: DeviceData) -> Dict[str, Any]:
        """Update an existing device record"""
        updated_device = {
            "name": device_data.name,
            "company_id": device_data.company_id,
            "scraping_status": "PIPELINE_PROCESSING_DEVICE"
        }
        self.supabase.table('eudamed_product').update(updated_device).eq("eudamed_uuid", device_data.eudamed_uuid).execute()
        
        # Return updated record
        result = self.supabase.table('eudamed_product').select("*").eq("eudamed_uuid", device_data.eudamed_uuid).execute()
        return result.data[0]
    
    def update_device_status(self, device_id: str, status: str) -> None:
        """Update device scraping status"""
        self._update_record_status('eudamed_product', device_id, status) 