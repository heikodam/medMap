import os
import requests
from dotenv import load_dotenv
from supabase import create_client, Client
import openai
from bs4 import BeautifulSoup
import sys
from helpers import fetch_all_companies

load_dotenv()

# Set up API keys and clients
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
PERPLEXITY_API_KEY = os.environ.get("PERPLEXITY_API_KEY")

openai.api_key = OPENAI_API_KEY
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def perplexity_search_website(company_name):
    """
    Use Perplexity's Sonar model to find the official website for a company.
    Returns the domain name or None if not found.
    """
    headers = {
        "Authorization": f"Bearer {PERPLEXITY_API_KEY}",
        "Content-Type": "application/json"
    }
    
    prompt = f"What is the official website for the company '{company_name}'? Please provide only the domain (with the format 'example.com' without www and without http/https) or 'N/A' if you cannot find it. Do not provide any additional explanation."
    
    data = {
        "model": "sonar",
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "max_tokens": 100
    }
    
    try:
        response = requests.post("https://api.perplexity.ai/chat/completions", headers=headers, json=data)
        response.raise_for_status()
        result = response.json()

        
        
        content = result['choices'][0]['message']['content'].strip()
        
        # Clean up the response to extract just the domain
        content = content.lower()
        if content == 'n/a' or 'n/a' in content or 'not found' in content or 'cannot find' in content:
            return None
            
        # Extract domain from the response (remove common prefixes/suffixes)
        lines = content.split('\n')
        for line in lines:
            line = line.strip()
            # Remove common text and extract domain-like strings
            if '.' in line and not line.startswith('http'):
                # Clean the line to extract just the domain
                import re
                domain_match = re.search(r'([a-zA-Z0-9-]+\.(?:[a-zA-Z]{2,}|[a-zA-Z]{2,}\.[a-zA-Z]{2,}))', line)
                if domain_match:
                    return domain_match.group(1)
        
        return None
        
    except Exception as e:
        print(f"Error searching for {company_name}: {str(e)}")
        return None

def fetch_and_update_company_websites(iso_code):
    def additional_filters(query):
        return query.is_("website", "null")
    
    # Fetch all companies
    companies = fetch_all_companies(supabase, iso_code, additional_filters)
    
    if not companies:
        print(f"No companies to process for {iso_code}")
        return

    total_companies = len(companies)
    print(f"Processing {total_companies} companies for {iso_code}")

    for i, company in enumerate(companies):
        company_name = company['name']
        
        # Use Perplexity to find the official website
        verified_website = perplexity_search_website(company_name)
        
        if verified_website:
            # Update the company record in Supabase
            supabase.table("eudamed_company").update({
                "website": verified_website,
                "scraping_status": "FETCHED_WEBSITE_PERPLEXITY"
            }).eq("id", company['id']).execute()
            print(f"[{i+1}/{total_companies}] Updated {company_name} with website: {verified_website}")
        else:
            print(f"[{i+1}/{total_companies}] Could not find website for {company_name}")
            supabase.table("eudamed_company").update({
                "scraping_status": "ERROR_WEBSITE_SEARCH",
                "error_message": "Website not found via Perplexity"
            }).eq("id", company['id']).execute()

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python fetch_company_websites.py <iso_code>")
        sys.exit(1)
    
    iso_code = sys.argv[1]
    fetch_and_update_company_websites(iso_code)
