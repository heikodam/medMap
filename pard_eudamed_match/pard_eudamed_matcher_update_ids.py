import os
import time
from dotenv import load_dotenv
from supabase import create_client, Client
from typing import List, Dict, Any, Tuple, Set


def connect_to_supabase() -> Client:
    """
    Connect to Supabase client using environment variables.
    
    Returns:
        Client: Supabase client
    """
    # Load environment variables from .env file
    load_dotenv()
    
    url: str = os.environ.get("SUPABASE_URL")
    key: str = os.environ.get("SUPABASE_KEY")
    
    # Create Supabase client
    supabase: Client = create_client(url, key)
    return supabase


def fetch_eudamed_companies(supabase: Client) -> Dict[str, str]:
    """
    Fetch eudamed companies with their IDs and build a lookup dictionary.
    
    Args:
        supabase: Supabase client
        
    Returns:
        Dictionary mapping normalized company names to their IDs
    """
    print("Fetching eudamed companies...")
    eudamed_companies = {}
    page_size = 1000
    start = 0
    
    while True:
        eudamed_response = supabase.table('eudamed_companies').select("id, name").range(start, start + page_size - 1).execute()
        batch = eudamed_response.data
        
        for company in batch:
            normalized_name = normalize_company_name(company.get('name', ''))
            if normalized_name:
                eudamed_companies[normalized_name] = company.get('id')
        
        if len(batch) < page_size:
            break
            
        start += page_size
        print(f"Fetched {len(eudamed_companies)} eudamed companies so far...")
    
    print(f"Found total of {len(eudamed_companies)} eudamed companies")
    return eudamed_companies


def fetch_pard_companies(supabase: Client) -> List[Dict[str, Any]]:
    """
    Fetch pard companies with their IDs.
    
    Args:
        supabase: Supabase client
        
    Returns:
        List of pard companies with IDs and names
    """
    print("Fetching pard companies...")
    pard_companies = []
    page_size = 1000
    start = 0
    
    while True:
        pard_response = supabase.table('pard_companies').select("id, man_organisation_name").range(start, start + page_size - 1).execute()
        batch = pard_response.data
        pard_companies.extend(batch)
        
        if len(batch) < page_size:
            break
            
        start += page_size
        print(f"Fetched {len(pard_companies)} pard companies so far...")
    
    print(f"Found total of {len(pard_companies)} pard companies")
    return pard_companies


def normalize_company_name(name: str) -> str:
    """
    Normalize company name for better matching.
    
    Args:
        name: Company name to normalize
        
    Returns:
        Normalized company name
    """
    if not name:
        return ""
    
    # Convert to lowercase and trim whitespace
    normalized = name.lower().strip()
    
    # Remove common suffixes and legal entity identifiers
    suffixes = [" inc", " inc.", " incorporated", " llc", " llc.", " ltd", " ltd.", " limited", 
                " gmbh", " corp", " corp.", " corporation", " co", " co.", " company",
                " ag", " s.a.", " s.a", " b.v.", " b.v", " n.v.", " n.v"]
    
    for suffix in suffixes:
        if normalized.endswith(suffix):
            normalized = normalized[:-len(suffix)].strip()
    
    # Replace special characters with spaces
    for char in [',', '.', '-', '/', '\\', '(', ')', '[', ']', '{', '}', '&']:
        normalized = normalized.replace(char, ' ')
    
    # Remove extra spaces
    while '  ' in normalized:
        normalized = normalized.replace('  ', ' ')
    
    return normalized.strip()


def update_pard_companies(supabase: Client, pard_companies: List[Dict[str, Any]], 
                         eudamed_lookup: Dict[str, str]) -> Dict[str, Any]:
    """
    Update pard companies with matching eudamed IDs.
    
    Args:
        supabase: Supabase client
        pard_companies: List of pard companies
        eudamed_lookup: Dictionary mapping normalized eudamed names to IDs
        
    Returns:
        Dictionary with update statistics
    """
    total = len(pard_companies)
    matched = 0
    batch_size = 100
    update_batch = []
    
    print(f"Updating pard companies with eudamed IDs...")
    
    for i, pard_company in enumerate(pard_companies):
        if i % 100 == 0:
            print(f"Processed {i}/{total} companies...")
        
        pard_id = pard_company.get('id')
        pard_name = pard_company.get('man_organisation_name', '')
        normalized_pard_name = normalize_company_name(pard_name)
        
        if normalized_pard_name in eudamed_lookup:
            eudamed_id = eudamed_lookup[normalized_pard_name]
            update_batch.append({"id": pard_id, "eudamed_id": eudamed_id})
            matched += 1
            
            # Execute batch updates
            if len(update_batch) >= batch_size:
                _execute_batch_update(supabase, update_batch)
                update_batch = []
    
    # Execute any remaining updates
    if update_batch:
        _execute_batch_update(supabase, update_batch)
    
    return {
        "total_companies": total,
        "matched_companies": matched,
        "match_percentage": round((matched / total) * 100, 2) if total > 0 else 0
    }


def _execute_batch_update(supabase: Client, batch: List[Dict[str, Any]]) -> None:
    """
    Execute batch update of pard companies.
    
    Args:
        supabase: Supabase client
        batch: List of company updates
    """
    for company in batch:
        supabase.table('pard_companies').update(
            {"eudamed_id": company["eudamed_id"]}
        ).eq("id", company["id"]).execute()
    
    print(f"Updated batch of {len(batch)} companies")


def main():
    start_time = time.time()
    
    # Connect to Supabase
    supabase = connect_to_supabase()
    
    # Fetch eudamed companies with their IDs
    eudamed_lookup = fetch_eudamed_companies(supabase)
    
    # Fetch pard companies
    pard_companies = fetch_pard_companies(supabase)
    
    # Update pard companies with matching eudamed IDs
    stats = update_pard_companies(supabase, pard_companies, eudamed_lookup)
    
    # Print summary
    print("\nUpdate Summary:")
    print(f"Total PARD companies: {stats['total_companies']}")
    print(f"Matched with EUDAMED: {stats['matched_companies']}")
    print(f"Match percentage: {stats['match_percentage']}%")
    
    elapsed_time = time.time() - start_time
    print(f"\nProcess completed in {elapsed_time:.2f} seconds")


if __name__ == "__main__":
    main() 