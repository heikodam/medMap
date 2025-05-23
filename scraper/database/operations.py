import uuid
import json
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone

from config.settings import get_supabase_client
from models.data_models import CompanyData, DeviceData, CertificateData, ContactData

class DatabaseOperations:
    """Centralized database operations for the scraper"""
    
    def __init__(self):
        self.supabase = get_supabase_client()
    
    # Company operations
    def check_company_exists(self, eudamed_uuid: str) -> Optional[Dict[str, Any]]:
        """Check if a company exists in the database"""
        result = self.supabase.table('eudamed_company').select("*").eq("eudamed_uuid", eudamed_uuid).execute()
        return result.data[0] if result.data else None
    
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
        self.supabase.table('eudamed_company').update({"scraping_status": status}).eq('id', company_id).execute()
    
    def update_company_srn(self, company_id: str, srn: str) -> None:
        """Update company SRN (eudamed_identifier)"""
        self.supabase.table('eudamed_company').update({"eudamed_identifier": srn}).eq('id', company_id).execute()
    
    # Device operations
    def check_device_exists(self, eudamed_uuid: str) -> Optional[Dict[str, Any]]:
        """Check if a device exists in the database"""
        result = self.supabase.table('eudamed_product').select("*").eq("eudamed_uuid", eudamed_uuid).execute()
        return result.data[0] if result.data else None
    
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
        self.supabase.table('eudamed_product').update({"scraping_status": status}).eq('id', device_id).execute()
    
    # Certificate operations
    def check_certificate_exists(self, eudamed_uuid: str) -> Optional[Dict[str, Any]]:
        """Check if a certificate exists in the database"""
        result = self.supabase.table('eudamed_certificate').select("*").eq("eudamed_uuid", eudamed_uuid).execute()
        return result.data[0] if result.data else None
    
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
        self.supabase.table('eudamed_certificate').update({"scraping_status": status}).eq('id', certificate_id).execute()
    
    # City operations
    async def get_or_create_city(self, city_name: str) -> str:
        """Get or create a city record and return its ID"""
        existing_city = self.supabase.table('city').select('id').eq('name', city_name).execute()
        if existing_city.data:
            return existing_city.data[0]['id']
        else:
            new_city = self.supabase.table('city').insert({'name': city_name}).execute()
            return new_city.data[0]['id']
    
    # Contact operations
    def check_contact_exists(self, contact_data: ContactData) -> Optional[Dict[str, Any]]:
        """Check if a contact person exists in the database based on key fields"""
        query = self.supabase.table('eudamed_contact_people').select('*').eq('company_id', contact_data.company_id)
        
        # Build query based on available data
        if contact_data.email:
            query = query.eq('email', contact_data.email)
        if contact_data.phone:
            query = query.eq('phone', contact_data.phone)
        if contact_data.first_name:
            query = query.eq('first_name', contact_data.first_name)
        if contact_data.family_name:
            query = query.eq('family_name', contact_data.family_name)
        if contact_data.position:
            query = query.eq('position', contact_data.position)
            
        result = query.execute()
        return result.data[0] if result.data else None
    
    def create_contact_record(self, contact_data: ContactData) -> Dict[str, Any]:
        """Create a new contact person record in the database"""
        # Remove None values from the contact_data
        contact_dict = {
            "company_id": contact_data.company_id,
        }
        
        # Only add non-None values
        if contact_data.first_name is not None:
            contact_dict["first_name"] = contact_data.first_name
        if contact_data.family_name is not None:
            contact_dict["family_name"] = contact_data.family_name
        if contact_data.email is not None:
            contact_dict["email"] = contact_data.email
        if contact_data.phone is not None:
            contact_dict["phone"] = contact_data.phone
        if contact_data.position is not None:
            contact_dict["position"] = contact_data.position
        if contact_data.city_id is not None:
            contact_dict["city_id"] = contact_data.city_id
        if contact_data.iso_code is not None:
            contact_dict["iso_code"] = contact_data.iso_code
        
        result = self.supabase.table('eudamed_contact_people').insert(contact_dict).execute()
        return result.data[0]
    
    def update_contact_record(self, contact_id: str, contact_data: ContactData) -> Dict[str, Any]:
        """Update an existing contact person record"""
        # Build update dictionary with only non-None values
        update_dict = {}
        
        if contact_data.first_name is not None:
            update_dict["first_name"] = contact_data.first_name
        if contact_data.family_name is not None:
            update_dict["family_name"] = contact_data.family_name
        if contact_data.email is not None:
            update_dict["email"] = contact_data.email
        if contact_data.phone is not None:
            update_dict["phone"] = contact_data.phone
        if contact_data.position is not None:
            update_dict["position"] = contact_data.position
        if contact_data.city_id is not None:
            update_dict["city_id"] = contact_data.city_id
        if contact_data.iso_code is not None:
            update_dict["iso_code"] = contact_data.iso_code
        
        self.supabase.table('eudamed_contact_people').update(update_dict).eq('id', contact_id).execute()
        
        # Return updated record
        result = self.supabase.table('eudamed_contact_people').select("*").eq("id", contact_id).execute()
        return result.data[0] 