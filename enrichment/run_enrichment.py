import os
import sys
import asyncio
from fetch_company_websites import fetch_and_update_company_websites
from clean_url import process_all_companies as clean_urls
from bing_get_company_empl_llm import process_all_companies as get_employee_counts
from get_apollo_company import process_all_companies as get_apollo_data

async def run_enrichment(iso_code):
    # print("\n1. Fetching company websites...")
    # fetch_and_update_company_websites(iso_code)
    
    # print("\n2. Cleaning URLs...")
    # clean_urls(iso_code)
    
    # print("\n3. Getting employee counts...")
    # get_employee_counts(iso_code)
    
    print("\n4. Getting Apollo company data...")
    await get_apollo_data(iso_code)
    
    print("\nAll enrichment tasks completed!")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python run_enrichment.py <iso_code>")
        sys.exit(1)
        
    iso_code = sys.argv[1].upper()
    asyncio.run(run_enrichment(iso_code))