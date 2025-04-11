import os
import time
from datetime import datetime
from typing import List, Dict, Optional
import requests
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich import print as rprint
from supabase import Client, create_client

# Initialize Rich console for pretty printing
console = Console()

class CognismRateLimiter:
    def __init__(self):
        self.total_limit = 1000
        self.total_remaining = 1000
        self.reset_time = 0
        self.result_limit = 0
        self.result_remaining = 0
        self.result_reset = 0

    def update_from_headers(self, headers: Dict):
        """Update rate limit info from response headers"""
        self.total_limit = int(headers.get('x-rate-total-limit', 1000))
        self.total_remaining = int(headers.get('x-rate-total-limit-remaining', 0))
        self.reset_time = int(headers.get('x-rate-limit-reset', 0))
        self.result_limit = int(headers.get('x-rate-result-limit', 0))
        self.result_remaining = int(headers.get('x-rate-result-limit-remaining', 0))
        self.result_reset = int(headers.get('x-rate-result-limit-reset', 0))

    def wait_if_needed(self):
        """Wait if rate limit is reached"""
        if self.total_remaining <= 0:
            wait_time = self.reset_time + 1
            console.print(f"[yellow]Rate limit reached. Waiting for {wait_time} seconds...[/yellow]")
            time.sleep(wait_time)

class CognismClient:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://app.cognism.com/api/search/contact"
        self.rate_limiter = CognismRateLimiter()
        self.headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }

    def _handle_response(self, response: requests.Response) -> Dict:
        """Handle API response and rate limits"""
        if response.status_code == 429:
            console.print("[red]Rate limit exceeded. Waiting for reset...[/red]")
            time.sleep(60)  # Wait for 1 minute
            return None
        
        self.rate_limiter.update_from_headers(response.headers)
        return response.json() if response.status_code == 200 else None

    def enrich_contact(self, linkedin_url: str) -> Optional[Dict]:
        """Enrich contact using LinkedIn URL"""
        self.rate_limiter.wait_if_needed()
        response = requests.post(
            f"{self.base_url}/enrich",
            headers=self.headers,
            json={"linkedinUrl": linkedin_url}
        )
        return self._handle_response(response)

    def redeem_contacts(self, redeem_ids: List[str]) -> Optional[Dict]:
        """Redeem contacts using redeem IDs"""
        self.rate_limiter.wait_if_needed()
        response = requests.post(
            f"{self.base_url}/redeem",
            headers=self.headers,
            json={"redeemIds": redeem_ids}
        )
        return self._handle_response(response)

def parse_date(date_str: str) -> Optional[str]:
    """Parse date string in different formats and return ISO format string"""
    if not date_str:
        return None
        
    formats = ['%B %Y', '%Y']  # Add more formats if needed
    
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt).date().isoformat()
        except ValueError:
            continue
    
    return None

