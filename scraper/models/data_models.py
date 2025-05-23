from dataclasses import dataclass
from typing import Optional, Dict, Any, List
from datetime import datetime

@dataclass
class CompanyData:
    """Data model for company information"""
    eudamed_uuid: str
    name: str
    iso_code: str
    eudamed_identifier: Optional[str] = None
    id: Optional[str] = None
    scraping_status: Optional[str] = None

@dataclass
class ContactData:
    """Data model for contact person information"""
    company_id: str
    first_name: Optional[str] = None
    family_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    position: Optional[str] = None
    city_id: Optional[str] = None
    iso_code: Optional[str] = None
    id: Optional[str] = None
    is_active: Optional[bool] = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    last_scraped_at: Optional[datetime] = None

@dataclass
class ContactChangeData:
    """Data model for tracking contact person changes"""
    contact_people_id: Optional[int] = None
    company_id: Optional[str] = None
    change_type: Optional[str] = None  # CREATED, UPDATED, DEACTIVATED, REACTIVATED
    scrape_run_id: Optional[str] = None
    
    # Previous state
    previous_first_name: Optional[str] = None
    previous_family_name: Optional[str] = None
    previous_position: Optional[str] = None
    previous_email: Optional[str] = None
    previous_phone: Optional[str] = None
    previous_city_id: Optional[int] = None
    previous_iso_code: Optional[str] = None
    
    # New state
    new_first_name: Optional[str] = None
    new_family_name: Optional[str] = None
    new_position: Optional[str] = None
    new_email: Optional[str] = None
    new_phone: Optional[str] = None
    new_city_id: Optional[int] = None
    new_iso_code: Optional[str] = None
    
    # Change metadata
    changed_fields: Optional[List[str]] = None
    change_summary: Optional[str] = None
    change_detected_at: Optional[datetime] = None

@dataclass
class DeviceData:
    """Data model for device information"""
    eudamed_uuid: str
    name: str
    company_id: str
    id: Optional[str] = None
    scraping_status: Optional[str] = None

@dataclass
class CertificateData:
    """Data model for certificate information"""
    eudamed_uuid: str
    certificate_number: str
    json_dump: Dict[str, Any]
    id: Optional[str] = None
    scraping_status: Optional[str] = None

@dataclass
class ProcessingStats:
    """Data model for tracking processing statistics"""
    total_companies: int = 0
    processed_companies: int = 0
    total_devices: int = 0
    processed_devices: int = 0
    total_certificates: int = 0
    processed_certificates: int = 0
    total_contacts: int = 0
    processed_contacts: int = 0
    start_time: Optional[datetime] = None
    companies_with_devices: int = 0
    companies_without_devices: int = 0
    companies_with_contacts: int = 0
    companies_without_contacts: int = 0

@dataclass
class PipelineConfig:
    """Configuration for pipeline execution"""
    iso_code: str
    max_companies: Optional[int] = None
    max_devices_per_company: Optional[int] = None
    max_certificates: Optional[int] = None
    page_size: int = 300
    enable_enrichment: bool = False 