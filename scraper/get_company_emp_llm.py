import os
import requests
from googleapiclient.discovery import build
from bs4 import BeautifulSoup
import openai
from dotenv import load_dotenv
from supabase import create_client, Client
import time

# Load environment variables
load_dotenv()

# Supabase setup
url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url, key)

# Set up API keys
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")
GOOGLE_CSE_ID = os.environ.get("GOOGLE_CSE_ID")

openai.api_key = OPENAI_API_KEY

def google_search(query, num_results=5):
    service = build("customsearch", "v1", developerKey=GOOGLE_API_KEY)
    result = service.cse().list(q=query, cx=GOOGLE_CSE_ID, num=num_results).execute()
    return result.get('items', [])

def extract_text_from_url(url, max_retries=2, backoff_factor=0.3):
    
    for attempt in range(max_retries):
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()  # Raises an HTTPError for bad responses
            soup = BeautifulSoup(response.text, 'html.parser')
            return soup.get_text()
        
        except Exception as e:
            print(f"Attempt {attempt + 1} failed: {e}")
            
            if attempt + 1 == max_retries:
                print(f"Failed to fetch {url} after {max_retries} attempts")
                return ""  # Return an empty string if all attempts fail
            
            # Exponential backoff
            time.sleep(backoff_factor * (2 ** attempt))
    
    # This line should never be reached, but just in case
    return ""

def get_employee_count(website):
    query = f"How many people work at {website}"
    search_results = google_search(query)
    
    texts = []
    for item in search_results:
        url = item['link']
        text = extract_text_from_url(url)
        texts.append(text[:5000])
    
    combined_text = "\n\n".join(texts)
    
    prompt = f"Based on the following text, how many employees work at {website} worldwide? Please respond with only a number. If you can't find a specific number, respond with 'Unknown'.\n\n{combined_text}"
    
    response = openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a helpful assistant that extracts employee counts from text."},
            {"role": "user", "content": prompt}
        ]
    )

    content = response.choices[0].message.content.strip()
    if content.isdigit():
        return int(content)
    else:
        return None

        # .not_.is_("website", None)\
        # .not_.is_("website", "null")\
        # .not_.is_("website", "")\
        # .not_.is_("website", '("",null, "null")')\


def fetch_companies(page=0, page_size=1000):
    return supabase.table('eudamed_companies').select('*')\
        .eq('iso_code', 'DE')\
        .eq('eudamed_type', 'MF')\
        .eq('scraping_status', 'GOT_COMPANY_DEVICES')\
        .not_.is_('website', 'null')\
        .range(page*page_size, (page+1)*page_size-1)\
        .execute()

def process_company(company):
    website = company['website']
    if website:
        employee_count = get_employee_count(website)
        update_data = {
            "empl_website": employee_count,
            "scraping_status": "GOT_EMPL_WEBSITE"
        }
    else:
        update_data = {
            "scraping_status": "GOT_EMPL_WEBSITE"
        }
    
    supabase.table('eudamed_companies').update(update_data).eq('id', company['id']).execute()
    print(f"Processed company: {company['name']} - Employee count: {employee_count if 'empl_website' in update_data else 'N/A'}")

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
process_all_companies()