def process_contact_data(supabase: Client, contact_data: Dict, contact_id: str) -> None:
    """Process and store contact data in the database"""
    # Extract company data
    company_data = contact_data.get('account', {})
    
    # Convert timestamps to ISO format strings
    last_confirmed_company = company_data.get('lastConfirmed', 0)
    last_confirmed_company_str = datetime.fromtimestamp(last_confirmed_company/1000).isoformat() if last_confirmed_company else None
    
    # Check if company already exists
    existing_company = supabase.table('cognism_companies')\
        .select('id')\
        .eq('cognism_id', company_data.get('id'))\
        .execute()
    
    if existing_company.data:
        company_id = existing_company.data[0]['id']
    else:
        # Insert company data
        company_result = supabase.table('cognism_companies').insert({
            'cognism_id': company_data.get('id'),
            'name': company_data.get('name'),
            'domain': company_data.get('domain'),
            'type': company_data.get('type'),
            'headcount': company_data.get('headcount'),
            'size_from': company_data.get('sizeFrom'),
            'size_to': company_data.get('sizeTo'),
            'revenue': company_data.get('revenue'),
            'linkedin_url': company_data.get('linkedinUrl'),
            'website': company_data.get('website'),
            'founded': company_data.get('founded'),
            'last_confirmed': last_confirmed_company_str,
            'short_description': company_data.get('shortDescription'),
            'description': company_data.get('description')
        }).execute()
        
        company_id = company_result.data[0]['id']

        # Insert locations
        for location in company_data.get('location', []):
            # Get country data
            country_iso = None
            if location.get('country'):
                country_result = supabase.table('countries')\
                    .select('iso_code')\
                    .ilike('name', location.get('country'))\
                    .execute()
                if country_result.data:
                    country_iso = country_result.data[0]['iso_code']

            # Get or create city
            city_id = None
            if location.get('city'):
                # Try to find existing city
                city_result = supabase.table('cities')\
                    .select('id')\
                    .ilike('name', location.get('city'))\
                    .execute()
                
                if city_result.data:
                    city_id = city_result.data[0]['id']
                else:
                    # Create new city
                    new_city_result = supabase.table('cities')\
                        .insert({'name': location.get('city')})\
                        .execute()
                    if new_city_result.data:
                        city_id = new_city_result.data[0]['id']

            supabase.table('cognism_locations').insert({
                'cognism_company_id': company_id,
                'city_id': city_id,
                'country_iso_code': country_iso,
                'address_type': location.get('addressType'),
                'state': location.get('state'),
                'street': location.get('street'),
                'zip': location.get('zip')
            }).execute()

        # Insert technologies and industries as tags
        for tech in company_data.get('technologies', []):
            supabase.table('tags').insert({
                'cognism_company_id': company_id,
                'name': tech,
                'category': 'technology'
            }).execute()

        for industry in company_data.get('industry', []):
            supabase.table('tags').insert({
                'cognism_company_id': company_id,
                'name': industry,
                'category': 'industry'
            }).execute()

    # Check if contact already exists
    existing_contact = supabase.table('cognism_contacts')\
        .select('id')\
        .eq('cognism_id', contact_data.get('id'))\
        .execute()
    
    if existing_contact.data:
        cognism_contact_id = existing_contact.data[0]['id']
    else:
        # Convert contact timestamps to ISO format strings
        last_confirmed_contact = contact_data.get('lastConfirmed', 0)
        last_confirmed_contact_str = datetime.fromtimestamp(last_confirmed_contact/1000).isoformat() if last_confirmed_contact else None

        # Insert contact data
        contact_result = supabase.table('cognism_contacts').insert({
            'contact_id': contact_id,  # Add the contact_id foreign key
            'cognism_id': contact_data.get('id'),
            'cognism_redeem_id': contact_data.get('redeemId'),
            'first_name': contact_data.get('firstName'),
            'last_name': contact_data.get('lastName'),
            'full_name': contact_data.get('fullName'),
            'job_title': contact_data.get('jobTitle'),
            'email': contact_data.get('email', {}).get('address'),
            'email_quality': contact_data.get('email', {}).get('quality'),
            'email_sha256': contact_data.get('email', {}).get('sha256'),
            'linkedin_url': contact_data.get('linkedinUrl'),
            'country': contact_data.get('country'),
            'management_level': contact_data.get('managementLevel'),
            'position_start_date': contact_data.get('positionStartDate'),
            'last_confirmed': last_confirmed_contact_str,
            'privacy_notification_sent': contact_data.get('privacyNotificationSent'),
            'cognism_company_id': company_id
        }).execute()

        cognism_contact_id = contact_result.data[0]['id']

        # Insert employment history
        for job in contact_data.get('previousAccounts', []):
            start_date = parse_date(job.get('start'))
            end_date = parse_date(job.get('end'))
            
            supabase.table('cognism_employment_history').insert({
                'cognism_contact_id': cognism_contact_id,
                'company_name': job.get('name'),
                'title': job.get('title'),
                'start_date': start_date,
                'end_date': end_date
            }).execute()

        # Insert education history
        for edu in contact_data.get('education', []):
            start_date = parse_date(edu.get('start'))
            end_date = parse_date(edu.get('end'))
            
            supabase.table('cognism_education').insert({
                'cognism_contact_id': cognism_contact_id,
                'school': edu.get('school'),
                'degree': edu.get('degree'),
                'start_date': start_date,
                'end_date': end_date
            }).execute()

        # Insert job events
        for event in contact_data.get('jobLeaveEvent', []):
            try:
                event_date = datetime.strptime(event.get('date', ''), '%d.%m.%Y').date().isoformat() if event.get('date') else None
                
                supabase.table('cognism_job_events').insert({
                    'cognism_contact_id': cognism_contact_id,
                    'event_date': event_date,
                    'event_type': 'leave',
                    'from_company': event.get('from', {}).get('name'),
                    'from_title': event.get('from', {}).get('title'),
                    'to_company': event.get('to', {}).get('name'),
                    'to_title': event.get('to', {}).get('title')
                }).execute()
            except ValueError as e:
                console.print(f"[yellow]Warning: Could not parse date for job leave event: {str(e)}[/yellow]")
                continue

        for event in contact_data.get('jobJoinEvent', []):
            try:
                event_date = datetime.strptime(event.get('date', ''), '%d.%m.%Y').date().isoformat() if event.get('date') else None
                
                supabase.table('cognism_job_events').insert({
                    'cognism_contact_id': cognism_contact_id,
                    'event_date': event_date,
                    'event_type': 'join',
                    'from_company': event.get('from', {}).get('name'),
                    'from_title': event.get('from', {}).get('title'),
                    'to_company': event.get('to', {}).get('name'),
                    'to_title': event.get('to', {}).get('title')
                }).execute()
            except ValueError as e:
                console.print(f"[yellow]Warning: Could not parse date for job join event: {str(e)}[/yellow]")
                continue

        # Insert phone numbers
        for phone in contact_data.get('mobilePhoneNumbers', []):
            supabase.table('phone_numbers').insert({
                'contact_id': contact_id,  
                'number': phone.get('number'),
                'source': 'COGNISM',
                'score': phone.get('score'),
                'cognism_contact_id': cognism_contact_id
            }).execute()

