import os
import csv
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Supabase setup
supabase_url: str = os.environ.get("SUPABASE_URL")
supabase_key: str = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(supabase_url, supabase_key)

INPUT_CSV = './cognism_to_supabase/cognism_enriched.csv'
OUTPUT_CSV = './cognism_to_supabase/processed_cognism.csv'

def company_exists(website):
    result = supabase.table('cognism_company').select('id').eq('website', website).execute()
    return len(result.data) > 0

def contact_exists(cognism_id):
    result = supabase.table('cognism_contact').select('id').eq('cognism_id', cognism_id).execute()
    return len(result.data) > 0

def insert_company(row):
    company_data = {
        'name': row['Matched Company'],
        'office_phone': row['Office'],
        'hq': row['HQ'],
        'headcount': row['Headcount'],
        'industries': row['Industries'],
        'sic': row['SIC'],
        'isic': row['ISIC'],
        'naics': row['NAICS'],
        'revenue': row['Revenue'],
        'website': row['Matched Website'],
        'country': row['Company Country'],
        'state': row['Company State'],
        'city': row['Company City'],
        'address': row['Company Address'],
        'zip': row['Company ZIP'],
        'location': row['Company Location'],
        'linkedin_url': row['Company Linkedin Handle'],
        'type': row['Company Type'],
        'tech': row['Company Tech'],
        'eudamed_company_id': row['medmap_company_id']
    }
    result = supabase.table('cognism_company').insert(company_data).execute()
    return result.data[0]['id'] if result.data else None

def insert_contact(row, company_id):
    contact_data = {
        'cognism_id': row['Cognism ID'],
        'job_title': row['Matched Job Title'],
        'seniority': row['Seniority'],
        'mobile_phone': row['Mobile'],
        'direct_phone': row['Direct'],
        'department': row['Department'],
        'country': row['Person Country'],
        'state': row['Person State'],
        'city': row['Person City'],
        'email': row['Cognism Email'],
        'email_verified': row['Cognism Email Verified'],
        'linkedin_url': row['Personal LinkedIn URL'],
        'optimistic_match': row['Optimistic Match'],
        'eudamed_company_id': row['medmap_company_id'],
        'eudamed_contactperson_id': row['medmap_contact_id']
    }
    result = supabase.table('cognism_contact').insert(contact_data).execute()
    return result.data[0]['id'] if result.data else None

def process_csv():
    with open(INPUT_CSV, 'r') as infile, open(OUTPUT_CSV, 'w', newline='') as outfile:
        reader = csv.DictReader(infile)
        writer = csv.DictWriter(outfile, fieldnames=reader.fieldnames)
        writer.writeheader()

        for row in reader:
            if not contact_exists(row['Cognism ID']):
                company_id = None
                if not company_exists(row['Matched Website']):
                    company_id = insert_company(row)
                
                if insert_contact(row, company_id):
                    print(f"Processed: {row['Cognism ID']}")
                else:
                    writer.writerow(row)
            else:
                print(f"Skipped existing contact: {row['Cognism ID']}")

process_csv()
