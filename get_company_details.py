import os
import uuid
import asyncio
import aiohttp
from dotenv import load_dotenv
from supabase import create_client, Client
import json

# Load environment variables
load_dotenv()

# Supabase setup
url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url, key)

# EUDAMED API URL
base_url = "https://ec.europa.eu/tools/eudamed/api/actors"

async def fetch_company_details(session, eudamed_uuid):
    url = f"{base_url}/{eudamed_uuid}/publicInformation?languageIso2Code=en"
    
    for attempt in range(3):  # Try up to 3 times
        try:
            async with session.get(url) as response:
                return await response.json()
        except aiohttp.ClientError:
            if attempt < 2:  # If this is not the last attempt
                print(f"Connection error for {eudamed_uuid}. Retrying in 5 seconds...")
                await asyncio.sleep(5)  # Wait for 5 seconds before retrying
            else:
                print(f"Connection failed after 3 attempts for {eudamed_uuid}. Skipping this company.")
                return None
    
    return None

async def get_or_create_city(city_name):
    existing_city = await supabase.table('cities').select('id').eq('name', city_name).execute()
    if existing_city.data:
        return existing_city.data[0]['id']
    else:
        new_city = await supabase.table('cities').insert({'name': city_name}).execute()
        return new_city.data[0]['id']

async def update_company(company_id, details):
    actor_data = details.get('actorDataPublicView', {})
    if not actor_data:
        print(f"Warning: No actorDataPublicView for company {company_id}")
        await supabase.table('eudamed_companies').update({"scraping_status": "ERROR"}).eq('id', company_id).execute()
        return

    city_name = actor_data.get('actorAddress', {}).get('cityName', 'Unknown')
    city_id = await get_or_create_city(city_name)
    
    company_update = {
        "json_dump": json.dumps(details),
        "importers": json.dumps(details.get('importers')),
        "non_eu_manufacturers": json.dumps(details.get('nonEuManufacturers')),
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
        "original_website": actor_data.get('website'),
        "validator_name": actor_data.get('validatorName'),
        "validator_uuid": actor_data.get('validatorUuid'),
        "validator_type": actor_data.get('validatorType', {}).get('srnCode') if actor_data.get('validatorType') else None,
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
        "actor_country_name": actor_data.get('country', {}).get('name'),
        "actor_country_type": actor_data.get('country', {}).get('type'),
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
        "scraping_status": "GOT_COMPANY_DETAILS"
    }
    
    # Remove None values from the update dictionary
    company_update = {k: v for k, v in company_update.items() if v is not None}
    
    await supabase.table('eudamed_companies').update(company_update).eq('id', company_id).execute()

async def insert_contact_person(company_id, contact):
    existing_contact = await supabase.table('eudamed_contactpeople').select('id')\
        .eq('company_id', company_id)\
        .eq('email', contact.get('electronicMail'))\
        .eq('phone', contact.get('telephone'))\
        .eq('first_name', contact.get('firstName'))\
        .eq('family_name', contact.get('familyName'))\
        .eq('position', contact.get('position'))\
        .execute()
    
    if existing_contact.data:
        return

    geo_address = contact.get('geographicalAddress', {})
    city_name = geo_address.get('cityName', 'Unknown')
    city_id = await get_or_create_city(city_name)
    
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
    
    await supabase.table('eudamed_contactpeople').insert(new_contact).execute()

async def process_company(session, company):
    details = await fetch_company_details(session, company['eudamed_uuid'])
    
    if details is None:
        print(f"Error fetching details for company {company['id']}")
        await supabase.table('eudamed_companies').update({"scraping_status": "ERROR"}).eq('id', company['id']).execute()
        return

    # Check for error response
    if 'httpStatusCode' in details:
        print(f"Error fetching details for company {company['id']}: {details['httpStatus']}")
        await supabase.table('eudamed_companies').update({"scraping_status": "ERROR"}).eq('id', company['id']).execute()
        return

    actor_data = details.get('actorDataPublicView')
    if actor_data:
        regulatory_compliance = actor_data.get('regulatoryComplianceResponsibles')
        if regulatory_compliance is not None:
            for contact in regulatory_compliance:
                await insert_contact_person(company['id'], contact)
        else:
            print(f"No regulatory compliance responsibles for company {company['id']}")
        
        await update_company(company['id'], details)
    else:
        print(f"Warning: No actorDataPublicView for company {company['id']}")
        await supabase.table('eudamed_companies').update({"scraping_status": "ERROR"}).eq('id', company['id']).execute()

async def fetch_companies():
    response = supabase.table('eudamed_companies')\
        .select('*')\
        .neq("scraping_status", "GOT_COMPANY_DETAILS")\
        .execute()
    return response.data

async def process_all_companies():
    async with aiohttp.ClientSession() as session:
        while True:
            companies = await asyncio.to_thread(fetch_companies)
            if not companies:
                break
            
            tasks = []
            for company in companies[:5]:  # Process 5 companies at a time
                print(f"Processing company: {company['name']} - {company['id']}")
                tasks.append(process_company(session, company))
            
            await asyncio.gather(*tasks)
    
    print("Finished processing all companies.")

# Run the script
asyncio.run(process_all_companies())


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

