from typing import Dict, Any, List, Optional
from models.data_models import ContactData
from database.operations import DatabaseOperations
from ui.progress_tracker import ProgressTracker

class ContactProcessor:
    """Handles contact person extraction and processing operations"""
    
    def __init__(self, progress_tracker: ProgressTracker):
        self.db = DatabaseOperations()
        self.progress = progress_tracker
    
    def extract_contacts_from_company_details(self, company_id: str, details: Dict[str, Any]) -> List[ContactData]:
        """
        Extract all contact persons from company details JSON.
        Returns a list of ContactData objects.
        """
        contacts = []
        actor_data = details.get('actorDataPublicView', {})
        
        if not actor_data:
            self.progress.display_status_update(
                f"No actorDataPublicView found for company {company_id}", 
                "yellow"
            )
            return contacts
        
        # Extract regulatory compliance responsibles
        regulatory_compliance = actor_data.get('regulatoryComplianceResponsibles')
        if regulatory_compliance and isinstance(regulatory_compliance, list):
            for contact_info in regulatory_compliance:
                contact = self._create_contact_data_from_json(company_id, contact_info)
                if contact:
                    contacts.append(contact)
        
        # Extract authorized representatives contacts if they exist
        auth_representatives = actor_data.get('authorisedRepresentatives')
        if auth_representatives and isinstance(auth_representatives, list):
            for auth_rep in auth_representatives:
                # Check if there are contact details in the authorized representative
                if isinstance(auth_rep, dict) and 'contactPersons' in auth_rep:
                    contact_persons = auth_rep.get('contactPersons', [])
                    for contact_info in contact_persons:
                        contact = self._create_contact_data_from_json(company_id, contact_info)
                        if contact:
                            contacts.append(contact)
        
        return contacts
    
    def _create_contact_data_from_json(self, company_id: str, contact_info: Dict[str, Any]) -> Optional[ContactData]:
        """
        Create a ContactData object from JSON contact information.
        Returns None if contact_info is invalid or empty.
        """
        if not isinstance(contact_info, dict):
            return None
        
        # Extract geographical address info for city and country
        geo_address = contact_info.get('geographicalAddress', {})
        city_name = geo_address.get('cityName')
        iso_code = None
        
        if 'country' in geo_address and isinstance(geo_address['country'], dict):
            iso_code = geo_address['country'].get('iso2Code')
        
        # Create ContactData object
        contact = ContactData(
            company_id=company_id,
            first_name=contact_info.get('firstName'),
            family_name=contact_info.get('familyName'),
            email=contact_info.get('electronicMail'),
            phone=contact_info.get('telephone'),
            position=contact_info.get('position'),
            iso_code=iso_code
        )
        
        # Only return contact if it has at least some meaningful data
        if any([contact.first_name, contact.family_name, contact.email, contact.phone]):
            return contact
        
        return None
    
    async def process_contacts_for_company(self, company_id: str, details: Dict[str, Any]) -> int:
        """
        Process all contacts for a company using the new change tracking functionality.
        Returns the number of contacts processed.
        """
        contacts = self.extract_contacts_from_company_details(company_id, details)
        
        if not contacts:
            self.progress.display_status_update(
                "No contact persons found for this company", 
                "blue"
            )
            return 0
        
        # Process city information for each contact
        for contact in contacts:
            try:
                # Get or create city if city name is available
                city_name = self._extract_city_name_for_contact(details, contact)
                if city_name:
                    contact.city_id = await self.db.get_or_create_city(city_name)
            except Exception as e:
                self.progress.display_status_update(
                    f"Error processing city for contact {contact.first_name} {contact.family_name}: {str(e)}", 
                    "yellow"
                )
        
        # Generate scrape run ID for this processing session
        scrape_run_id = self.db.generate_scrape_run_id()
        
        # Use the new change tracking functionality
        try:
            stats = self.db.process_company_contacts_with_change_tracking(
                company_id=company_id,
                new_contacts=contacts,
                scrape_run_id=scrape_run_id
            )
            
            # Display detailed stats
            total_processed = stats['created'] + stats['updated'] + stats['unchanged']
            
            if stats['created'] > 0:
                self.progress.display_status_update(
                    f"✅ Created {stats['created']} new contact(s)", 
                    "bold green"
                )
            
            if stats['updated'] > 0:
                self.progress.display_status_update(
                    f"🔄 Updated {stats['updated']} existing contact(s)", 
                    "bold blue"
                )
            
            if stats['deactivated'] > 0:
                self.progress.display_status_update(
                    f"❌ Deactivated {stats['deactivated']} contact(s) no longer found", 
                    "bold red"
                )
            
            if stats['unchanged'] > 0:
                self.progress.display_status_update(
                    f"⚪ {stats['unchanged']} contact(s) unchanged", 
                    "blue"
                )
            
            # Show change summary if there were any changes
            total_changes = stats['created'] + stats['updated'] + stats['deactivated']
            if total_changes > 0:
                self.progress.display_status_update(
                    f"📝 {total_changes} contact change(s) logged (Run ID: {scrape_run_id[:8]}...)", 
                    "bold cyan"
                )
            
            self.progress.display_status_update(
                f"Successfully processed {total_processed} contact(s) with change tracking", 
                "bold green"
            )
            
            return total_processed
            
        except Exception as e:
            self.progress.display_status_update(
                f"Error processing contacts with change tracking: {str(e)}", 
                "red"
            )
            return 0

    def _extract_city_name_for_contact(self, details: Dict[str, Any], contact: ContactData) -> Optional[str]:
        """
        Extract city name for a specific contact from the company details JSON.
        This is a helper method to get the city name associated with a contact.
        """
        actor_data = details.get('actorDataPublicView', {})
        
        # Try to find the contact in regulatory compliance responsibles
        regulatory_compliance = actor_data.get('regulatoryComplianceResponsibles', [])
        for contact_info in regulatory_compliance:
            if (contact_info.get('firstName') == contact.first_name and 
                contact_info.get('familyName') == contact.family_name and
                contact_info.get('electronicMail') == contact.email):
                geo_address = contact_info.get('geographicalAddress', {})
                return geo_address.get('cityName')
        
        # Try to find in authorized representatives
        auth_representatives = actor_data.get('authorisedRepresentatives', [])
        for auth_rep in auth_representatives:
            if isinstance(auth_rep, dict) and 'contactPersons' in auth_rep:
                contact_persons = auth_rep.get('contactPersons', [])
                for contact_info in contact_persons:
                    if (contact_info.get('firstName') == contact.first_name and 
                        contact_info.get('familyName') == contact.family_name and
                        contact_info.get('electronicMail') == contact.email):
                        geo_address = contact_info.get('geographicalAddress', {})
                        return geo_address.get('cityName')
        
        return None 