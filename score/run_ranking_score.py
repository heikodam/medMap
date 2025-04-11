import os
import sys
import asyncio
import aiohttp
from dotenv import load_dotenv
from supabase import create_client, Client
from ranking_score_helpers import calculate_company_ranking, update_company
from helpers import fetch_all_companies

# Load environment variables
load_dotenv()

# Supabase setup
url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url, key)

async def process_company(session, company):
    ranking_score = await calculate_company_ranking(supabase, company)
    
    update_data = {
        "ranking_score": ranking_score,
        "scraping_status": "UPDATED_RANKING_SCORE"
    }

    await update_company(supabase, company['id'], update_data)
    print(f"Updated ranking score for {company['name']} to {ranking_score}")

async def process_companies_batch(companies):
    async with aiohttp.ClientSession() as session:
        tasks = [process_company(session, company) for company in companies]
        await asyncio.gather(*tasks)

async def run_ranking_score(iso_code: str):
    print(f"\nCalculating ranking scores for companies in {iso_code}...")
    
    def additional_filters(query):
        return query.neq("scraping_status", "UPDATED_RANKING_SCORE")
    
    companies = fetch_all_companies(supabase, iso_code, additional_filters)
    
    if not companies:
        print(f"No companies found for {iso_code} that need ranking score update.")
        return
    
    print(f"Found {len(companies)} companies to process.")
    
    # Process in batches of 100
    batch_size = 100
    for i in range(0, len(companies), batch_size):
        batch = companies[i:i + batch_size]
        await process_companies_batch(batch)
        print(f"Processed {min(i + batch_size, len(companies))} out of {len(companies)} companies.")
    
    print(f"\nFinished calculating ranking scores for {iso_code}!")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python run_ranking_score.py <iso_code>")
        sys.exit(1)
        
    iso_code = sys.argv[1].upper()
    asyncio.run(run_ranking_score(iso_code)) 