import os
import requests
import asyncio
import aiohttp
from dotenv import load_dotenv
from supabase import create_client, Client
from helpers import fetch_all_companies
import sys
import re

# Load environment variables
load_dotenv()

# Supabase setup
supabase_url: str = os.environ.get("SUPABASE_URL")
supabase_key: str = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(supabase_url, supabase_key)

# Apollo API setup
APOLLO_API_KEY = os.environ.get("APOLLO_API_KEY")
APOLLO_API_URL = "https://api.apollo.io/v1/organizations/enrich"

def clean_website_url(url):
    """
    Clean website URL to standardize format for comparison.
    Examples:
    - http://www.example.com -> example.com
    - https://example.com/home -> example.com
    - example.com/ -> example.com
    """
    if not url:
        return None
    
    # Remove http://, https://, www., and trailing paths
    cleaned_url = url.lower()
    cleaned_url = re.sub(r'^https?://', '', cleaned_url)
    cleaned_url = re.sub(r'^www\.', '', cleaned_url)
    cleaned_url = cleaned_url.split('/')[0]
    
    # Remove trailing dots or slashes
    cleaned_url = cleaned_url.rstrip('./')
    
    return cleaned_url

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
                    await asyncio.sleep(retry_delay)
                    continue
                else:
                    print(f"Failed to fetch data for {domain} after {max_retries} attempts due to rate limiting.")
                    return None
            else:
                print(f"Failed to fetch data for {domain}. Status: {response.status}")
                return None
    
    return None

