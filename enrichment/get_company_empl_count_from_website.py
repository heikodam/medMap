import os
import requests
from bs4 import BeautifulSoup
import openai
from dotenv import load_dotenv
from supabase import create_client, Client
import time
import sys
import re
from helpers import fetch_all_companies

# Load environment variables
load_dotenv()

# Supabase setup
url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url, key)

# Set up API keys
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
PERPLEXITY_API_KEY = os.environ.get("PERPLEXITY_API_KEY")

openai.api_key = OPENAI_API_KEY

def perplexity_get_employee_count(company_name, website=None):
    """
    Use Perplexity's Sonar model to find the number of employees for a company.
    Returns the employee count as integer or None if not found.
    """
    if not PERPLEXITY_API_KEY:
        print("Error: PERPLEXITY_API_KEY not found in environment variables")
        return None
        
    headers = {
        "Authorization": f"Bearer {PERPLEXITY_API_KEY}",
        "Content-Type": "application/json"
    }
    
    # Include website in the prompt if available
    if website:
        prompt = f"How many employees work at {company_name} (website: {website}) worldwide? Please provide only the number of employees. If you cannot find a specific number, respond with 'Unknown'."
    else:
        prompt = f"How many employees work at {company_name} worldwide? Please provide only the number of employees. If you cannot find a specific number, respond with 'Unknown'."
    
    data = {
        "model": "sonar",
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "max_tokens": 150
    }
    
    try:
        response = requests.post("https://api.perplexity.ai/chat/completions", headers=headers, json=data)
        response.raise_for_status()
        result = response.json()
        
        content = result['choices'][0]['message']['content'].strip()
        
        # Extract number from response
        content_lower = content.lower()
        if 'unknown' in content_lower or 'not found' in content_lower or 'cannot find' in content_lower:
            return None
        
        # Look for numbers in the response
        # Handle various formats like "1,000", "1000", "approximately 1000", etc.
        number_patterns = [
            r'(\d{1,3}(?:,\d{3})+)',  # Numbers with commas like 1,000
            r'(\d+,?\d*)',            # General numbers
        ]
        
        for pattern in number_patterns:
            matches = re.findall(pattern, content)
            if matches:
                # Take the first number found
                number_str = matches[0].replace(',', '')
                if number_str.isdigit():
                    return int(number_str)
        
        return None
        
    except Exception as e:
        print(f"Error getting employee count for {company_name}: {str(e)}")
        return None

def process_company(company, current, total):
    website = company['website']
    company_name = company['name']
    
    if website:
        employee_count = perplexity_get_employee_count(company_name, website)
        update_data = {
            "empl_website": employee_count,
            "scraping_status": "GOT_EMPL_WEBSITE_PERPLEXITY"
        }
    else:
        # Try without website if no website available
        employee_count = perplexity_get_employee_count(company_name)
        update_data = {
            "empl_website": employee_count,
            "scraping_status": "GOT_EMPL_WEBSITE_PERPLEXITY_NO_SITE"
        }
    
    supabase.table('eudamed_company').update(update_data).eq('id', company['id']).execute()
    print(f"[{current}/{total}] Processed company: {company_name} - Employee count: {employee_count if employee_count else 'N/A'}")

def process_all_companies(iso_code):
    def additional_filters(query):
        return query.not_.is_('website', 'null')
    
    # Fetch all companies
    companies = fetch_all_companies(supabase, iso_code, additional_filters)
    
    if not companies:
        print(f"No companies to process for {iso_code}")
        return

    total_companies = len(companies)
    print(f"Processing {total_companies} companies for {iso_code}")
    
    for i, company in enumerate(companies):
        process_company(company, i+1, total_companies)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python get_company_empl_count_from_website.py <iso_code>")
        sys.exit(1)
    
    iso_code = sys.argv[1]
    process_all_companies(iso_code) 