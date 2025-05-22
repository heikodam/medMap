import os
import csv
from dotenv import load_dotenv
from supabase import create_client, Client
import time
from typing import List, Dict, Any, Tuple


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


def fetch_company_data(supabase: Client) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Fetch company data from both tables with pagination support.
    
    Args:
        supabase: Supabase client
        
    Returns:
        Tuple containing lists of eudamed companies and pard companies
    """
    # Fetch eudamed companies with pagination
    print("Fetching eudamed companies...")
    eudamed_companies = []
    page_size = 1000
    start = 0
    
    while True:
        eudamed_response = supabase.table('eudamed_companies').select("name").range(start, start + page_size - 1).execute()
        batch = eudamed_response.data
        eudamed_companies.extend(batch)
        
        if len(batch) < page_size:
            break
            
        start += page_size
        print(f"Fetched {len(eudamed_companies)} eudamed companies so far...")
    
    print(f"Found total of {len(eudamed_companies)} eudamed companies")
    
    # Fetch pard companies with pagination
    print("Fetching pard companies...")
    pard_companies = []
    start = 0
    
    while True:
        pard_response = supabase.table('pard_companies').select("man_organisation_name").range(start, start + page_size - 1).execute()
        batch = pard_response.data
        pard_companies.extend(batch)
        
        if len(batch) < page_size:
            break
            
        start += page_size
        print(f"Fetched {len(pard_companies)} pard companies so far...")
    
    print(f"Found total of {len(pard_companies)} pard companies")
    
    return eudamed_companies, pard_companies


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
                " gmbh", " corp", " corp.", " corporation", " co", " co.", " company"]
    
    for suffix in suffixes:
        if normalized.endswith(suffix):
            normalized = normalized[:-len(suffix)].strip()
    
    return normalized


def compare_companies(eudamed_companies: List[Dict[str, Any]], 
                     pard_companies: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Compare company names between both tables.
    
    Args:
        eudamed_companies: List of eudamed companies
        pard_companies: List of pard companies
        
    Returns:
        List of pard companies with match status
    """
    # Create a set of normalized eudamed company names for faster lookup
    eudamed_names_set = {normalize_company_name(company.get('name', '')) 
                         for company in eudamed_companies if company.get('name')}
    
    results = []
    
    print("Comparing company names...")
    total = len(pard_companies)
    
    for i, pard_company in enumerate(pard_companies):
        if i % 1000 == 0:
            print(f"Processed {i}/{total} companies...")
        
        pard_name = pard_company.get('man_organisation_name', '')
        normalized_pard_name = normalize_company_name(pard_name)
        
        # Check if normalized name exists in eudamed set
        match_found = normalized_pard_name in eudamed_names_set
        
        results.append({
            'pard_name': pard_name,
            'match_found': match_found
        })
    
    return results


def export_to_csv(results: List[Dict[str, Any]], output_path: str) -> None:
    """
    Export results to CSV file.
    
    Args:
        results: List of company match results
        output_path: Path to output CSV file
    """
    print(f"Writing results to {output_path}...")
    
    with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['pard_name', 'match_found']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        writer.writeheader()
        writer.writerows(results)
    
    print(f"Results written to {output_path}")


def generate_summary(results: List[Dict[str, Any]]) -> Dict[str, int]:
    """
    Generate a summary of the matching results.
    
    Args:
        results: List of company match results
        
    Returns:
        Dictionary with summary statistics
    """
    total = len(results)
    matches = sum(1 for result in results if result.get('match_found'))
    
    summary = {
        'total_pard_companies': total,
        'matches_found': matches,
        'match_percentage': round((matches / total) * 100, 2) if total > 0 else 0
    }
    
    return summary


def main():
    start_time = time.time()
    
    # Connect to Supabase
    supabase = connect_to_supabase()
    
    # Fetch data from both tables
    eudamed_companies, pard_companies = fetch_company_data(supabase)
    
    # Compare companies
    results = compare_companies(eudamed_companies, pard_companies)
    
    # Generate summary
    summary = generate_summary(results)
    print("\nSummary:")
    print(f"Total PARD companies: {summary['total_pard_companies']}")
    print(f"Matches found: {summary['matches_found']}")
    print(f"Match percentage: {summary['match_percentage']}%")
    
    # Export to CSV
    output_dir = os.path.dirname(os.path.abspath(__file__))
    output_path = os.path.join(output_dir, 'pard_eudamed_matches.csv')
    export_to_csv(results, output_path)
    
    elapsed_time = time.time() - start_time
    print(f"\nProcess completed in {elapsed_time:.2f} seconds")


if __name__ == "__main__":
    main() 