async def insert_apollo_company(eudamed_company_id, apollo_data):
    organization = apollo_data.get('organization', {})
    apollo_id = organization.get('id')
    
    # Check if an Apollo company with this apollo_id already exists
    if apollo_id:
        existing_result = supabase.table('apollo_companies') \
            .select('id') \
            .eq('apollo_id', apollo_id) \
            .execute()
        
        if existing_result.data and len(existing_result.data) > 0:
            existing_apollo_id = existing_result.data[0]['id']
            print(f"Apollo company with apollo_id {apollo_id} already exists. Updating instead of inserting.")
            
            # Update the existing Apollo company with the new eudamed_company_id
            update_data = {
                "eudamed_company_id": eudamed_company_id,
                "json_dump": apollo_data
            }
            
            update_result = supabase.table('apollo_companies') \
                .update(update_data) \
                .eq('id', existing_apollo_id) \
                .execute()
            
            if len(update_result.data) > 0:
                print(f"Updated existing Apollo company {existing_apollo_id} with eudamed_company_id {eudamed_company_id}")
                
                # Update eudamed_companies with the apollo_companies_id
                eudamed_update_result = supabase.table('eudamed_companies').update({
                    "apollo_companies_id": existing_apollo_id
                }).eq('id', eudamed_company_id).execute()
                
                if len(eudamed_update_result.data) > 0:
                    print(f"Updated eudamed_company {eudamed_company_id} with apollo_companies_id {existing_apollo_id}")
                else:
                    print(f"Failed to update eudamed_company {eudamed_company_id} with apollo_companies_id")
                
                return
            else:
                print(f"Failed to update existing Apollo company {existing_apollo_id}")
    
    # If no existing record with same apollo_id was found, proceed with insert
    insert_data = {
        "eudamed_company_id": eudamed_company_id,
        "apollo_id": apollo_id,
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

    result = supabase.table('apollo_companies').insert(insert_data).execute()
    
    if len(result.data) > 0:
        print(f"Inserted Apollo data for company {eudamed_company_id} - {organization.get('website_url')}")
        # Update eudamed_companies with the apollo_companies_id
        update_result = supabase.table('eudamed_companies').update({
            "apollo_companies_id": result.data[0]['id']
        }).eq('id', eudamed_company_id).execute()
        if len(update_result.data) > 0:
            print(f"Updated eudamed_company {eudamed_company_id} with apollo_companies_id")
        else:
            print(f"Failed to update eudamed_company {eudamed_company_id} with apollo_companies_id")
    else:
        print(f"Failed to insert Apollo data for company {eudamed_company_id}")

async def check_apollo_company_exists(eudamed_company_id):
    result = supabase.table('apollo_companies') \
        .select('id') \
        .eq('eudamed_company_id', eudamed_company_id) \
        .execute()
    
    return len(result.data) > 0

async def find_existing_apollo_company_by_website(website):
    """
    Check if a company with the same website already exists in apollo_companies
    Returns the apollo_companies record if found, None otherwise
    """
    if not website:
        return None
    
    cleaned_website = clean_website_url(website)
    if not cleaned_website:
        return None
    
    # Get all apollo companies
    result = supabase.table('apollo_companies').select('id, website_url, apollo_id').execute()
    
    for apollo_company in result.data:
        if not apollo_company.get('website_url'):
            continue
        
        apollo_website_cleaned = clean_website_url(apollo_company['website_url'])
        if apollo_website_cleaned and apollo_website_cleaned == cleaned_website:
            return apollo_company
    
    return None

async def link_eudamed_to_existing_apollo(eudamed_company_id, apollo_company_id):
    """
    Link an eudamed_company to an existing apollo_company
    """
    update_result = supabase.table('eudamed_companies').update({
        "apollo_companies_id": apollo_company_id
    }).eq('id', eudamed_company_id).execute()
    
    if len(update_result.data) > 0:
        print(f"Linked eudamed_company {eudamed_company_id} to existing apollo_company {apollo_company_id}")
        return True
    else:
        print(f"Failed to link eudamed_company {eudamed_company_id} to apollo_company {apollo_company_id}")
        return False

async def update_apollo_company_with_eudamed_id(apollo_company_id, eudamed_company_id):
    """
    Update an existing apollo_company with an eudamed_company_id reference
    """
    update_result = supabase.table('apollo_companies').update({
        "eudamed_company_id": eudamed_company_id
    }).eq('id', apollo_company_id).execute()
    
    if len(update_result.data) > 0:
        print(f"Updated apollo_company {apollo_company_id} with eudamed_company_id {eudamed_company_id}")
        return True
    else:
        print(f"Failed to update apollo_company {apollo_company_id} with eudamed_company_id {eudamed_company_id}")
        return False

async def process_company(session, company, current, total):
    # First check if the eudamed company already has an apollo_companies_id
    result = supabase.table('eudamed_companies') \
        .select('apollo_companies_id') \
        .eq('id', company['id']) \
        .execute()
    
    if result.data and result.data[0].get('apollo_companies_id'):
        print(f"[{current}/{total}] {company['name']} already linked to Apollo. Skipping.")
        return
    
    # If no direct link, check if the company with same website already exists in apollo_companies
    existing_apollo = await find_existing_apollo_company_by_website(company['website'])
    if existing_apollo:
        print(f"[{current}/{total}] Found existing Apollo company with matching website for {company['name']}.")
        # Update the apollo company with the eudamed company ID
        await update_apollo_company_with_eudamed_id(existing_apollo['id'], company['id'])
        # Also update the eudamed company with the apollo company ID for backward compatibility
        await link_eudamed_to_existing_apollo(company['id'], existing_apollo['id'])
        return
    
    # If Apollo company already exists for this eudamed company, skip
    if await check_apollo_company_exists(company['id']):
        print(f"[{current}/{total}] {company['name']} already exists in Apollo. Skipping.")
        return

    if not company['website']:
        print(f"[{current}/{total}] {company['name']} has no website. Skipping.")
        return

    # Only make the API call if no existing Apollo company was found
    apollo_data = await fetch_apollo_data(session, company['website'])

    if apollo_data:
        await insert_apollo_company(company['id'], apollo_data)
    else:
        # Create a minimal entry in the apollo_companies table
        minimal_data = {
            "eudamed_company_id": company['id'],
            "website_url": company['website'],
            "json_dump": {"message": "No data found by Apollo"}
        }
        result = supabase.table('apollo_companies').insert(minimal_data).execute()
        if len(result.data) > 0:
            print(f"[{current}/{total}] Inserted minimal Apollo data for company {company['id']} - {company['website']}")
            # Update eudamed_companies with the apollo_companies_id
            update_result = supabase.table('eudamed_companies').update({
                "apollo_companies_id": result.data[0]['id']
            }).eq('id', company['id']).execute()
            if len(update_result.data) > 0:
                print(f"Updated eudamed_company {company['id']} with apollo_companies_id")
            else:
                print(f"Failed to update eudamed_company {company['id']} with apollo_companies_id")
        else:
            print(f"[{current}/{total}] Failed to insert minimal Apollo data for company {company['id']}")

    # wait 2 sec to avoid Apollo rate limiting
    await asyncio.sleep(2)

async def process_all_companies(iso_code):
    def additional_filters(query):
        return query.not_.is_('website', 'null')
    
    # Fetch all companies
    companies = fetch_all_companies(supabase, iso_code, additional_filters)
    
    if not companies:
        print(f"No companies to process for {iso_code}")
        return

    total_companies = len(companies)
    print(f"Processing {total_companies} companies for {iso_code}")
    
    async with aiohttp.ClientSession() as session:
        for i, company in enumerate(companies):
            if not company.get('website') or company.get('website') == 'n/a':
                continue
            await process_company(session, company, i+1, total_companies)


    print(f"Finished processing all companies. Total processed: {total_companies}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python get_apollo_company.py <iso_code>")
        sys.exit(1)
    
    iso_code = sys.argv[1].upper()
    asyncio.run(process_all_companies(iso_code))
