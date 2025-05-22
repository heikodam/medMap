import os
import csv
from dotenv import load_dotenv
from supabase import create_client, Client
import time
from typing import List, Dict, Any, Tuple
from fuzzywuzzy import process, fuzz


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


def compare_companies_fuzzy(eudamed_companies: List[Dict[str, Any]], 
                           pard_companies: List[Dict[str, Any]], 
                           threshold: int = 90) -> List[Dict[str, Any]]:
    """
    Compare company names between both tables using fuzzy matching.
    
    Args:
        eudamed_companies: List of eudamed companies
        pard_companies: List of pard companies
        threshold: Similarity threshold for fuzzy matching (0-100)
        
    Returns:
        List of pard companies with match status and details
    """
    # Create a list of normalized eudamed company names for fuzzy matching
    eudamed_names = [normalize_company_name(company.get('name', '')) 
                     for company in eudamed_companies if company.get('name')]
    
    # Create a set for exact matching (faster initial check)
    eudamed_names_set = set(eudamed_names)
    
    results = []
    
    print("Comparing company names with fuzzy matching...")
    total = len(pard_companies)
    
    for i, pard_company in enumerate(pard_companies):
        if i % 100 == 0:
            print(f"Processed {i}/{total} companies...")
        
        pard_name = pard_company.get('man_organisation_name', '')
        normalized_pard_name = normalize_company_name(pard_name)
        
        if not normalized_pard_name:  # Skip empty names
            results.append({
                'pard_name': pard_name,
                'exact_match': False,
                'fuzzy_match': False,
                'match_score': 0,
                'best_match': ''
            })
            continue
            
        # Check for exact match first (much faster)
        exact_match = normalized_pard_name in eudamed_names_set
        
        # If no exact match, try fuzzy matching
        if exact_match:
            best_match = normalized_pard_name
            match_score = 100
            fuzzy_match = True
        else:
            # Only use fuzzy matching if no exact match found
            best_match_result = process.extractOne(
                normalized_pard_name, 
                eudamed_names, 
                scorer=fuzz.token_sort_ratio
            )
            
            if best_match_result:
                best_match, match_score = best_match_result
                fuzzy_match = match_score >= threshold
            else:
                best_match = ''
                match_score = 0
                fuzzy_match = False
        
        results.append({
            'pard_name': pard_name,
            'exact_match': exact_match,
            'fuzzy_match': fuzzy_match,
            'match_score': match_score,
            'best_match': best_match
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
        fieldnames = ['pard_name', 'exact_match', 'fuzzy_match', 'match_score', 'best_match']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        writer.writeheader()
        writer.writerows(results)
    
    print(f"Results written to {output_path}")


def generate_summary(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Generate a summary of the matching results.
    
    Args:
        results: List of company match results
        
    Returns:
        Dictionary with summary statistics
    """
    total = len(results)
    exact_matches = sum(1 for result in results if result.get('exact_match'))
    fuzzy_matches = sum(1 for result in results if result.get('fuzzy_match') and not result.get('exact_match'))
    total_matches = exact_matches + fuzzy_matches
    
    summary = {
        'total_pard_companies': total,
        'exact_matches': exact_matches,
        'fuzzy_matches': fuzzy_matches,
        'total_matches': total_matches,
        'match_percentage': round((total_matches / total) * 100, 2) if total > 0 else 0
    }
    
    return summary


def main():
    start_time = time.time()
    
    # Connect to Supabase
    supabase = connect_to_supabase()
    
    # Fetch data from both tables
    eudamed_companies, pard_companies = fetch_company_data(supabase)
    
    # Compare companies using fuzzy matching
    results = compare_companies_fuzzy(eudamed_companies, pard_companies, threshold=85)
    
    # Generate summary
    summary = generate_summary(results)
    print("\nSummary:")
    print(f"Total PARD companies: {summary['total_pard_companies']}")
    print(f"Exact matches: {summary['exact_matches']}")
    print(f"Fuzzy matches: {summary['fuzzy_matches']}")
    print(f"Total matches: {summary['total_matches']}")
    print(f"Match percentage: {summary['match_percentage']}%")
    
    # Export to CSV
    output_dir = os.path.dirname(os.path.abspath(__file__))
    output_path = os.path.join(output_dir, 'pard_eudamed_matches_fuzzy.csv')
    export_to_csv(results, output_path)
    
    elapsed_time = time.time() - start_time
    print(f"\nProcess completed in {elapsed_time:.2f} seconds")


if __name__ == "__main__":
    main() 