import os
import requests
from dotenv import load_dotenv
from supabase import create_client, Client
import openai
from bs4 import BeautifulSoup

load_dotenv()

# Set up API keys and clients
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
BING_SEARCH_V7_SUBSCRIPTION_KEY = os.environ.get("BING_SEARCH_V7_SUBSCRIPTION_KEY")
BING_SEARCH_V7_ENDPOINT = os.environ.get("BING_SEARCH_V7_ENDPOINT")

openai.api_key = OPENAI_API_KEY
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def bing_search(query):
    headers = {"Ocp-Apim-Subscription-Key": BING_SEARCH_V7_SUBSCRIPTION_KEY}
    params = {"q": query, "count": 5, "offset": 0, "mkt": "en-US"}
    response = requests.get(BING_SEARCH_V7_ENDPOINT, headers=headers, params=params)
    response.raise_for_status()
    search_results = response.json()
    return search_results.get("webPages", {}).get("value", [])

def extract_domain(url):
    from urllib.parse import urlparse
    parsed_url = urlparse(url)
    domain = parsed_url.netloc
    if domain.startswith('www.'):
        domain = domain[4:]
    return domain

def verify_website_with_llm(company_name, website):
    prompt = f"Does the website '{website}' appear to be the correct official website for the company '{company_name}'? Please respond with 'Yes' or 'No' and a brief explanation."
    
    response = openai.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are a helpful assistant that verifies company websites."},
            {"role": "user", "content": prompt}
        ]
    )

    content = response.choices[0].message.content.strip()
    return content.lower().startswith("yes")

def fetch_and_update_company_websites():
    batch_size = 1000
    offset = 0

    while True:
        # Fetch companies from Supabase
        companies = supabase.table("eudamed_companies").select("*").eq("iso_code", "DE").is_("website", "null").neq("scraping_status", "SEARCHED_FOR_WEBSITE").range(offset, offset + batch_size - 1).execute()
        
        if not companies.data:
            break  # No more companies to process

        for company in companies.data:
            company_name = company['name']
            query = f"{company_name} official website"
            search_results = bing_search(query)

            if search_results:
                potential_website = extract_domain(search_results[0]['url'])
                
                # Verify the website with LLM
                if verify_website_with_llm(company_name, potential_website):
                    # Update the company record in Supabase
                    supabase.table("eudamed_companies").update({
                        "website": potential_website,
                        "scraping_status": "SEARCHED_FOR_WEBSITE"
                    }).eq("id", company['id']).execute()
                    print(f"Updated {company_name} with website: {potential_website}")
                else:
                    print(f"Could not verify website for {company_name}")
                    supabase.table("eudamed_companies").update({
                        "scraping_status": "SEARCHED_FOR_WEBSITE"
                    }).eq("id", company['id']).execute()
            else:
                print(f"No website found for {company_name}")
                supabase.table("eudamed_companies").update({
                    "scraping_status": "SEARCHED_FOR_WEBSITE"
                }).eq("id", company['id']).execute()

        offset += batch_size

if __name__ == "__main__":
    fetch_and_update_company_websites()
