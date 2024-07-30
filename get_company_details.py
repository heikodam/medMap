import os
import uuid
import requests
from dotenv import load_dotenv
from supabase import create_client, Client

# Load environment variables
load_dotenv()

# Supabase setup
url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url, key)

# EUDAMED API URL
base_url = "https://ec.europa.eu/tools/eudamed/api/actors"

def fetch_company_details(eudamed_uuid):
    response = requests.get(f"{base_url}/{eudamed_uuid}/publicInformation?languageIso2Code=en")
    return response.json()

def get_or_create_city(city_name):
    existing_city = supabase.table('cities').select('id').eq('name', city_name).execute()
    if existing_city.data:
        return existing_city.data[0]['id']
    else:
        new_city = supabase.table('cities').insert({'name': city_name}).execute()
        return new_city.data[0]['id']

def update_company(company_id, details):
    actor_data = details.get('actorDataPublicView', {})
    if not actor_data:
        print(f"Warning: No actorDataPublicView for company {company_id}")
        supabase.table('eudamed_companies').update({"scraping_status": "ERROR"}).eq('id', company_id).execute()
        return

    city_name = actor_data.get('actorAddress', {}).get('cityName', 'Unknown')
    city_id = get_or_create_city(city_name)
    
    company_update = {
        "eudamed_status": actor_data.get('actorStatus', {}).get('code') if actor_data.get('actorStatus') else None,
        "iso_code": actor_data.get('actorAddress', {}).get('country', {}).get('iso2Code'),
        "city_id": city_id,
        "eudamed_type": actor_data.get('type', {}).get('srnCode') if actor_data.get('type') else None,
        "trade_register": actor_data.get('tradeRegister'),
        "eori": actor_data.get('eori'),
        "european_vat_number": actor_data.get('europeanVatNumber'),
        "eudamed_identifier": actor_data.get('eudamedIdentifier'),
        "phone": actor_data.get('telephone'),
        "email": actor_data.get('electronicMail'),
        "website": actor_data.get('website'),
        "validator_name": actor_data.get('validatorName'),
        "validator_uuid": actor_data.get('validatorUuid'),
        "validator_type": actor_data.get('validatorType', {}).get('srnCode') if actor_data.get('validatorType') else None,
        "validator_srn": actor_data.get('validatorSrn'),
        "validator_email": actor_data.get('validatorEmail'),
        "validator_phone": actor_data.get('validatorTelephone'),
        "scraping_status": "GOT_COMPANY_DETAILS"
    }
    
    # Remove None values from the update dictionary
    company_update = {k: v for k, v in company_update.items() if v is not None}
    
    supabase.table('eudamed_companies').update(company_update).eq('id', company_id).execute()

def insert_contact_person(company_id, contact):
    existing_contact = supabase.table('eudamed_contactpeople').select('id')\
        .eq('company_id', company_id)\
        .eq('email', contact.get('electronicMail'))\
        .eq('phone', contact.get('telephone'))\
        .eq('first_name', contact.get('firstName'))\
        .eq('family_name', contact.get('familyName'))\
        .eq('position', contact.get('position'))\
        .execute()
    
    if existing_contact.data:
        print(f"Contact already exists for company {company_id} with email {contact.get('electronicMail')} and phone {contact.get('telephone')}")
        return

    geo_address = contact.get('geographicalAddress', {})
    city_name = geo_address.get('cityName', 'Unknown')
    city_id = get_or_create_city(city_name)
    
    new_contact = {
        "company_id": company_id,
        "first_name": contact.get('firstName'),
        "family_name": contact.get('familyName'),
        "email": contact.get('electronicMail'),
        "phone": contact.get('telephone'),
        "position": contact.get('position'),
        "city_id": city_id,
        "iso_code": geo_address.get('country', {}).get('iso2Code')
    }
    
    # Remove None values from the new_contact dictionary
    new_contact = {k: v for k, v in new_contact.items() if v is not None}
    
    supabase.table('eudamed_contactpeople').insert(new_contact).execute()

def process_company(company):
    details = fetch_company_details(company['eudamed_uuid'])
    
    # Check for error response
    if 'httpStatusCode' in details:
        print(f"Error fetching details for company {company['id']}: {details['httpStatus']}")
        supabase.table('eudamed_companies').update({"scraping_status": "ERROR"}).eq('id', company['id']).execute()
        return

    actor_data = details.get('actorDataPublicView')
    if actor_data:
        regulatory_compliance = actor_data.get('regulatoryComplianceResponsibles')
        if regulatory_compliance is not None:
            for contact in regulatory_compliance:
                insert_contact_person(company['id'], contact)
        else:
            print(f"No regulatory compliance responsibles for company {company['id']}")
        
        update_company(company['id'], details)
    else:
        print(f"Warning: No actorDataPublicView for company {company['id']}")
        supabase.table('eudamed_companies').update({"scraping_status": "ERROR"}).eq('id', company['id']).execute()

def fetch_companies(page=0, page_size=1000):
    return supabase.table('eudamed_companies').select('*').eq('scraping_status', 'GOT_COMPANY_ID').range(page*page_size, (page+1)*page_size-1).execute()

def process_all_companies():
    page = 0
    while True:
        companies = fetch_companies(page)
        if not companies.data:
            break
        
        for company in companies.data:
            print(f"Processing company: {company['name']} - {company['id']}")
            process_company(company)
        
        page += 1
    
    print("Finished processing all companies.")

# Run the script
process_all_companies()


# Pseudo code


# Fetch companies from database - should happen in batches

# For eacht company, fetch the details: https://ec.europa.eu/tools/eudamed/api/actors/fc9cb447-d565-4643-980b-196ef56fbb6e/publicInformation?languageIso2Code=en

# Insert the details into the database


# Table - matching keys
# eudamed  -  supabase
# 
# actorStatus.code - eudamed_status
# actorAddress.country.iso2Code - iso_code
# actorAddress.cityName - city_id -> foreign key to cities table (id, name) insert if not exists else get id
# type.srnCode - eudamed_type
# actorStatus.code - eudamed_status
# tradeRegister - trade_register
# eori - eori
# europeanVatNumber - european_vat_number
# eudamedIdentifier - eudamed_identifier
# tradeRegister - trade_register
# telephone - phone
# electronicMail - email
# website - website
# validatorName - validator_name
# validatorUuid - validator_uuid
# validatorType.srnCode - validator_type
# validatorSrn - validator_srn
# validatorEmail - validator_email
# validatorTelephone - validator_phone



# table: eudamed_contactpeople
# eudamed  - supabase

# company_id - is the id of the company in the eudamed_companies table
# firstName - first_name
# familyName - family_name
# electronicMail - email
# telephone - phone
# position - position
# geographicalAddress.cityName - city_id -> foreign key to cities table (id, name) insert if not exists else get id
# geographicalAddress.country.iso2Code - iso_code (also a forgein key to the countries table with all iso codes and names)

