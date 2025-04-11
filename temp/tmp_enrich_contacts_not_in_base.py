import os
import asyncio
import aiohttp
from typing import List, Dict
from dotenv import load_dotenv
from supabase import create_client, Client
from enrichment.contacts.get_apollo_contacts import enrich_contacts_batch, batch_contacts

# Load environment variables
load_dotenv(override=True)

# Supabase setup
supabase_url: str = os.environ.get("SUPABASE_URL")
supabase_key: str = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(supabase_url, supabase_key)

async def fetch_contacts_to_enrich(offset: int = 0, limit: int = 1000) -> List[Dict]:
    """
    Fetch contacts that need email enrichment from Supabase.
    
    Args:
        offset (int): Number of records to skip
        limit (int): Maximum number of records to return
        
    Returns:
        List[Dict]: List of contacts that need enrichment
    """
    result = supabase.table('contacts')\
        .select('*')\
        .is_('scraping_status', 'null')\
        .is_('email', 'null')\
        .eq('is_relevant', True)\
        .range(offset, offset + limit - 1)\
        .execute()
    
    return result.data

async def update_contact_email(contact_id: str, email: str | None, email_status: str | None) -> None:
    """
    Update a contact's email and scraping status in Supabase.
    
    Args:
        contact_id (str): The UUID of the contact to update
        email (str | None): The email address to set
        email_status (str | None): The status of the email
    """
    update_data = {
        'email': email,
        'email_status': email_status,
        'scraping_status': 'FETCHED_APOLLO_CONTACT'
    }
    
    try:
        supabase.table('contacts')\
            .update(update_data)\
            .eq('id', contact_id)\
            .execute()
    except Exception as e:
        print(f"Error updating contact {contact_id}: {str(e)}")

async def process_contact_batch(session, batch: List[Dict]) -> None:
    """
    Process a batch of contacts by enriching them with Apollo data and updating Supabase.
    
    Args:
        session: The aiohttp session
        batch (List[Dict]): List of contacts to process
    """
    enriched_data = await enrich_contacts_batch(session, batch)
    
    for contact in batch:
        apollo_id = contact.get('apollo_id')
        if apollo_id and apollo_id in enriched_data:
            enriched = enriched_data[apollo_id]
            await update_contact_email(
                contact_id=contact['id'],
                email=enriched.get('email'),
                email_status=enriched.get('email_status')
            )
        else:
            # Mark as processed even if no enriched data found
            await update_contact_email(
                contact_id=contact['id'],
                email=None,
                email_status=None
            )
        
        # Small delay between updates
        await asyncio.sleep(0.5)

async def fetch_all_contacts() -> List[Dict]:
    """Fetch all contacts that need enrichment from Supabase."""
    all_contacts = []
    offset = 0
    limit = 1000

    while True:
        contacts = await fetch_contacts_to_enrich(offset, limit)
        if not contacts:
            break
        all_contacts.extend(contacts)
        if len(contacts) < limit:
            break
        offset += limit
    
    return all_contacts

async def main():
    """Main function to process all contacts that need enrichment"""
    print("\nFetching all contacts...")
    all_contacts = await fetch_all_contacts()
    total_contacts = len(all_contacts)
    
    if not total_contacts:
        print("No contacts found to process")
        return
    
    print(f"Found {total_contacts} contacts to process")
    total_processed = 0
    
    async with aiohttp.ClientSession() as session:
        contact_batches = batch_contacts(all_contacts)
        
        for i, batch in enumerate(contact_batches, 1):
            print(f"Processing batch {i}/{len(contact_batches)} ({len(batch)} contacts)")
            await process_contact_batch(session, batch)
            total_processed += len(batch)
            print(f"Processed {total_processed}/{total_contacts} contacts")
            # Add delay between batches to avoid rate limiting
            await asyncio.sleep(2)
            
    
    print(f"\nFinished processing {total_contacts} contacts")

if __name__ == "__main__":
    asyncio.run(main())


