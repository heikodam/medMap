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
base_url = "https://ec.europa.eu/tools/eudamed/api/certificates/search/"

def fetch_certificates(page=0, page_size=300):
    params = {
        "page": page,
        "pageSize": page_size,
        "size": page_size,
        "iso2Code": "en",
        "entityTypeCode": "certificate.certificates",
        "languageIso2Code": "en"
    }
    response = requests.get(base_url, params=params)
    return response.json()

def insert_certificate(certificate, counter):
    eudamed_uuid = certificate['uuid']
    
    # Clear the terminal
    os.system('cls' if os.name == 'nt' else 'clear')
    
    # Print certificate number and counter
    print(f"Certificate {counter}: {certificate['certificateNumber']}")
    
    # Check if the certificate already exists
    existing = supabase.table('eudamed_certificates').select("eudamed_uuid").eq("eudamed_uuid", eudamed_uuid).execute()
    
    if not existing.data:
        new_record = {
            "id": str(uuid.uuid4()),
            "eudamed_uuid": eudamed_uuid,
            "certificate_number": certificate['certificateNumber'],
            "scraping_status": "GOT_CERTIFICATE_ID"
        }
        supabase.table('eudamed_certificates').insert(new_record).execute()

def process_certificates():
    page = 0
    counter = 1
    while True:
        data = fetch_certificates(page)
        
        for certificate in data['content']:
            insert_certificate(certificate, counter)
            counter += 1
        
        if data['last']:
            break
        
        page += 1

# Run the script
process_certificates()
print("Finished processing all certificates.")
