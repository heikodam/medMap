import os
from dotenv import load_dotenv
from supabase import create_client, Client
import openai
import sys
from helpers import fetch_all_companies

# Load environment variables
load_dotenv()

# Supabase setup
url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url, key)

# OpenAI setup
openai.api_key = os.environ.get("OPENAI_API_KEY")


def fetch_companies(iso_code):
    return supabase.table('eudamed_company').select('*')\
        .neq("scraping_status", "CLEANED_WEBSITE") \
        .eq("iso_code", iso_code) \
        .execute()

def fetch_companies_with_website(iso_code: str, batch_size=100, start=0):
    """Fetch companies with website field that needs cleaning"""
    return supabase.table('eudamed_company').select('*')\
        .eq('iso_code', iso_code)\
        .not_.is_('website', 'null')\
        .range(start, start + batch_size - 1)\
        .execute()

def clean_website(website):

    response = openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": """
                You are a helpful assistant that cleans up website URLs but does not change the url itself. 
                You will be provided with domain a value such as "http://www.domain.com or domain.at" and 
                should only return 1 url that looks like this domain.com. 
                Do not change the name or spelling of the domain itself - just clean it up. 
                If in the value there are more than 1 domain, pick the more international one and always only 
                return one. 
            """},
            {"role": "user", "content": website}
        ]
    )

    return response.choices[0].message.content.strip()

def process_all_companies(iso_code):
    # Fetch all companies
    companies = fetch_all_companies(supabase, iso_code)
    
    if not companies:
        print(f"No companies to process for {iso_code}")
        return

    total_companies = len(companies)
    print(f"Processing {total_companies} companies for {iso_code}")
    
    for i, company in enumerate(companies):
        process_company(company, i+1, total_companies)

def process_company(company, current, total):
    if company['website'] is None:
        update_data = {
            "scraping_status": "CLEANED_WEBSITE"
        }
        cleaned_website = None
    else:
        cleaned_website = clean_website(company['website'])
        update_data = {
            "website": cleaned_website,
            "original_website": company['website'],
            "scraping_status": "CLEANED_WEBSITE"
        }
    
    supabase.table('eudamed_company').update(update_data).eq('id', company['id']).execute()
    print(f"[{current}/{total}] Processed company: {company['name']} - Old: {company['website']} New Website: {cleaned_website if cleaned_website else 'N/A'}")

# Run the script
if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python clean_url.py <iso_code>")
        sys.exit(1)
    
    iso_code = sys.argv[1]
    process_all_companies(iso_code)