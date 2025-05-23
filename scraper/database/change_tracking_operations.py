import uuid
from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime, timezone, timedelta

from models.data_models import ContactData, ContactChangeData
from .contact_operations import ContactDatabaseOperations


class ChangeTrackingOperations(ContactDatabaseOperations):
    """Database operations for contact change tracking"""
    
    def detect_contact_changes(self, existing_contact: Dict[str, Any], new_contact_data: ContactData) -> Tuple[List[str], bool]:
        """
        Detect what fields have changed between existing and new contact data.
        Returns: (list of changed fields, has_changes boolean)
        """
        changed_fields = []
        
        # Define fields to check for changes
        field_mappings = {
            'first_name': 'first_name',
            'family_name': 'family_name',
            'position': 'position',
            'email': 'email',
            'phone': 'phone',
            'city_id': 'city_id',
            'iso_code': 'iso_code'
        }
        
        for db_field, obj_field in field_mappings.items():
            existing_value = existing_contact.get(db_field)
            new_value = getattr(new_contact_data, obj_field, None)
            
            # Normalize values for comparison
            existing_normalized = str(existing_value).strip() if existing_value is not None else ""
            new_normalized = str(new_value).strip() if new_value is not None else ""
            
            if existing_normalized != new_normalized:
                changed_fields.append(db_field)
        
        return changed_fields, len(changed_fields) > 0
    
    def generate_change_summary(self, change_type: str, existing_contact: Optional[Dict[str, Any]], 
                              new_contact_data: ContactData, changed_fields: List[str] = None) -> str:
        """Generate human-readable change summary"""
        if change_type == 'CREATED':
            name = f"{new_contact_data.first_name or ''} {new_contact_data.family_name or ''}".strip()
            position = f" ({new_contact_data.position})" if new_contact_data.position else ""
            return f"New contact added: {name}{position}"
        
        elif change_type == 'DEACTIVATED':
            if existing_contact:
                name = f"{existing_contact.get('first_name', '')} {existing_contact.get('family_name', '')}".strip()
                position = f" ({existing_contact.get('position')})" if existing_contact.get('position') else ""
                return f"Contact no longer found: {name}{position}"
            return "Contact deactivated"
        
        elif change_type == 'UPDATED' and changed_fields:
            name = f"{new_contact_data.first_name or ''} {new_contact_data.family_name or ''}".strip()
            if len(changed_fields) == 1:
                field = changed_fields[0]
                old_val = existing_contact.get(field, '') if existing_contact else ''
                new_val = getattr(new_contact_data, field, '') or ''
                return f"{name} {field} changed from '{old_val}' to '{new_val}'"
            else:
                return f"{name} updated fields: {', '.join(changed_fields)}"
        
        elif change_type == 'REACTIVATED':
            name = f"{new_contact_data.first_name or ''} {new_contact_data.family_name or ''}".strip()
            return f"Contact reactivated: {name}"
        
        return f"Contact {change_type.lower()}"
    
    def log_contact_change(self, change_data: ContactChangeData) -> None:
        """Log a contact change to the history table"""
        change_detected_at = change_data.change_detected_at or datetime.now(timezone.utc)
        
        change_record = {
            "contact_people_id": change_data.contact_people_id,
            "company_id": change_data.company_id,
            "change_type": change_data.change_type,
            "scrape_run_id": change_data.scrape_run_id,
            "change_detected_at": change_detected_at.isoformat(),  # Convert to ISO string
            
            # Previous values
            "previous_first_name": change_data.previous_first_name,
            "previous_family_name": change_data.previous_family_name,
            "previous_position": change_data.previous_position,
            "previous_email": change_data.previous_email,
            "previous_phone": change_data.previous_phone,
            "previous_city_id": change_data.previous_city_id,
            "previous_iso_code": change_data.previous_iso_code,
            
            # New values
            "new_first_name": change_data.new_first_name,
            "new_family_name": change_data.new_family_name,
            "new_position": change_data.new_position,
            "new_email": change_data.new_email,
            "new_phone": change_data.new_phone,
            "new_city_id": change_data.new_city_id,
            "new_iso_code": change_data.new_iso_code,
            
            # Change metadata
            "changed_fields": change_data.changed_fields,
            "change_summary": change_data.change_summary
        }
        
        # Remove None values
        change_record = self._filter_none_values(change_record)
        
        self.supabase.table('eudamed_contact_people_change_history').insert(change_record).execute()
    
    def process_company_contacts_with_change_tracking(self, company_id: str, new_contacts: List[ContactData], 
                                                    scrape_run_id: str) -> Dict[str, int]:
        """
        Process contacts for a company with full change tracking.
        This is the main method that handles the comparison logic.
        """
        stats = {"created": 0, "updated": 0, "deactivated": 0, "unchanged": 0}
        current_time = datetime.now(timezone.utc)
        
        # Get existing active contacts for the company
        existing_contacts = self.get_existing_contacts_for_company(company_id)
        existing_contacts_processed = set()
        
        # Process each new contact from EUDAMED
        for new_contact in new_contacts:
            new_contact.company_id = company_id
            new_contact.last_scraped_at = current_time
            
            # Find matching existing contact
            matching_contact = self.find_matching_contact(new_contact, existing_contacts)
            
            if matching_contact:
                # Contact exists - check for changes
                existing_contacts_processed.add(matching_contact['id'])
                changed_fields, has_changes = self.detect_contact_changes(matching_contact, new_contact)
                
                if has_changes:
                    # Update the contact
                    self.update_contact_record_with_tracking(matching_contact['id'], new_contact, 
                                                           matching_contact, changed_fields, scrape_run_id)
                    stats["updated"] += 1
                else:
                    # Just update the last_scraped_at timestamp
                    self.supabase.table('eudamed_contact_people')\
                        .update({"last_scraped_at": current_time.isoformat()})\
                        .eq('id', matching_contact['id'])\
                        .execute()
                    stats["unchanged"] += 1
            else:
                # New contact - create it
                created_contact = self.create_contact_record_with_tracking(new_contact, scrape_run_id)
                stats["created"] += 1
        
        # Deactivate contacts that were not found in the new EUDAMED data
        for existing_contact in existing_contacts:
            if existing_contact['id'] not in existing_contacts_processed:
                self.deactivate_contact_with_tracking(existing_contact['id'], existing_contact, scrape_run_id)
                stats["deactivated"] += 1
        
        return stats
    
    def create_contact_record_with_tracking(self, contact_data: ContactData, scrape_run_id: str) -> Dict[str, Any]:
        """Create a new contact record with change tracking"""
        # Create the contact record
        created_contact = self.create_contact_record(contact_data)
        
        # Log the creation
        change_data = ContactChangeData(
            contact_people_id=created_contact['id'],
            company_id=contact_data.company_id,
            change_type='CREATED',
            scrape_run_id=scrape_run_id,
            new_first_name=contact_data.first_name,
            new_family_name=contact_data.family_name,
            new_position=contact_data.position,
            new_email=contact_data.email,
            new_phone=contact_data.phone,
            new_city_id=contact_data.city_id,
            new_iso_code=contact_data.iso_code,
            change_summary=self.generate_change_summary('CREATED', None, contact_data)
        )
        
        self.log_contact_change(change_data)
        return created_contact
    
    def update_contact_record_with_tracking(self, contact_id: int, new_contact_data: ContactData, 
                                          existing_contact: Dict[str, Any], changed_fields: List[str], 
                                          scrape_run_id: str) -> None:
        """Update a contact record with change tracking"""
        # Update the contact record
        self.update_contact_record(contact_id, new_contact_data)
        
        # Log the change
        change_data = ContactChangeData(
            contact_people_id=contact_id,
            company_id=new_contact_data.company_id,
            change_type='UPDATED',
            scrape_run_id=scrape_run_id,
            
            # Previous values
            previous_first_name=existing_contact.get('first_name'),
            previous_family_name=existing_contact.get('family_name'),
            previous_position=existing_contact.get('position'),
            previous_email=existing_contact.get('email'),
            previous_phone=existing_contact.get('phone'),
            previous_city_id=existing_contact.get('city_id'),
            previous_iso_code=existing_contact.get('iso_code'),
            
            # New values
            new_first_name=new_contact_data.first_name,
            new_family_name=new_contact_data.family_name,
            new_position=new_contact_data.position,
            new_email=new_contact_data.email,
            new_phone=new_contact_data.phone,
            new_city_id=new_contact_data.city_id,
            new_iso_code=new_contact_data.iso_code,
            
            changed_fields=changed_fields,
            change_summary=self.generate_change_summary('UPDATED', existing_contact, new_contact_data, changed_fields)
        )
        
        self.log_contact_change(change_data)
    
    def deactivate_contact_with_tracking(self, contact_id: int, existing_contact: Dict[str, Any], 
                                       scrape_run_id: str) -> None:
        """Deactivate a contact with change tracking"""
        current_time = datetime.now(timezone.utc)
        
        # Deactivate the contact
        self.supabase.table('eudamed_contact_people')\
            .update({
                "is_active": False, 
                "updated_at": current_time.isoformat(),
                "last_scraped_at": current_time.isoformat()
            })\
            .eq('id', contact_id)\
            .execute()
        
        # Log the deactivation
        change_data = ContactChangeData(
            contact_people_id=contact_id,
            company_id=existing_contact['company_id'],
            change_type='DEACTIVATED',
            scrape_run_id=scrape_run_id,
            
            # Store previous values
            previous_first_name=existing_contact.get('first_name'),
            previous_family_name=existing_contact.get('family_name'),
            previous_position=existing_contact.get('position'),
            previous_email=existing_contact.get('email'),
            previous_phone=existing_contact.get('phone'),
            previous_city_id=existing_contact.get('city_id'),
            previous_iso_code=existing_contact.get('iso_code'),
            
            change_summary=self.generate_change_summary('DEACTIVATED', existing_contact, None)
        )
        
        self.log_contact_change(change_data)
    
    def generate_scrape_run_id(self) -> str:
        """Generate a unique scrape run ID for tracking changes across a scrape session"""
        return str(uuid.uuid4())
    
    def get_contact_change_history(self, company_id: Optional[str] = None, 
                                 contact_id: Optional[int] = None,
                                 change_type: Optional[str] = None,
                                 days_back: int = 30) -> List[Dict[str, Any]]:
        """
        Get contact change history with optional filters
        
        Args:
            company_id: Filter by specific company
            contact_id: Filter by specific contact
            change_type: Filter by change type (CREATED, UPDATED, DEACTIVATED, REACTIVATED)
            days_back: Number of days to look back
        """
        query = self.supabase.table('eudamed_contact_people_change_history')\
            .select('*')\
            .gte('change_detected_at', 
                 (datetime.now(timezone.utc) - timedelta(days=days_back)).isoformat())
        
        if company_id:
            query = query.eq('company_id', company_id)
        if contact_id:
            query = query.eq('contact_people_id', contact_id)
        if change_type:
            query = query.eq('change_type', change_type)
        
        query = query.order('change_detected_at', desc=True)
        
        result = query.execute()
        return result.data or [] 