import os
import asyncio
from dotenv import load_dotenv
from supabase import create_client, Client
import sys

# Import all the scraper modules
from get_company_id import process_companies_for_country, process_all_countries
from get_company_details import process_all_companies as process_all_company_details
from get_company_devices import process_all_companies as process_all_company_devices
from get_company_devices_details import process_all_products as process_all_device_details

# Load environment variables
load_dotenv()

# Supabase setup
url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url, key)

def reset_scraping_status():
    """Reset scraping status for all companies"""
    print("Resetting scraping status for all companies...")
    supabase.table('eudamed_companies') \
        .update({"scraping_status": None}) \
        .not_.is_('scraping_status', 'null') \
        .execute()
    print("Reset complete.")

def validate_iso_code(iso_code):
    """Validate if the given ISO code exists in the countries table"""
    if not iso_code:
        return True
    
    result = supabase.table('countries').select("iso_code").eq("iso_code", iso_code).execute()
    return len(result.data) > 0

async def run_scraper(iso_code):
    """Run all scraper scripts in sequence for a specific country"""
    if not validate_iso_code(iso_code):
        print(f"Error: Invalid ISO code '{iso_code}'")
        return

    # Reset scraping status
    reset_scraping_status()
    
    # Step 1: Get company IDs
    print("\n1. Getting company IDs...")
    process_companies_for_country(iso_code)
    
    # Step 2: Get company details
    print("\n2. Getting company details...")
    await process_all_company_details()
    
    # Step 3: Get company devices
    print("\n3. Getting company devices...")
    await process_all_company_devices()
    
    # Step 4: Get device details
    print("\n4. Getting device details...")
    await process_all_device_details()
    
    
    print("\nAll scraping tasks completed!")

def main():
    """
    Main function that requires exactly one ISO code as a command line argument.
    Throws an error if no ISO code or multiple arguments are provided.
    """
    if len(sys.argv) != 2:
        print("Error: Exactly one ISO code must be provided as an argument.")
        print("Usage: python run_scraper.py <iso_code>")
        sys.exit(1)
    
    iso_code = sys.argv[1]
    asyncio.run(run_scraper(iso_code))

if __name__ == "__main__":
    main() 