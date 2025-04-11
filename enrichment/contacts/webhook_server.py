from fastapi import FastAPI, Request
from dotenv import load_dotenv
from supabase import create_client, Client
import os
import uvicorn
import json
from datetime import datetime
import pathlib

# Load environment variables
load_dotenv()

# Supabase setup
supabase_url: str = os.environ.get("SUPABASE_URL")
supabase_key: str = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(supabase_url, supabase_key)

app = FastAPI()

# Get the absolute path to the temp_data directory
TEMP_DATA_DIR = pathlib.Path(__file__).parent / "temp_data"
TEMP_DATA_DIR.mkdir(parents=True, exist_ok=True)

print(f"Webhook server starting. Files will be saved to: {TEMP_DATA_DIR}")

@app.post("/webhook")
async def handle_webhook(request: Request):
    """Handle webhook POST requests from Apollo"""
    print("\n--- Received webhook request ---")
    data = await request.json()
    
    print(f"Total people in webhook: {len(data.get('people', []))}")
    
    # Process each person's phone numbers
    for person in data.get('people', []):
        apollo_id = person.get('id')
        phone_numbers = person.get('phone_numbers', [])

        print(f"\nProcessing Apollo ID: {apollo_id}")
        print(f"Number of phone numbers found: {len(phone_numbers)}")
        
        if not apollo_id or not phone_numbers:
            print("Skipping - no apollo_id or phone numbers")
            continue
            
        # Get the contact_id from our database using apollo_id
        result = supabase.table('contacts').select('id').eq('apollo_id', apollo_id).execute()
        if not result.data:
            print(f"Contact with Apollo ID {apollo_id} not found in database")
            continue
            
        contact_id = result.data[0]['id']
        
        # Insert each phone number
        for phone in phone_numbers:
            sanitized_number = phone.get('sanitized_number')
            if sanitized_number:
                try:
                    # Check if phone number already exists for this contact
                    existing_phone = supabase.table('phone_numbers')\
                        .select('id')\
                        .eq('contact_id', contact_id)\
                        .eq('number', sanitized_number)\
                        .execute()
                        
                    if existing_phone.data:
                        print(f"Phone number {sanitized_number} already exists for contact {apollo_id}")
                        continue
                    
                    # Insert into phone_numbers table
                    supabase.table('phone_numbers').insert({
                        'contact_id': contact_id,
                        'number': sanitized_number,
                        'source': 'APOLLO'
                    }).execute()
                    print(f"Successfully stored phone number {sanitized_number} for contact {apollo_id}")
                except Exception as e:
                    print(f"Error storing phone number: {str(e)}")
    
    print("--- Webhook processing complete ---\n")
    return {"status": "success"}

if __name__ == "__main__":
    print(f"\nStarting webhook server on port 8000")
    print(f"Waiting for webhook calls from Apollo...")
    uvicorn.run(app, host="0.0.0.0", port=8000) 