import os
import uuid
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
base_url = "https://ec.europa.eu/tools/eudamed/api/devices/udiDiData"

def fetch_companies(batch_size=1000, from_=0):
    return supabase.table('eudamed_companies') \
        .select("id", "eudamed_identifier") \
        .eq("scraping_status", "GOT_COMPANY_DETAILS") \
        .range(from_, from_ + batch_size - 1) \
        .execute()

async def fetch_devices(session, srn, page=0, page_size=300):
    params = {
        "page": page,
        "pageSize": page_size,
        "size": page_size,
        "iso2Code": "en",
        "srn": srn,
        "languageIso2Code": "en"
    }
    async with session.get(base_url, params=params) as response:
        return await response.json()

async def insert_or_update_device(device, company_id):
    eudamed_uuid = device['uuid']
    
    # Check if the device already exists
    existing_device = supabase.table('eudamed_products') \
        .select("id") \
        .eq("eudamed_uuid", eudamed_uuid) \
        .execute()

    if existing_device.data:
        # Update existing device
        updated_device = {
            "name": device['tradeName'],
            "company_id": company_id,
            "scraping_status": "GOT_COMPANY_DEVICES"
        }
        supabase.table('eudamed_products') \
            .update(updated_device) \
            .eq("eudamed_uuid", eudamed_uuid) \
            .execute()
        print(f"Updated existing device: {eudamed_uuid}")
    else:
        # Insert new device
        new_device = {
            "id": str(uuid.uuid4()),
            "name": device['tradeName'],
            "company_id": company_id,
            "eudamed_uuid": eudamed_uuid,
            "scraping_status": "GOT_COMPANY_DEVICES"
        }
        supabase.table('eudamed_products').insert(new_device).execute()
        print(f"Inserted new device: {eudamed_uuid}")

async def process_company_devices(session, company):
    page = 0
    while True:
        data = await fetch_devices(session, company['eudamed_identifier'], page)
        
        tasks = [insert_or_update_device(device, company['id']) for device in data['content']]
        await asyncio.gather(*tasks)
        
        if data['last']:
            break
        
        page += 1
    
    # Update company scraping status
    supabase.table('eudamed_companies') \
        .update({"scraping_status": "GOT_COMPANY_DEVICES"}) \
        .eq("id", company['id']) \
        .execute()

async def process_companies_batch(companies):
    async with aiohttp.ClientSession() as session:
        tasks = [process_company_devices(session, company) for company in companies]
        await asyncio.gather(*tasks)

async def process_all_companies():
    batch_size = 50
    from_ = 0
    total_processed = 0

    while True:
        companies = fetch_companies(batch_size, from_)
        
        if not companies.data:
            print("No companies found.")
            break
        
        await process_companies_batch(companies.data)
        
        total_processed += len(companies.data)
        from_ += batch_size
        
        print(f"Processed {total_processed} companies so far.")
        
        if len(companies.data) < batch_size:
            break
        
        
        

    print(f"Finished processing all companies. Total processed: {total_processed}")

# Run the script
asyncio.run(process_all_companies())
