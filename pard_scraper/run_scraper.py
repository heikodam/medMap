import os
import argparse
import time
import traceback
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime

from utils import (
    get_supabase_client, 
    retry_supabase_operation, 
    format_company_data,
    get_all_company_ids,
    log_scrape_run
)
from company_scraper import scrape_all_companies, save_companies_to_supabase
from device_scraper import scrape_all_devices, scrape_devices_for_company

def log_company_addition(company_data: Dict[str, Any], action: str = "insert") -> None:
    """
    Log company addition or update to console with detailed information
    
    Args:
        company_data: The company data being saved
        action: Action being performed ("insert" or "update")
    """
    # Clear the terminal for better visibility
    os.system('cls' if os.name == 'nt' else 'clear')
    
    formatted_data = format_company_data(company_data)
    
    # Print company details with formatting
    print(f"{'=' * 50}")
    print(f"COMPANY {action.upper()} AT {datetime.now().isoformat()}")
    print(f"{'=' * 50}")
    print(f"ID: {formatted_data.get('man_organisation_id', 'N/A')}")
    print(f"Name: {formatted_data.get('man_organisation_name', 'N/A')}")
    print(f"Country: {formatted_data.get('man_country', 'N/A')}")
    print(f"City: {formatted_data.get('man_city', 'N/A')}")
    
    # Skip detailed logging if it's failing
    if os.environ.get("SKIP_DETAILED_LOGS") == "1":
        return
        
    # Add to the database logs
    log_data = {
        "log_type": "company",
        "action": action,
        "entity_id": formatted_data.get('man_organisation_id'),
        "entity_name": formatted_data.get('man_organisation_name'),
        "created_at": datetime.now().isoformat()
    }
    
    try:
        supabase = get_supabase_client()
        
        def insert_log():
            return supabase.table("detailed_logs").insert(log_data).execute()
        
        retry_supabase_operation(insert_log)
    except Exception as e:
        # Set environment variable to skip future detailed logging
        os.environ["SKIP_DETAILED_LOGS"] = "1"
        print(f"Warning: Could not save detailed log: {str(e) or 'Unknown error'}. Detailed logging disabled.")
        print("To re-enable detailed logging, restart the scraper.")
        # Sleep briefly to ensure the message is seen
        time.sleep(1)

def custom_save_companies_to_supabase(companies: List[Dict[str, Any]]) -> int:
    """
    Save companies to Supabase with detailed logging
    
    Args:
        companies: List of company data dictionaries
        
    Returns:
        Number of companies saved
    """
    if not companies:
        return 0
    
    supabase = get_supabase_client()
    saved_count = 0
    
    for company in companies:
        try:
            formatted_company = format_company_data(company)
            
            # Check if company already exists
            def check_company_exists():
                return supabase.table("pard_companies").select("id").eq("man_organisation_id", formatted_company["man_organisation_id"]).execute()
            
            existing = retry_supabase_operation(check_company_exists)
            
            if existing.data:
                # Update existing company
                def update_company():
                    return supabase.table("pard_companies").update(formatted_company).eq("man_organisation_id", formatted_company["man_organisation_id"]).execute()
                
                retry_supabase_operation(update_company)
                log_company_addition(company, "update")
            else:
                # Insert new company
                def insert_company():
                    return supabase.table("pard_companies").insert(formatted_company).execute()
                
                retry_supabase_operation(insert_company)
                log_company_addition(company, "insert")
            
            saved_count += 1
            
            # Add a small delay between operations to avoid overwhelming the API
            time.sleep(0.1)
            
        except Exception as e:
            print(f"Error saving company {formatted_company.get('man_organisation_name', 'Unknown')}: {e}")
            # Continue with next company instead of failing the entire batch
            continue
    
    return saved_count

