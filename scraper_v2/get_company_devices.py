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

def fetch_companies(batch_size=10, from_=0):
    """Fetch a batch of companies from Supabase"""
    return supabase.table('eudamed_company') \
        .select("id", "eudamed_uuid") \
        .eq("scraping_status", "FETCHED_DETAILS") \
        .range(from_, from_ + batch_size - 1) \
        .execute()

async def fetch_devices(session, srn, page=0, page_size=300, max_retries=3):
    params = {
        "page": page,
        "pageSize": page_size,
        "size": page_size,
        "iso2Code": "en",
        "srn": srn,
        "languageIso2Code": "en"
    }
    
    for attempt in range(max_retries):
        try:
            async with session.get(base_url, params=params) as response:
                return await response.json()
        except asyncio.TimeoutError:
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt  # Exponential backoff
                print(f"Request timed out for SRN {srn}, retrying in {wait_time} seconds (attempt {attempt+1}/{max_retries})")
                await asyncio.sleep(wait_time)
            else:
                print(f"Failed to fetch devices for SRN {srn} after {max_retries} attempts")
                raise
        except Exception as e:
            print(f"Error fetching devices for SRN {srn}: {str(e)}")
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt
                print(f"Retrying in {wait_time} seconds (attempt {attempt+1}/{max_retries})")
                await asyncio.sleep(wait_time)
            else:
                raise

async def insert_or_update_device(device, company_id):
    eudamed_uuid = device['uuid']
    
    # Check if the device already exists
    existing_device = supabase.table('eudamed_product') \
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
        supabase.table('eudamed_product') \
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
        supabase.table('eudamed_product').insert(new_device).execute()
        print(f"Inserted new device: {eudamed_uuid}")

async def process_company_devices(session, company):
    try:
        page = 0
        while True:
            data = await fetch_devices(session, company['eudamed_uuid'], page)
            
            tasks = [insert_or_update_device(device, company['id']) for device in data['content']]
            await asyncio.gather(*tasks)
            
            if data['last']:
                break
            
            page += 1
        
        # Update company scraping status
        supabase.table('eudamed_company') \
            .update({"scraping_status": "FETCHED_PRODUCTS"}) \
            .eq("id", company['id']) \
            .execute()
    except Exception as e:
        print(f"Error processing company {company['eudamed_uuid']}: {str(e)}")
        raise

async def process_companies_batch(companies):
    # Configure timeout settings for the client session
    timeout = aiohttp.ClientTimeout(total=120, connect=60, sock_connect=60, sock_read=60)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        tasks = []
        for company in companies:
            task = process_company_devices(session, company)
            tasks.append(task)
        
        # Use return_exceptions to prevent one failure from stopping all tasks
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Log any exceptions that occurred
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                print(f"Failed to process company {companies[i]['eudamed_uuid']}: {result}")

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
# asyncio.run(process_all_companies())
