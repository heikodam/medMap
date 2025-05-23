from typing import Optional, Dict, Any, List
from datetime import datetime, timezone

from models.data_models import ContactData
from .base_database_operations import BaseDatabaseOperations


class ContactDatabaseOperations(BaseDatabaseOperations):
    """Database operations specific to contacts"""
    
    def get_contact_identity_key(self, contact_data: ContactData) -> str:
        """
        Generate a unique identity key for contact identification.
        Primary strategy: first_name + family_name + email + company_id
        """
        first_name = (contact_data.first_name or "").strip().lower()
        family_name = (contact_data.family_name or "").strip().lower()
        email = (contact_data.email or "").strip().lower()
        company_id = str(contact_data.company_id)
        
        return f"{first_name}|{family_name}|{email}|{company_id}"
    
    def get_existing_contacts_for_company(self, company_id: str) -> List[Dict[str, Any]]:
        """Get all active contacts for a company"""
        result = self.supabase.table('eudamed_contact_people')\
            .select('*')\
            .eq('company_id', company_id)\
            .eq('is_active', True)\
            .execute()
        return result.data or []
    
    def find_matching_contact(self, contact_data: ContactData, existing_contacts: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """
        Find matching contact using the identification strategy:
        1. Primary: first_name + family_name + email + company_id
        2. Secondary: first_name + family_name + company_id (if email missing)
        3. Tertiary: email + company_id (fallback)
        """
        target_key = self.get_contact_identity_key(contact_data)
        
        for existing in existing_contacts:
            existing_contact_data = ContactData(
                company_id=existing['company_id'],
                first_name=existing.get('first_name'),
                family_name=existing.get('family_name'),
                email=existing.get('email')
            )
            existing_key = self.get_contact_identity_key(existing_contact_data)
            
            if target_key == existing_key:
                return existing
        
        # Secondary strategy: match by name + company if email is missing from new data
        if not contact_data.email:
            for existing in existing_contacts:
                if (existing.get('first_name', '').strip().lower() == (contact_data.first_name or '').strip().lower() and
                    existing.get('family_name', '').strip().lower() == (contact_data.family_name or '').strip().lower()):
                    return existing
        
        # Tertiary strategy: match by email + company if names are missing from new data
        if contact_data.email and not (contact_data.first_name and contact_data.family_name):
            for existing in existing_contacts:
                if existing.get('email', '').strip().lower() == contact_data.email.strip().lower():
                    return existing
        
        return None
    
    def check_contact_exists(self, contact_data: ContactData) -> Optional[Dict[str, Any]]:
        """Check if a contact person exists in the database based on key fields"""
        # Use the new identification strategy
        existing_contacts = self.get_existing_contacts_for_company(contact_data.company_id)
        return self.find_matching_contact(contact_data, existing_contacts)
    
    def create_contact_record(self, contact_data: ContactData) -> Dict[str, Any]:
        """Create a new contact person record in the database"""
        current_time = datetime.now(timezone.utc)
        
        # Remove None values from the contact_data
        contact_dict = {
            "company_id": contact_data.company_id,
            "is_active": True,
            "created_at": current_time.isoformat(),
            "updated_at": current_time.isoformat(),
            "last_scraped_at": current_time.isoformat()
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
    
    def update_contact_record(self, contact_id: int, contact_data: ContactData) -> Dict[str, Any]:
        """Update an existing contact person record"""
        current_time = datetime.now(timezone.utc)
        
        # Build update dictionary with only non-None values
        update_dict = {
            "updated_at": current_time.isoformat(),
            "last_scraped_at": current_time.isoformat()
        }
        
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