def run_company_scraper(max_retries: int = 3, retry_delay: int = 5) -> int:
    """
    Run the company scraper with retry logic
    
    Args:
        max_retries: Maximum number of retry attempts
        retry_delay: Delay between retries in seconds
        
    Returns:
        Total number of companies saved
    """
    print(f"Starting company scraper at {datetime.now().isoformat()}")
    
    attempt = 0
    while attempt < max_retries:
        try:
            # Fetch companies
            print(f"Fetching companies...")
            from company_scraper import fetch_companies
            companies = fetch_companies()
            
            if not companies:
                print("No companies found")
                return 0
            
            print(f"Found {len(companies)} companies")
            
            # Use our custom save function with detailed logging
            saved = custom_save_companies_to_supabase(companies)
            
            log_scrape_run("companies", saved, "success")
            return saved
        except Exception as e:
            attempt += 1
            error_message = str(e)
            print(f"Error in company scraper (attempt {attempt}/{max_retries}): {error_message}")
            if attempt < max_retries:
                print(f"Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
            else:
                print(f"Maximum retry attempts reached. Giving up.")
                log_scrape_run("companies", 0, "error", error_message)
                traceback.print_exc()
                return 0
    
    return 0

def run_device_scraper(company_ids: Optional[List[int]] = None, max_retries: int = 3, 
                     retry_delay: int = 5, batch_size: int = 100, batch_delay: int = 2) -> int:
    """
    Run the device scraper with retry logic
    
    Args:
        company_ids: List of company IDs to scrape devices for (None for all devices)
        max_retries: Maximum number of retry attempts
        retry_delay: Delay between retries in seconds
        batch_size: Number of devices to process in each batch
        batch_delay: Delay in seconds between batches
        
    Returns:
        Total number of devices saved
    """
    print(f"Starting device scraper at {datetime.now().isoformat()}")
    
    attempt = 0
    while attempt < max_retries:
        try:
            total_saved = 0
            
            if company_ids:
                # Filter out any None values
                valid_company_ids = [cid for cid in company_ids if cid is not None]
                if len(valid_company_ids) != len(company_ids):
                    print(f"Warning: Filtered out {len(company_ids) - len(valid_company_ids)} None company IDs")
                
                for company_id in valid_company_ids:
                    print(f"Scraping devices for company {company_id}")
                    saved, skipped = scrape_devices_for_company(company_id)
                    total_saved += saved
            else:
                total_saved, _ = scrape_all_devices(batch_size=batch_size, batch_delay=batch_delay)
            
            log_scrape_run("devices", total_saved, "success")
            return total_saved
        except Exception as e:
            attempt += 1
            error_message = str(e)
            print(f"Error in device scraper (attempt {attempt}/{max_retries}): {error_message}")
            if attempt < max_retries:
                print(f"Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
            else:
                print(f"Maximum retry attempts reached. Giving up.")
                log_scrape_run("devices", 0, "error", error_message)
                traceback.print_exc()
                return 0
    
    return 0

def run_full_scrape(batch_size: int = 100, batch_delay: int = 2) -> Dict[str, int]:
    """
    Run a full scrape of companies followed by devices
    
    Args:
        batch_size: Number of devices to process in each batch
        batch_delay: Delay in seconds between batches
        
    Returns:
        Dictionary with counts of companies and devices saved
    """
    print(f"Starting full scrape at {datetime.now().isoformat()}")
    
    # First scrape companies
    companies_saved = run_company_scraper()
    print(f"Saved {companies_saved} companies")
    
    # Give Supabase a moment to process the inserts
    time.sleep(2)
    
    # Then scrape devices for all companies
    if companies_saved > 0:
        company_ids = get_all_company_ids()
        devices_saved = run_device_scraper(company_ids=company_ids, batch_size=batch_size, batch_delay=batch_delay)
    else:
        devices_saved = run_device_scraper(batch_size=batch_size, batch_delay=batch_delay)
    
    print(f"Saved {devices_saved} devices")
    
    return {
        "companies_saved": companies_saved,
        "devices_saved": devices_saved
    }

def main():
    """
    Main entry point with command line argument parsing
    """
    parser = argparse.ArgumentParser(description="Run PARD scrapers to fetch companies and devices")
    parser.add_argument("--type", choices=["companies", "devices", "full"], default="full",
                        help="Type of scrape to run (companies, devices, or full)")
    parser.add_argument("--company-id", type=int, default=None,
                        help="Specific company ID to scrape devices for (only for devices type)")
    parser.add_argument("--batch-size", type=int, default=100,
                        help="Number of devices to process in each batch")
    parser.add_argument("--batch-delay", type=int, default=2,
                        help="Delay in seconds between batches")
    
    args = parser.parse_args()
    
    if args.type == "companies":
        companies_saved = run_company_scraper()
        print(f"Saved {companies_saved} companies")
    
    elif args.type == "devices":
        if args.company_id:
            devices_saved, _ = scrape_devices_for_company(args.company_id)
            print(f"Saved {devices_saved} devices for company {args.company_id}")
        else:
            devices_saved = run_device_scraper(batch_size=args.batch_size, batch_delay=args.batch_delay)
            print(f"Saved {devices_saved} devices")
    
    elif args.type == "full":
        results = run_full_scrape(batch_size=args.batch_size, batch_delay=args.batch_delay)
        print(f"Full scrape complete. Saved {results['companies_saved']} companies and {results['devices_saved']} devices")

if __name__ == "__main__":
    main() 