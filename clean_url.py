import os
from dotenv import load_dotenv
from supabase import create_client, Client
import openai

# Load environment variables
load_dotenv()

# Supabase setup
url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url, key)

# OpenAI setup
openai.api_key = os.environ.get("OPENAI_API_KEY")


def fetch_companies(page=0, page_size=1000):
    return supabase.table('eudamed_companies').select('*')\
        .or_('scraping_status.eq.GOT_COMPANY_DEVICES,scraping_status.eq.GOT_EMPL_WEBSITE')\
        .range(page*page_size, (page+1)*page_size-1)\
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

def process_company(company):

    if company['website'] is None:
        update_data = {
            "scraping_status": "CLEANED_WEBSITE"
        }
    else:
        cleaned_website = clean_website(company['website'])
        update_data = {
            "website": cleaned_website,
            "original_website": company['website'],
            "scraping_status": "CLEANED_WEBSITE"
        }
    
    supabase.table('eudamed_companies').update(update_data).eq('id', company['id']).execute()
    print(f"Processed company: {company['name']} - Old: {company['website']} New Website: {cleaned_website if 'website' in update_data else 'N/A'}")

def process_all_companies():
    page = 0
    while True:
        companies = fetch_companies(page)
        if not companies.data:
            break
        
        for company in companies.data:
            process_company(company)

        
        page += 1

    
    print("Finished processing all companies.")

# Run the script
if __name__ == "__main__":
    process_all_companies()