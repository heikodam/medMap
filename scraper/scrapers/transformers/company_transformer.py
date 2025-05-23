import json
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

from models.data_models import ContactData


class CompanyDataTransformer:
    """Handles transformation of raw company API data into structured formats"""
    
    @staticmethod
    def safe_get(data: Dict[str, Any], *keys) -> Any:
        """Safely get nested dictionary values"""
        for key in keys:
            if data is None or not isinstance(data, dict):
                return None
            data = data.get(key)
        return data
    
    @classmethod
    def transform_company_details(cls, raw_details: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform raw company details from EUDAMED API into database format.
        
        Args:
            raw_details: Raw response from EUDAMED company details API
            
        Returns:
            Dictionary with transformed company data ready for database
        """
        actor_data = raw_details.get('actorDataPublicView', {})
        
        if not actor_data:
            raise ValueError("No actorDataPublicView found in company details")
        
        current_timestamp = datetime.now(timezone.utc).isoformat()
        
        # Transform the data
        transformed_data = {
            "json_dump": json.dumps(raw_details),
            "importers": json.dumps(raw_details.get('importers')),
            "non_eu_manufacturers": json.dumps(raw_details.get('nonEuManufacturers')),
            "eudamed_status": cls.safe_get(actor_data, 'actorStatus', 'code'),
            "iso_code": cls.safe_get(actor_data, 'actorAddress', 'country', 'iso2Code'),
            "eudamed_type": cls.safe_get(actor_data, 'type', 'srnCode'),
            "trade_register": actor_data.get('tradeRegister'),
            "eori": actor_data.get('eori'),
            "european_vat_number": actor_data.get('europeanVatNumber'),
            "eudamed_identifier": actor_data.get('eudamedIdentifier'),
            "phone": actor_data.get('telephone'),
            "email": actor_data.get('electronicMail'),
            "original_website": actor_data.get('website'),
            "validator_name": actor_data.get('validatorName'),
            "validator_uuid": actor_data.get('validatorUuid'),
            "validator_type": cls.safe_get(actor_data, 'validatorType', 'srnCode'),
            "validator_srn": actor_data.get('validatorSrn'),
            "validator_email": actor_data.get('validatorEmail'),
            "validator_phone": actor_data.get('validatorTelephone'),
            "actor_ulid": actor_data.get('ulid'),
            "actor_version_number": actor_data.get('versionNumber'),
            "actor_version_state": actor_data.get('versionState'),
            "actor_latest_version": actor_data.get('latestVersion'),
            "actor_last_update_date": actor_data.get('lastUpdateDate'),
            "actor_names": json.dumps(actor_data.get('name')),
            "actor_abbreviated_names": json.dumps(actor_data.get('abbreviatedName')),
            "actor_status_from_date": actor_data.get('actorStatusFromDate'),
            "actor_country_name": cls.safe_get(actor_data, 'country', 'name'),
            "actor_country_type": cls.safe_get(actor_data, 'country', 'type'),
            "actor_geographical_address": actor_data.get('geographicalAddress'),
            "european_vat_number_applicable": actor_data.get('europeanVatNumberApplicable'),
            "organization_identification_documents": json.dumps(actor_data.get('organizationIdentificationDocuments')),
            "authorised_representatives": json.dumps(actor_data.get('authorisedRepresentatives')),
            "competent_authority_responsibility": actor_data.get('competentAuthorityResponsibility'),
            "actor_address": json.dumps(actor_data.get('actorAddress')),
            "validator_address": json.dumps(actor_data.get('validatorAddress')),
            "regulatory_compliance_responsibles": json.dumps(actor_data.get('regulatoryComplianceResponsibles')),
            "legislation_links": json.dumps(actor_data.get('legislationLinks')),
            "latest_subsidiary": json.dumps(actor_data.get('latestSubsidiary')),
            "certificates": json.dumps(actor_data.get('certificates')),
            "latest_version": actor_data.get('latestVersion'),
            "version_number": actor_data.get('versionNumber'),
            "version_state": json.dumps(actor_data.get('versionState')),
            "last_update_date": actor_data.get('lastUpdateDate'),
            "accuracy_data": json.dumps(actor_data.get('accuracyData')),
            "last_accuracy_date": actor_data.get('lastAccuracyDate'),
            "scraping_status": "GOT_COMPANY_DETAILS",
            "medmap_last_update": current_timestamp
        }
        
        # Remove None values
        return {k: v for k, v in transformed_data.items() if v is not None}
    
    @classmethod
    def extract_contact_data(cls, raw_details: Dict[str, Any], company_id: str) -> List[ContactData]:
        """
        Extract contact information from company details.
        
        Args:
            raw_details: Raw response from EUDAMED company details API
            company_id: ID of the company these contacts belong to
            
        Returns:
            List of ContactData objects
        """
        contacts = []
        actor_data = raw_details.get('actorDataPublicView', {})
        
        regulatory_compliance = actor_data.get('regulatoryComplianceResponsibles')
        if regulatory_compliance:
            for contact in regulatory_compliance:
                geo_address = contact.get('geographicalAddress', {})
                
                contact_data = ContactData(
                    company_id=company_id,
                    first_name=contact.get('firstName'),
                    family_name=contact.get('familyName'),
                    email=contact.get('electronicMail'),
                    phone=contact.get('telephone'),
                    position=contact.get('position'),
                    iso_code=cls.safe_get(geo_address, 'country', 'iso2Code')
                )
                
                contacts.append(contact_data)
        
        return contacts
    
    @classmethod
    def get_city_name_from_contact(cls, contact: Dict[str, Any]) -> str:
        """Extract city name from contact data"""
        geo_address = contact.get('geographicalAddress', {})
        return geo_address.get('cityName', 'Unknown') 