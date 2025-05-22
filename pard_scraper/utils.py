import os
import random
import time
from typing import Dict, Any, Callable, Optional, List
from datetime import datetime
import httpx
from supabase import create_client

def get_supabase_client():
    """
    Create and return a Supabase client using environment variables
    """
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_KEY")
    
    if not url or not key:
        raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set in environment variables")
    
    return create_client(url, key)

def retry_supabase_operation(operation: Callable, max_retries: int = 5, initial_backoff: float = 1.0, 
                            max_backoff: float = 60.0, jitter: float = 0.1) -> Any:
    """
    Retry a Supabase operation with exponential backoff

    Args:
        operation: The function to retry
        max_retries: Maximum number of retry attempts
        initial_backoff: Initial backoff time in seconds
        max_backoff: Maximum backoff time in seconds
        jitter: Random jitter factor to add to backoff

    Returns:
        The result of the operation if successful

    Raises:
        The last exception if all retries fail
    """
    retries = 0
    backoff = initial_backoff
    last_exception = None

    while retries < max_retries:
        try:
            return operation()
        except (httpx.RemoteProtocolError, httpx.ReadTimeout, httpx.ConnectTimeout, 
                httpx.ReadError, httpx.ConnectError) as e:
            last_exception = e
            retries += 1
            
            if retries >= max_retries:
                break
                
            # Calculate backoff with jitter
            jitter_amount = backoff * jitter * random.uniform(-1, 1)
            sleep_time = min(backoff + jitter_amount, max_backoff)
            
            print(f"Supabase connection error: {e}. Retry {retries}/{max_retries} after {sleep_time:.2f}s")
            time.sleep(sleep_time)
            
            # Exponential backoff
            backoff = min(backoff * 2, max_backoff)
    
    # If we got here, all retries failed
    raise last_exception

def format_company_data(company_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Format the company data for insertion into Supabase
    
    Args:
        company_data: Raw company data from the API
        
    Returns:
        Formatted company data ready for database insertion
    """
    # Convert to snake_case and standardize data types
    formatted_data = {
        "man_organisation_id": company_data.get("MAN_ORGANISATION_ID"),
        "man_created_date": company_data.get("MAN_CREATED_DATE"),
        "man_organisation_name": company_data.get("MAN_ORGANISATION_NAME", "").strip(),
        "man_addr_line_1": company_data.get("MAN_ADDR_LINE_1", ""),
        "man_addr_line_2": company_data.get("MAN_ADDR_LINE_2", ""),
        "man_addr_line_3": company_data.get("MAN_ADDR_LINE_3", ""),
        "man_addr_line_4": company_data.get("MAN_ADDR_LINE_4", ""),
        "man_city": company_data.get("MAN_CITY", ""),
        "man_countystateprovince": company_data.get("MAN_COUNTYSTATEPROVINCE", ""),
        "man_country": company_data.get("MAN_COUNTRY", ""),
        "rep_name": company_data.get("REP_NAME", ""),
        "rep_address_line_1": company_data.get("REP_ADDRESS_LINE_1", ""),
        "rep_address_line_2": company_data.get("REP_ADDRESS_LINE_2", ""),
        "rep_address_line_3": company_data.get("REP_ADDRESS_LINE_3", ""),
        "rep_address_line_4": company_data.get("REP_ADDRESS_LINE_4", ""),
        "rep_city": company_data.get("REP_CITY", ""),
        "rep_county_state_province": company_data.get("REP_COUNTY_STATE_PROVINCE", ""),
        "rep_country": company_data.get("REP_COUNTRY", ""),
        "relationship": company_data.get("RELATIONSHIP", ""),
        "last_updated_date": company_data.get("LAST_UPDATED_DATE"),
        "man_account_number": company_data.get("MAN_ACCOUNT_NUMBER"),
        "man_postcode": company_data.get("MAN_POSTCODE", ""),
        "rep_postcode": company_data.get("REP_POSTCODE", ""),
        "rep_organisation_id": company_data.get("REP_ORGANISATION_ID"),
        "customer_service_email_address": company_data.get("CUSTOMER_SERVICE_EMAIL_ADDRESS"),
        "customer_service_telephone_number": company_data.get("CUSTOMER_SERVICE_TELEPHONE_NUMBER"),
        "rep_customer_service_email_address": company_data.get("REP_CUSTOMER_SERVICE_EMAIL_ADDRESS"),
        "rep_customer_service_telephone_number": company_data.get("REP_CUSTOMER_SERVICE_TELEPHONE_NUMBER")
    }
    
    return formatted_data

def get_all_company_ids() -> List[int]:
    """
    Get all company IDs from the Supabase database
    
    Returns:
        List of company MAN_ORGANISATION_ID values
    """
    supabase = get_supabase_client()
    
    def fetch_company_ids():
        return supabase.table("pard_company").select("man_organisation_id").execute()
    
    result = retry_supabase_operation(fetch_company_ids)
    
    if not result.data:
        return []
    
    # Filter out None values
    return [company["man_organisation_id"] for company in result.data 
            if company.get("man_organisation_id") is not None]

def log_scrape_run(scrape_type: str, total_items: int, status: str, error: Optional[str] = None) -> Dict[str, Any]:
    """
    Log a scrape run to track when scrapes were performed
    
    Args:
        scrape_type: Type of scrape ('companies' or 'devices')
        total_items: Total number of items scraped
        status: Status of the scrape ('success' or 'error')
        error: Error message if status is 'error'
        
    Returns:
        The logged record
    """
    supabase = get_supabase_client()
    
    # Create a scrape_log table if it doesn't exist yet
    try:
        log_data = {
            "scrape_type": scrape_type,
            "total_items": total_items,
            "status": status,
            "error": error,
            "created_at": datetime.now().isoformat()
        }
        
        def insert_log():
            return supabase.table("scrape_log").insert(log_data).execute()
        
        result = retry_supabase_operation(insert_log)
        return result.data[0] if result.data else log_data
    except Exception as e:
        print(f"Error logging scrape run: {e}")
        return {
            "scrape_type": scrape_type,
            "total_items": total_items,
            "status": status,
            "error": str(e),
            "created_at": datetime.now().isoformat()
        } 