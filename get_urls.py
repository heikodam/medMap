import os
import asyncio
import csv
from dotenv import load_dotenv
from supabase import create_client, Client
import re

# Load environment variables
load_dotenv()

# Supabase setup
url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url, key)

def format_url(url):
    # Remove http://, https://, www., and trailing /
    url = re.sub(r'^(https?://)?(www\.)?', '', url)
    url = url.rstrip('/')
    # Add stars at the beginning and end
    return f"*.{url}/*"

async def fetch_websites_batch(start, end):
    response = supabase.table("eudamed_companies") \
        .select("website") \
        .not_.is_("website", "null") \
        .range(start, end) \
        .execute()
    return [row['website'] for row in response.data]

async def fetch_and_export_websites():
    batch_size = 1000
    start = 0
    all_websites = []

    while True:
        websites_batch = await fetch_websites_batch(start, start + batch_size - 1)
        if not websites_batch:
            break
        all_websites.extend(websites_batch)
        start += batch_size
        print(f"Fetched {len(all_websites)} websites so far...")

    # Format URLs and write to CSV
    with open('formatted_websites.csv', 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        for website in all_websites:
            formatted_url = format_url(website)
            writer.writerow([formatted_url])
    
    print(f"Exported {len(all_websites)} formatted website URLs to formatted_websites.csv")

# Run the async function
asyncio.run(fetch_and_export_websites())

# import os
# import asyncio
# import csv
# from dotenv import load_dotenv
# from supabase import create_client, Client
# import re

# # Load environment variables
# load_dotenv()

# # Supabase setup
# url: str = os.environ.get("SUPABASE_URL")
# key: str = os.environ.get("SUPABASE_KEY")
# supabase: Client = create_client(url, key)

# def format_url(url):
#     # Remove http://, https://, www., and trailing /
#     url = re.sub(r'^(https?://)?(www\.)?', '', url)
#     url = url.rstrip('/')
#     # Add stars at the beginning and end
#     return f"*{url}/*"

# async def fetch_and_export_websites():
#     # Fetch rows where website is not null
#     response = supabase.table("eudamed_companies").select("website").not_.is_("website", "null").execute()
    
#     websites = [row['website'] for row in response.data]
    
#     # Format URLs and write to CSV
#     with open('formatted_websites.csv', 'w', newline='') as csvfile:
#         writer = csv.writer(csvfile)
#         for website in websites:
#             formatted_url = format_url(website)
#             writer.writerow([formatted_url])
    
#     print(f"Exported {len(websites)} formatted website URLs to formatted_websites.csv")

# # Run the async function
# asyncio.run(fetch_and_export_websites())