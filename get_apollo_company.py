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

# Apollo API setup
APOLLO_API_KEY = os.environ.get("APOLLO_API_KEY")
APOLLO_API_URL = "https://api.apollo.io/v1/organizations/enrich"

async def fetch_companies(iso_code, batch_size=1000, from_=0):
    return supabase.table('eudamed_companies') \
        .select("id", "name", "website") \
        .eq("iso_code", iso_code) \
        .neq("id", supabase.table('apollo_companies').select("eudamed_company_id")) \
        .range(from_, from_ + batch_size - 1) \
        .execute()


async def fetch_apollo_data(session, domain):
    headers = {
        "Content-Type": "application/json",
        "Cache-Control": "no-cache",
        "X-Api-Key": APOLLO_API_KEY
    }
    params = {"domain": domain}
    
    max_retries = 3
    retry_delay = 10

    for attempt in range(max_retries):
        async with session.get(APOLLO_API_URL, headers=headers, params=params) as response:
            if response.status == 200:
                return await response.json()
            elif response.status == 429:
                if attempt < max_retries - 1:
                    print(f"Rate limit reached for {domain}. Retrying in {retry_delay} seconds...")
                    print(response.headers)
                    exit(1)
                    await asyncio.sleep(retry_delay)
                    continue
                else:
                    print(f"Failed to fetch data for {domain} after {max_retries} attempts due to rate limiting.")
                    print(response.headers)
                    exit(1)
                    return None
            else:
                # stop the program if this happens and print the response status and headers
                print(f"Failed to fetch data for {domain}. Status: {response.status}")
                print(response.headers)

                # stop the program
                exit(1)

                return None
    
    return None

async def insert_apollo_company(eudamed_company_id, apollo_data):
    organization = apollo_data.get('organization', {})


    
    # Prepare the data for insertion
    insert_data = {
        "eudamed_company_id": eudamed_company_id,
        "apollo_id": organization.get('id'),
        "name": organization.get('name'),
        "website_url": organization.get('website_url'),
        "blog_url": organization.get('blog_url'),
        "angellist_url": organization.get('angellist_url'),
        "linkedin_url": organization.get('linkedin_url'),
        "twitter_url": organization.get('twitter_url'),
        "facebook_url": organization.get('facebook_url'),
        "primary_phone": organization.get('primary_phone', {}).get('number'),
        "alexa_ranking": organization.get('alexa_ranking'),
        "phone": organization.get('phone'),
        "linkedin_uid": organization.get('linkedin_uid'),
        "founded_year": organization.get('founded_year'),
        "publicly_traded_symbol": organization.get('publicly_traded_symbol'),
        "publicly_traded_exchange": organization.get('publicly_traded_exchange'),
        "logo_url": organization.get('logo_url'),
        "crunchbase_url": organization.get('crunchbase_url'),
        "primary_domain": organization.get('primary_domain'),
        "industry": organization.get('industry'),
        "estimated_num_employees": organization.get('estimated_num_employees'),
        "snippets_loaded": organization.get('snippets_loaded'),
        "industry_tag_id": organization.get('industry_tag_id'),
        "retail_location_count": organization.get('retail_location_count'),
        "raw_address": organization.get('raw_address'),
        "street_address": organization.get('street_address'),
        "city": organization.get('city'),
        "state": organization.get('state'),
        "postal_code": organization.get('postal_code'),
        "country": organization.get('country'),
        "owned_by_organization_id": organization.get('owned_by_organization_id'),
        "num_suborganizations": organization.get('num_suborganizations'),
        "seo_description": organization.get('seo_description'),
        "short_description": organization.get('short_description'),
        "annual_revenue_printed": organization.get('annual_revenue_printed'),
        "annual_revenue": organization.get('annual_revenue'),
        "total_funding": organization.get('total_funding'),
        "total_funding_printed": organization.get('total_funding_printed'),
        "latest_funding_round_date": organization.get('latest_funding_round_date'),
        "latest_funding_stage": organization.get('latest_funding_stage'),
        "suborganizations": organization.get('suborganizations'),
        "funding_events": organization.get('funding_events'),
        "account_id": organization.get('account_id'),
        "departmental_head_count": organization.get('departmental_head_count'),
        "account": organization.get('account'),
        "json_dump": apollo_data
    }

    # Insert the data into apollo_companies table
    result = supabase.table('apollo_companies').insert(insert_data).execute()
    
    if len(result.data) > 0:
        print(f"Inserted Apollo data for company {eudamed_company_id} - {organization.get('website_url')}")
    else:
        print(f"Failed to insert Apollo data for company {eudamed_company_id}")

async def update_eudamed_company_status(company_id):
    supabase.table('eudamed_companies') \
        .update({"scraping_status": "ENRICHED_APOLLO"}) \
        .eq('id', company_id) \
        .execute()

async def process_company(session, company):
    # print(f"Processing company {company['name']} - {company['website']}")

    if not company['website']:
        await update_eudamed_company_status(company['id'])
        print(f"Company {company['name']} has no website. Skipping.")
        return

    apollo_data = await fetch_apollo_data(session, company['website'])

    print("Apollo data: ", apollo_data)


    if apollo_data:
        await insert_apollo_company(company['id'], apollo_data)
        await update_eudamed_company_status(company['id'])
    else:
        await update_eudamed_company_status(company['id']) # commented because if apollo credits run out it returns None
        print(f"No Apollo data found for company {company['id']}")

async def process_companies_batch(companies):
    async with aiohttp.ClientSession() as session:
        tasks = [process_company(session, company) for company in companies]
        await asyncio.gather(*tasks)

async def process_all_companies(iso_code):
    batch_size = 1
    from_ = 0
    total_processed = 0

    while True:
        companies = await fetch_companies(iso_code, batch_size, from_)
        
        if not companies.data:
            print("No more companies found.")
            break
        
        print(f"Processing {len(companies.data)} companies...")
        await process_companies_batch(companies.data)
        
        total_processed += len(companies.data)
        
        # print(f"Processed {total_processed} companies so far.")
        
        if len(companies.data) < batch_size:
            break
        
        break   
        
        # wait 1 sec
        await asyncio.sleep(2)
        
        
        
        
    print(f"Finished processing all companies. Total processed: {total_processed}")

# Run the script
asyncio.run(process_all_companies("DE"))  # Replace "DE" with the desired country code
