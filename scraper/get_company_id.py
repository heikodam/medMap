import os
import uuid
import requests
from dotenv import load_dotenv
from supabase import create_client, Client

# Load environment variables
load_dotenv()

# Supabase setup
url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url, key)

# EUDAMED API URL
base_url = "https://ec.europa.eu/tools/eudamed/api/eos"

def fetch_companies(iso_code, page=0, page_size=300):
    params = {
        "page": page,
        "pageSize": page_size,
        "size": page_size,
        "rnd": 1718288423623,
        "sort": "srn,ASC",
        "sort": "versionNumber,DESC",
        "countryIso2Code": iso_code,
        "languageIso2Code": "en"
    }
    response = requests.get(base_url, params=params)
    return response.json()

def insert_company(company, iso_code, counter):
    eudamed_uuid = company['uuid']
    
    # Clear the terminal
    os.system('cls' if os.name == 'nt' else 'clear')
    
    # Print country code and company name
    print(f"Country Code: {iso_code}")
    print(f"Company {counter}: {company['name']}")
    
    # Check if the company already exists
    existing = supabase.table('eudamed_companies').select("eudamed_uuid").eq("eudamed_uuid", eudamed_uuid).execute()
    
    if not existing.data:
        new_record = {
            "id": str(uuid.uuid4()),
            "name": company['name'],
            "scraping_status": "GOT_COMPANY_ID",
            "eudamed_uuid": eudamed_uuid
        }
        supabase.table('eudamed_companies').insert(new_record).execute()
    
def process_companies_for_country(iso_code):
    page = 0
    counter = 1
    while True:
        data = fetch_companies(iso_code, page)
        
        for company in data['content']:
            insert_company(company, iso_code, counter)
            counter += 1
        
        if data['last']:
            break
        
        page += 1

def get_country_iso_codes():
    response = supabase.table('countries').select("iso_code").execute()
    return [country['iso_code'] for country in response.data]

def process_all_countries():
    iso_codes = get_country_iso_codes()
    for iso_code in iso_codes:
        process_companies_for_country(iso_code)
    print("Finished processing all countries.")

# Run the script
process_all_countries()
