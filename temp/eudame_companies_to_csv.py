import os
import csv
from dotenv import load_dotenv
from supabase import create_client, Client

# Load environment variables
load_dotenv()

# Supabase setup
url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url, key)

# Function to fetch companies with pagination
def fetch_companies(page_size=1000):
    companies = []
    start = 0
    while True:
        response = supabase.table("eudamed_companies").select("*").range(start, start + page_size - 1).execute()
        
        if response.data is None or len(response.data) == 0:
            break
        
        companies.extend(response.data)
        
        if len(response.data) < page_size:
            break
        
        start += page_size
        print(f"Fetched {len(companies)} companies so far...")
    
    return companies

# Fetch all companies
print("Fetching companies...")
all_companies = fetch_companies()
print(f"Total companies fetched: {len(all_companies)}")

# Define the CSV file name
csv_file = "eudamed_companies.csv"

# Write data to CSV
print(f"Writing data to {csv_file}...")
with open(csv_file, mode='w', newline='', encoding='utf-8') as file:
    if all_companies:
        fieldnames = all_companies[0].keys()
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        
        # Write the header
        writer.writeheader()
        
        # Write the data
        for company in all_companies:
            writer.writerow(company)

print(f"Data has been saved to {csv_file}")