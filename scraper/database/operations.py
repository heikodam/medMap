"""
Unified Database Operations Interface

This module provides a facade that maintains the same interface as the original DatabaseOperations
class while delegating to specialized operation classes for better organization and maintainability.
"""

import uuid
import json
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime, timezone, timedelta

from config.settings import get_supabase_client
from models.data_models import CompanyData, DeviceData, CertificateData, ContactData, ContactChangeData
from .company_operations import CompanyDatabaseOperations
from .device_operations import DeviceDatabaseOperations
from .certificate_operations import CertificateDatabaseOperations
from .contact_operations import ContactDatabaseOperations
from .change_tracking_operations import ChangeTrackingOperations
from .city_operations import CityDatabaseOperations


class DatabaseOperations:
    """
    Centralized database operations facade for the scraper.
    
    This class maintains the same interface as the original DatabaseOperations
    but delegates to specialized classes for better organization.
    """
    
    def __init__(self):
        # Initialize all specialized operation classes
        self._company_ops = CompanyDatabaseOperations()
        self._device_ops = DeviceDatabaseOperations()
        self._certificate_ops = CertificateDatabaseOperations()
        self._contact_ops = ContactDatabaseOperations()
        self._change_tracking_ops = ChangeTrackingOperations()
        self._city_ops = CityDatabaseOperations()
        
        # For backwards compatibility, expose the supabase client
        self.supabase = self._company_ops.supabase
    
    # Company operations - delegate to CompanyDatabaseOperations
    def check_company_exists(self, eudamed_uuid: str) -> Optional[Dict[str, Any]]:
        """Check if a company exists in the database"""
        return self._company_ops.check_company_exists(eudamed_uuid)
    
    def create_company_record(self, company_data: CompanyData) -> Dict[str, Any]:
        """Create a new company record in the database"""
        return self._company_ops.create_company_record(company_data)
    
    def update_company_status(self, company_id: str, status: str) -> None:
        """Update company scraping status"""
        self._company_ops.update_company_status(company_id, status)
    
    def update_company_srn(self, company_id: str, srn: str) -> None:
        """Update company SRN (eudamed_identifier)"""
        self._company_ops.update_company_srn(company_id, srn)
    
    # Device operations - delegate to DeviceDatabaseOperations
    def check_device_exists(self, eudamed_uuid: str) -> Optional[Dict[str, Any]]:
        """Check if a device exists in the database"""
        return self._device_ops.check_device_exists(eudamed_uuid)
    
    def create_device_record(self, device_data: DeviceData) -> Dict[str, Any]:
        """Create a new device record in the database"""
        return self._device_ops.create_device_record(device_data)
    
    def update_device_record(self, device_data: DeviceData) -> Dict[str, Any]:
        """Update an existing device record"""
        return self._device_ops.update_device_record(device_data)
    
    def update_device_status(self, device_id: str, status: str) -> None:
        """Update device scraping status"""
        self._device_ops.update_device_status(device_id, status)
    
    # Certificate operations - delegate to CertificateDatabaseOperations
    def check_certificate_exists(self, eudamed_uuid: str) -> Optional[Dict[str, Any]]:
        """Check if a certificate exists in the database"""
        return self._certificate_ops.check_certificate_exists(eudamed_uuid)
    
    def create_certificate_record(self, certificate_data: CertificateData) -> Dict[str, Any]:
        """Create a new certificate record in the database"""
        return self._certificate_ops.create_certificate_record(certificate_data)
    
    def update_certificate_record(self, certificate_data: CertificateData) -> Dict[str, Any]:
        """Update an existing certificate record"""
        return self._certificate_ops.update_certificate_record(certificate_data)
    
    def update_certificate_status(self, certificate_id: str, status: str) -> None:
        """Update certificate scraping status"""
        self._certificate_ops.update_certificate_status(certificate_id, status)
    
    # City operations - delegate to CityDatabaseOperations
    async def get_or_create_city(self, city_name: str) -> str:
        """Get or create a city record and return its ID"""
        return await self._city_ops.get_or_create_city(city_name)
    
    # Contact operations - delegate to ContactDatabaseOperations
    def get_contact_identity_key(self, contact_data: ContactData) -> str:
        """Generate a unique identity key for contact identification"""
        return self._contact_ops.get_contact_identity_key(contact_data)
    
    def get_existing_contacts_for_company(self, company_id: str) -> List[Dict[str, Any]]:
        """Get all active contacts for a company"""
        return self._contact_ops.get_existing_contacts_for_company(company_id)
    
    def find_matching_contact(self, contact_data: ContactData, existing_contacts: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Find matching contact using the identification strategy"""
        return self._contact_ops.find_matching_contact(contact_data, existing_contacts)
    
    def check_contact_exists(self, contact_data: ContactData) -> Optional[Dict[str, Any]]:
        """Check if a contact person exists in the database based on key fields"""
        return self._contact_ops.check_contact_exists(contact_data)
    
    def create_contact_record(self, contact_data: ContactData) -> Dict[str, Any]:
        """Create a new contact person record in the database"""
        return self._contact_ops.create_contact_record(contact_data)
    
    def update_contact_record(self, contact_id: int, contact_data: ContactData) -> Dict[str, Any]:
        """Update an existing contact person record"""
        return self._contact_ops.update_contact_record(contact_id, contact_data)
    
    # Change tracking operations - delegate to ChangeTrackingOperations
    def detect_contact_changes(self, existing_contact: Dict[str, Any], new_contact_data: ContactData) -> Tuple[List[str], bool]:
        """Detect what fields have changed between existing and new contact data"""
        return self._change_tracking_ops.detect_contact_changes(existing_contact, new_contact_data)
    
    def generate_change_summary(self, change_type: str, existing_contact: Optional[Dict[str, Any]], 
                              new_contact_data: ContactData, changed_fields: List[str] = None) -> str:
        """Generate human-readable change summary"""
        return self._change_tracking_ops.generate_change_summary(change_type, existing_contact, new_contact_data, changed_fields)
    
    def log_contact_change(self, change_data: ContactChangeData) -> None:
        """Log a contact change to the history table"""
        self._change_tracking_ops.log_contact_change(change_data)
    
    def process_company_contacts_with_change_tracking(self, company_id: str, new_contacts: List[ContactData], 
                                                    scrape_run_id: str) -> Dict[str, int]:
        """Process contacts for a company with full change tracking"""
        return self._change_tracking_ops.process_company_contacts_with_change_tracking(company_id, new_contacts, scrape_run_id)
    
    def create_contact_record_with_tracking(self, contact_data: ContactData, scrape_run_id: str) -> Dict[str, Any]:
        """Create a new contact record with change tracking"""
        return self._change_tracking_ops.create_contact_record_with_tracking(contact_data, scrape_run_id)
    
    def update_contact_record_with_tracking(self, contact_id: int, new_contact_data: ContactData, 
                                          existing_contact: Dict[str, Any], changed_fields: List[str], 
                                          scrape_run_id: str) -> None:
        """Update a contact record with change tracking"""
        self._change_tracking_ops.update_contact_record_with_tracking(contact_id, new_contact_data, existing_contact, changed_fields, scrape_run_id)
    
    def deactivate_contact_with_tracking(self, contact_id: int, existing_contact: Dict[str, Any], 
                                       scrape_run_id: str) -> None:
        """Deactivate a contact with change tracking"""
        self._change_tracking_ops.deactivate_contact_with_tracking(contact_id, existing_contact, scrape_run_id)
    
    def generate_scrape_run_id(self) -> str:
        """Generate a unique scrape run ID for tracking changes across a scrape session"""
        return self._change_tracking_ops.generate_scrape_run_id()
    
    def get_contact_change_history(self, company_id: Optional[str] = None, 
                                 contact_id: Optional[int] = None,
                                 change_type: Optional[str] = None,
                                 days_back: int = 30) -> List[Dict[str, Any]]:
        """Get contact change history with optional filters"""
        return self._change_tracking_ops.get_contact_change_history(company_id, contact_id, change_type, days_back) 