import os
import asyncio
import aiohttp
from dotenv import load_dotenv
from supabase import create_client, Client

# Load environment variables
load_dotenv()

# Supabase setup
url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url, key)

# EUDAMED API URL
base_url = "https://ec.europa.eu/tools/eudamed/api/devices/basicUdiData/udiDiData"

async def fetch_products(batch_size=1000, from_=0):
    return supabase.table('eudamed_products') \
        .select("id", "eudamed_uuid") \
        .eq("scraping_status", "GOT_COMPANY_DEVICES") \
        .range(from_, from_ + batch_size - 1) \
        .execute()

async def fetch_device_details(session, eudamed_uuid):
    url = f"{base_url}/{eudamed_uuid}?languageIso2Code=en"
    
    for attempt in range(2):  # Try twice
        try:
            async with session.get(url) as response:
                return await response.json()
        except aiohttp.ClientError:  # This catches connection refusals and other client errors
            if attempt == 0:  # If this is the first attempt
                print(f"Connection refused for {eudamed_uuid}. Retrying in 5 seconds...")
                await asyncio.sleep(5)  # Wait for 5 seconds before retrying
            else:
                print(f"Connection refused again for {eudamed_uuid}. Skipping this device.")
                return None  # Return None to indicate failure
    
    return None  # This line shouldn't be reached, but it's here for completeness

async def update_product(product_id, details):
    def safe_get(d, *keys):
        for key in keys:
            if d is None or not isinstance(d, dict):
                return None
            d = d.get(key)
        return d

    update_data = {
        "scraping_status": "GOT_COMPANY_DEVICES_DETAILS",
        "eudamed_ulid": safe_get(details, "ulid"),
        "udi_di_data": safe_get(details, "udiDiData"),
        "manufacturer_eudamed_uuid": safe_get(details, "manufacturer", "uuid"),
        "manufacturer_ulid": safe_get(details, "manufacturer", "ulid"),
        "manufacturer_version_number": safe_get(details, "manufacturer", "versionNumber"),
        "manufacturer_version_state": safe_get(details, "manufacturer", "versionState", "code"),
        "manufacturer_latest_version": safe_get(details, "manufacturer", "latestVersion"),
        "manufacturer_last_update_date": safe_get(details, "manufacturer", "lastUpdateDate"),
        "manufacturer_name": safe_get(details, "manufacturer", "name"),
        "manufacturer_actor_type": safe_get(details, "manufacturer", "actorType", "code"),
        "manufacturer_status": safe_get(details, "manufacturer", "status", "code"),
        "manufacturer_country_iso2_code": safe_get(details, "manufacturer", "countryIso2Code"),
        "manufacturer_country_name": safe_get(details, "manufacturer", "countryName"),
        "manufacturer_country_type": safe_get(details, "manufacturer", "countryType"),
        "manufacturer_geographical_address": safe_get(details, "manufacturer", "geographicalAddress"),
        "manufacturer_electronic_mail": safe_get(details, "manufacturer", "electronicMail"),
        "manufacturer_telephone": safe_get(details, "manufacturer", "telephone"),
        "manufacturer_srn": safe_get(details, "manufacturer", "srn"),
        "ar_non_eu_manufacturer_uuid": safe_get(details, "authorisedRepresentative", "nonEuManufacturerUuid"),
        "ar_uuid": safe_get(details, "authorisedRepresentative", "authorisedRepresentativeUuid"),
        "ar_ulid": safe_get(details, "authorisedRepresentative", "authorisedRepresentativeUlid"),
        "ar_name": safe_get(details, "authorisedRepresentative", "name"),
        "ar_srn": safe_get(details, "authorisedRepresentative", "srn"),
        "ar_address": safe_get(details, "authorisedRepresentative", "address"),
        "ar_country_name": safe_get(details, "authorisedRepresentative", "countryName"),
        "ar_email": safe_get(details, "authorisedRepresentative", "email"),
        "ar_telephone": safe_get(details, "authorisedRepresentative", "telephone"),
        "ar_version_number": safe_get(details, "authorisedRepresentative", "versionNumber"),
        "ar_version_state": safe_get(details, "authorisedRepresentative", "versionState", "code"),
        "ar_latest_version": safe_get(details, "authorisedRepresentative", "latestVersion"),
        "ar_last_update_date": safe_get(details, "authorisedRepresentative", "lastUpdateDate"),
        "active": safe_get(details, "active"),
        "administering_medicine": safe_get(details, "administeringMedicine"),
        "animal_tissues": safe_get(details, "animalTissues"),
        "nb_decision": safe_get(details, "nbDecision"),
        "basic_udi_uuid": safe_get(details, "basicUdi", "uuid"),
        "basic_udi_code": safe_get(details, "basicUdi", "code"),
        "basic_udi_issuing_agency": safe_get(details, "basicUdi", "issuingAgency", "code"),
        "basic_udi_type": safe_get(details, "basicUdi", "type"),
        "device_criterion": safe_get(details, "deviceCriterion"),
        "device_model": safe_get(details, "deviceModel"),
        "device_model_applicable": safe_get(details, "deviceModelApplicable"),
        "device_name": safe_get(details, "deviceName"),
        "human_tissues": safe_get(details, "humanTissues"),
        "human_product": safe_get(details, "humanProduct"),
        "medicinal_product": safe_get(details, "medicinalProduct"),
        "implantable": safe_get(details, "implantable"),
        "legislation": safe_get(details, "legislation", "code"),
        "measuring_function": safe_get(details, "measuringFunction"),
        "reusable": safe_get(details, "reusable"),
        "risk_class": safe_get(details, "riskClass", "code"),
        "special_device_type_applicable": safe_get(details, "specialDeviceTypeApplicable"),
        "version_date": safe_get(details, "versionDate"),
        "version_state": safe_get(details, "versionState", "code"),
        "latest_version": safe_get(details, "latestVersion"),
        "version_number": safe_get(details, "versionNumber"),
    }
    
    # Remove None values from the update dictionary
    update_data = {k: v for k, v in update_data.items() if v is not None}
    
    supabase.table('eudamed_products').update(update_data).eq('id', product_id).execute()
    # print(f"Updated product: {product_id}")

