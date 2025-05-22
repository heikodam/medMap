import os
import json
import requests
from datetime import datetime
from typing import Dict, List, Optional, Any
import time

from utils import get_supabase_client, retry_supabase_operation, format_company_data

def fetch_companies(page: int = 1, page_size: int = 100) -> List[Dict[str, Any]]:
    """
    Fetch companies from the PARD API
    
    Args:
        page: Page number to fetch (not used in this API)
        page_size: Number of items per page (not used in this API)
        
    Returns:
        List of company data dictionaries
    """
    api_url = "https://pard.mhra.gov.uk/searchManufacturersAdvanced"
    
    # The search payload with empty fields to get all companies
    payload = {
        "searchTerm": {
            "manufacturerName": "",
            "referenceNumber": "",
            "deviceName": "",
            "deviceType": "",
            "gmdnCode": ""
        }
    }
    
    headers = {
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(api_url, headers=headers, json=payload)
        response.raise_for_status()
        
        # The API returns a list of companies directly
        return response.json()
    except requests.RequestException as e:
        print(f"Error fetching companies: {e}")
        return []

def save_companies_to_supabase(companies: List[Dict[str, Any]]) -> int:
    """
    Save companies to Supabase
    
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
            else:
                # Insert new company
                def insert_company():
                    return supabase.table("pard_companies").insert(formatted_company).execute()
                
                retry_supabase_operation(insert_company)
            
            saved_count += 1
            
            # Add a small delay between operations to avoid overwhelming the API
            time.sleep(0.1)
            
        except Exception as e:
            print(f"Error saving company {formatted_company.get('man_organisation_name', 'Unknown')}: {e}")
            # Continue with next company instead of failing the entire batch
            continue
    
    return saved_count

def scrape_all_companies(max_pages: Optional[int] = None) -> int:
    """
    Scrape all companies from the PARD API and save to Supabase
    
    Args:
        max_pages: Maximum number of pages to scrape (not used since the API returns all data at once)
        
    Returns:
        Total number of companies saved
    """
    print(f"Fetching companies...")
    companies = fetch_companies()
    
    if not companies:
        print("No companies found")
        return 0
    
    print(f"Found {len(companies)} companies")
    saved = save_companies_to_supabase(companies)
    print(f"Saved {saved} companies")
    
    return saved

if __name__ == "__main__":
    # For testing the scraper directly
    scrape_all_companies() 