def main():
    # Initialize Supabase client
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")
    cognism_api_key = os.getenv("COGNISM_API_KEY")

    if not all([supabase_url, supabase_key, cognism_api_key]):
        console.print("[red]Missing required environment variables[/red]")
        return

    supabase = create_client(supabase_url, supabase_key)
    cognism_client = CognismClient(cognism_api_key)

    # Fetch all contacts iteratively
    all_contacts = []
    page_size = 1000
    
    while True:
        # Fetch next batch of contacts
        contacts_batch = supabase.table('contacts')\
            .select('*')\
            .eq('is_relevant', True)\
            .eq('scraping_status', 'FETCHED_APOLLO_CONTACT')\
            .range(len(all_contacts), len(all_contacts) + page_size - 1)\
            .execute()
            
        if not contacts_batch.data:
            break
            
        all_contacts.extend(contacts_batch.data)
        
        if len(contacts_batch.data) < page_size:
            break
    
    # Filter to only contacts that haven't been processed
    contacts = {
        'data': [
            contact for contact in all_contacts 
            if not contact.get('scraping_status') or contact.get('scraping_status') == 'FETCHED_APOLLO_CONTACT'
        ]
    }

    if not contacts['data']:
        console.print("[yellow]No contacts to process[/yellow]")
        return

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        console=console
    ) as progress:
        task = progress.add_task("[cyan]Processing contacts...", total=len(contacts['data']))

        for contact in contacts['data']:
            # Skip if no linkedin url
            if not contact.get('linkedin_url'):
                supabase.table('contacts')\
                    .update({'scraping_status': 'FETCHED_COGNISM_CONTACT'})\
                    .eq('id', contact['id'])\
                    .execute()
                progress.advance(task)
                continue

            # Step 1: Enrich contact
            enrich_result = cognism_client.enrich_contact(contact['linkedin_url'])
            if not enrich_result or not enrich_result.get('results'):
                supabase.table('contacts')\
                    .update({'scraping_status': 'FETCHED_COGNISM_CONTACT'})\
                    .eq('id', contact['id'])\
                    .execute()
                progress.advance(task)
                continue

            # Check if contact has email or phone
            contact_preview = enrich_result['results'][0]
            if not (contact_preview.get('hasEmail') or contact_preview.get('hasMobilePhoneNumbers')):
                console.print(f"[yellow]Contact {contact['id']} has no email or phone[/yellow]")
                supabase.table('contacts')\
                    .update({'scraping_status': 'FETCHED_COGNISM_CONTACT'})\
                    .eq('id', contact['id'])\
                    .execute()
                progress.advance(task)
                continue

            # Step 2: Redeem contact
            redeem_result = cognism_client.redeem_contacts([contact_preview['redeemId']])
            if not redeem_result or not redeem_result.get('results'):
                supabase.table('contacts')\
                    .update({'scraping_status': 'FETCHED_COGNISM_CONTACT'})\
                    .eq('id', contact['id'])\
                    .execute()
                progress.advance(task)
                continue

            # Process and store the contact data
            try:
                process_contact_data(supabase, redeem_result['results'][0], contact['id'])
                supabase.table('contacts')\
                    .update({'scraping_status': 'FETCHED_COGNISM_CONTACT'})\
                    .eq('id', contact['id'])\
                    .execute()
            except Exception as e:
                console.print(f"[red]Error processing contact {contact['id']}: {str(e)}[/red]")

            progress.advance(task)

if __name__ == "__main__":
    main()