async def process_product(session, product):
    details = await fetch_device_details(session, product['eudamed_uuid'])
    if details is not None:
        await update_product(product['id'], details)
    else:
        print(f"Skipping update for product {product['id']} due to connection issues.")

async def process_products_batch(products):
    async with aiohttp.ClientSession() as session:
        tasks = [process_product(session, product) for product in products]
        await asyncio.gather(*tasks)

async def process_all_products():
    batch_size = 50
    from_ = 0
    total_processed = 0

    while True:
        products = await fetch_products(batch_size, from_)
        
        if not products.data:
            print("No products found.")
            break
        
        await process_products_batch(products.data)
        
        total_processed += len(products.data)
        # from_ += batch_size
        
        print(f"Processed {total_processed} products so far.")
        
        if len(products.data) < batch_size:
            break
        
    print(f"Finished processing all products. Total processed: {total_processed}")

# Run the script
asyncio.run(process_all_products())








# eudamed_identifier - eudamed_identifier 
# uuid - eudamed_uuid 
# scraping_status - scraping_status
# ulid - eudamed_ulid
# udiDiData - udi_di_data
# manufacturer.uuid - manufacturer_eudamed_uuid
# manufacturer.ulid - manufacturer_ulid
# manufacturer.versionNumber - manufacturer_version_number
# manufacturer.versionState.code - manufacturer_version_state
# manufacturer.latestVersion - manufacturer_latest_version
# manufacturer.lastUpdateDate - manufacturer_last_update_date
# manufacturer.name - manufacturer_name
# manufacturer.actorType.code - manufacturer_actor_type
# manufacturer.status.code - manufacturer_status
# manufacturer.countryIso2Code - manufacturer_country_iso2_code
# manufacturer.countryName - manufacturer_country_name
# manufacturer.countryType - manufacturer_country_type
# manufacturer.geographicalAddress - manufacturer_geographical_address
# manufacturer.electronicMail - manufacturer_electronic_mail
# manufacturer.telephone - manufacturer_telephone
# manufacturer.srn - manufacturer_srn
# authorisedRepresentative.nonEuManufacturerUuid - ar_non_eu_manufacturer_uuid
# authorisedRepresentative.authorisedRepresentativeUuid - ar_uuid
# authorisedRepresentative.authorisedRepresentativeUlid - ar_ulid
# authorisedRepresentative.name - ar_name
# authorisedRepresentative.srn - ar_srn
# authorisedRepresentative.address - ar_address
# authorisedRepresentative.countryName - ar_country_name
# authorisedRepresentative.email - ar_email
# authorisedRepresentative.telephone - ar_telephone
# authorisedRepresentative.versionNumber - ar_version_number
# authorisedRepresentative.versionState.code - ar_version_state
# authorisedRepresentative.latestVersion - ar_latest_version
# authorisedRepresentative.lastUpdateDate - ar_last_update_date
# active - active
# administeringMedicine - administering_medicine
# animalTissues - animal_tissues
# nbDecision - nb_decision
# basicUdi.uuid - basic_udi_uuid
# basicUdi.code - basic_udi_code
# basicUdi.issuingAgency.code - basic_udi_issuing_agency
# basicUdi.type - basic_udi_type
# deviceCriterion - device_criterion
# deviceModel - device_model
# deviceModelApplicable - device_model_applicable
# deviceName - device_name
# humanTissues - human_tissues
# humanProduct - human_product
# medicinalProduct - medicinal_product
# implantable - implantable
# legislation.code - legislation
# measuringFunction - measuring_function
# reusable - reusable
# riskClass.code - risk_class
# specialDeviceTypeApplicable - special_device_type_applicable
# versionDate - version_date
# versionState.code - version_state
# latestVersion - latest_version
# versionNumber - version_number
