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
    return [result['url'] for result in search_results.get("webPages", {}).get("value", [])]

def verify_website_with_llm(company_name, urls):
    # print(f"Verifying websites for {company_name}: {urls}")
    urls_str = "\n".join(urls)
    prompt = f"Given the company name '{company_name}' and the following list of URLs:\n\n{urls_str}\n\nWhich URL is most likely to be the official website for the company? If none of them seem to be the official website, respond with 'N/A'. Please provide only the domain (with the format 'example.com' (no www and no http)) or 'N/A' as your answer, with no additional explanation."
    
    response = openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a helpful assistant that verifies company websites."},
            {"role": "user", "content": prompt}
        ]
    )

    content = response.choices[0].message.content.strip()
    return content if content.lower() != 'n/a' else None

def fetch_and_update_company_websites():
    batch_size = 1000
    offset = 0

    while True:
        # Fetch companies from Supabase
        companies = supabase.table("eudamed_companies").select("*").eq("iso_code", "CH").is_("website", "null").neq("scraping_status", "SEARCHED_FOR_WEBSITE").range(offset, offset + batch_size - 1).execute()
        
        if not companies.data:
            break  # No more companies to process

        for company in companies.data:
            company_name = company['name']
            query = f"{company_name} official website"
            search_results = bing_search(query)

            if search_results:
                # Verify the websites with LLM
                verified_website = verify_website_with_llm(company_name, search_results)
                
                if verified_website:
                    # Update the company record in Supabase
                    supabase.table("eudamed_companies").update({
                        "website": verified_website,
                        "scraping_status": "SEARCHED_FOR_WEBSITE"
                    }).eq("id", company['id']).execute()
                    print(f"Updated {company_name} with website: {verified_website}")
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
            
            

if __name__ == "__main__":
    fetch_and_update_company_websites()
