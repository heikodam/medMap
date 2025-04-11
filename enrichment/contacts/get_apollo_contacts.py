import os
import json
import asyncio
import aiohttp
from datetime import datetime
from typing import List, Dict, Set
from dotenv import load_dotenv
from supabase import create_client, Client
from enrichment.helpers import fetch_all_companies
from fuzzywuzzy import fuzz, process
import openai

# Load environment variables
load_dotenv(override=True)

# Supabase setup
supabase_url: str = os.environ.get("SUPABASE_URL")
supabase_key: str = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(supabase_url, supabase_key)

# OpenAI setup
openai.api_key = os.environ.get("OPENAI_API_KEY")

# Apollo API setup
APOLLO_API_KEY = os.environ.get("APOLLO_API_KEY")
APOLLO_API_URL = "https://api.apollo.io/api/v1/mixed_people/search"

def load_job_titles() -> Dict[str, List[str]]:
    """Load job titles from the JSON file"""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    job_titles_path = os.path.join(current_dir, "job_titles.json")
    
    with open(job_titles_path, 'r') as f:
        return json.load(f)

def load_excluded_titles() -> Set[str]:
    """Load excluded titles from the JSON file and prepare them for fuzzy matching"""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    excluded_titles_path = os.path.join(current_dir, "excluded_titles.json")
    
    with open(excluded_titles_path, 'r') as f:
        data = json.load(f)
    
    # Convert all titles to lowercase for case-insensitive matching
    excluded_titles = {title.lower() for title in data.get('project_management_titles', [])}
    return excluded_titles

def is_project_management_title(title: str, excluded_titles: Set[str]) -> bool:
    """
    Check if a title matches any of the excluded project management titles using fuzzy matching.
    
    Args:
        title (str): The title to check
        excluded_titles (Set[str]): Set of excluded titles for matching
    
    Returns:
        bool: True if the title matches any excluded title, False otherwise
    """
    if not title:
        return False
    
    # Convert title to lowercase for consistency
    title = title.lower()
    
    # Direct substring match first (for efficiency)
    if any(excluded in title for excluded in excluded_titles):
        return True
    
    # Use fuzzywuzzy for more sophisticated matching
    # Get the best match ratio for the title against all excluded titles
    best_match, score = process.extractOne(title, excluded_titles, scorer=fuzz.token_sort_ratio)
    
    # Consider it a match if the similarity score is above 85
    # This threshold can be adjusted based on needs
    return score >= 85

def is_matching_job_title(title: str, job_titles: List[str]) -> bool:
    """
    Check if a title matches any of the job titles using fuzzy matching.
    
    Args:
        title (str): The title to check
        job_titles (List[str]): List of job titles to match against
    
    Returns:
        bool: True if the title matches any job title, False otherwise
    """
    if not title:
        return False
    
    title = title.lower()
    best_match, score = process.extractOne(title, job_titles, scorer=fuzz.token_sort_ratio)
    return score >= 80

def clean_domain(url: str) -> str:
    """Clean domain by removing http://, https://, and www."""
    if not url:
        return ""
    
    domain = url.lower()
    for prefix in ['https://', 'http://', 'www.']:
        domain = domain.replace(prefix, '')
    return domain.strip('/')

def build_apollo_query_params(domain: str, job_titles: list) -> list[tuple]:
    """
    Build query parameters for the Apollo API request.
    
    Args:
        domain (str): The cleaned domain to search for.
        job_titles (list): A list of job titles to search within the organization.
        
    Returns:
        list[tuple]: A list of query parameter tuples.
    """
    query_params = [("q_organization_domains", domain)]
    # Use "person_titles[]" to ensure that Apollo receives an array.
    query_params.extend([("person_titles[]", title) for title in job_titles])
    return query_params

def get_rate_limit_wait_time(response) -> tuple[int, str]:
    """
    Calculate wait time based on Apollo API rate limit headers.
    Uses shorter wait times with more frequent retries.
    Returns tuple of (wait_time_in_seconds, rate_limit_type).
    """
    # Get rate limit headers
    minute_left = int(response.headers.get('x-minute-requests-left', 0))
    hourly_left = int(response.headers.get('x-hourly-requests-left', 0))
    daily_left = int(response.headers.get('x-daily-requests-left', 0))
    
    # If any limits are exceeded (0 or negative), calculate wait time
    if minute_left <= 0:
        return 30, 'minute'  # Wait 30 seconds for minute limit
    elif hourly_left <= 0:
        return 600, 'hour'  # Wait 10 minutes for hourly limit
    elif daily_left <= 0:
        return 3600, 'day'  # Wait 1 hour for daily limit
    
    return 0, None

def print_rate_limit_info(response) -> None:
    """Print current rate limit information from response headers."""
    print("\nApollo API Rate Limit Status:")
    print(f"Minute: {response.headers.get('x-minute-usage', '?')}/{response.headers.get('x-rate-limit-minute', '?')} (Remaining: {response.headers.get('x-minute-requests-left', '?')})")
    print(f"Hour: {response.headers.get('x-hourly-usage', '?')}/{response.headers.get('x-rate-limit-hourly', '?')} (Remaining: {response.headers.get('x-hourly-requests-left', '?')})")
    print(f"Day: {response.headers.get('x-daily-usage', '?')}/{response.headers.get('x-rate-limit-daily', '?')} (Remaining: {response.headers.get('x-daily-requests-left', '?')})")

async def handle_rate_limit_retry(response, attempt: int, max_retries: int) -> bool:
    """
    Handle rate limit retry logic with progressive backoff.
    Returns True if should retry, False if should give up.
    
    Args:
        response: The API response
        attempt: Current attempt number
        max_retries: Maximum number of retries allowed
    """
    if attempt >= max_retries:
        return False
        
    wait_time, limit_type = get_rate_limit_wait_time(response)
    if wait_time > 0:
        print(f"\nRate limit reached. Current rate limit status:")
        print_rate_limit_info(response)
        print(f"\nWaiting {wait_time} seconds for {limit_type} limit...")
        
        # For longer waits (hour/day), print countdown every minute
        if wait_time >= 60:
            for remaining in range(wait_time, 0, -60):
                print(f"⏳ {remaining} seconds remaining...")
                await asyncio.sleep(min(60, remaining))
        else:
            await asyncio.sleep(wait_time)
        return True
    
    return False

async def search_contacts(session, domain: str, job_titles: list) -> dict:
    """
    Search for contacts using Apollo API.
    
    Now, q_organization_domains and person_titles are passed as URL query parameters.
    
    Args:
        session: The aiohttp session for making the HTTP request.
        domain (str): The cleaned domain to search for.
        job_titles (list): A list of job titles to include in the search.
        
    Returns:
        dict: The JSON response from Apollo if the request succeeds, otherwise None.
    """
    headers = {
        "Content-Type": "application/json",
        "Cache-Control": "no-cache",
        "X-Api-Key": APOLLO_API_KEY
    }
    
    # Build query parameters for the request URL
    query_params = build_apollo_query_params(domain, job_titles)
    
    # Prepare the remaining JSON body
    payload = {
        "api_key": APOLLO_API_KEY,
        "page": 1,
        "per_page": 100  # Maximum allowed by Apollo
    }
    
    max_retries = 5  # Increased from 3 to 5 since we're retrying more frequently
    
    for attempt in range(max_retries):
        try:
            async with session.post(APOLLO_API_URL, headers=headers, params=query_params, json=payload) as response:
                response_text = await response.text()
                response_json = await response.json()
                
                if response.status == 200:
                    return response_json
                elif response.status == 429:
                    should_retry = await handle_rate_limit_retry(response, attempt, max_retries)
                    if should_retry:
                        continue
                    else:
                        print(f"Failed to fetch contacts for {domain} after {max_retries} attempts due to rate limiting.")
                        return None
                else:
                    print(response_text)
                    print(f"Failed to fetch contacts for {domain}. Status: {response.status}")
                    return None
        except Exception as e:
            print(f"Error fetching contacts for {domain}: {str(e)}")
            return None
    
    return None

def filter_matching_contacts(contacts: List[Dict], company_domain: str, job_titles: List[str]) -> tuple[List[Dict], List[Dict], List[Dict]]:
    """
    Filter contacts into three lists:
    1. Matching job titles (positive matches)
    2. Project management titles (excluded)
    3. Other titles (no match with either)
    
    Args:
        contacts (List[Dict]): List of all contacts
        company_domain (str): Company domain to match against
        job_titles (List[str]): List of job titles to match against
    
    Returns:
        tuple[List[Dict], List[Dict], List[Dict]]: Tuple of (matching_contacts, excluded_contacts, other_contacts)
    """
    if not contacts:
        return [], [], []
    
    company_domain = clean_domain(company_domain)
    matching_contacts = []
    excluded_contacts = []
    other_contacts = []
    excluded_titles = load_excluded_titles()
    
    # Convert job titles to lowercase for matching
    job_titles = [title.lower() for title in job_titles]
    
    for contact in contacts:
        org = contact.get('organization', {})
        contact_domain = clean_domain(org.get('website_url', ''))
        
        if contact_domain == company_domain:
            title = contact.get('title', '')
            
            # First check if it matches our target job titles
            if is_matching_job_title(title, job_titles):
                matching_contacts.append(contact)
            # Then check if it matches excluded titles
            elif is_project_management_title(title, excluded_titles):
                excluded_contacts.append(contact)
            # If neither, add to other contacts
            else:
                other_contacts.append(contact)
    
    return matching_contacts, excluded_contacts, other_contacts

def split_into_batches(items: List[str], batch_size: int = 98) -> List[List[str]]:
    """Split a list of items into batches of specified size"""
    return [items[i:i + batch_size] for i in range(0, len(items), batch_size)]

def analyze_job_title_with_llm(title: str) -> Dict:
    """
    Use OpenAI's GPT-4 to analyze if a job title is relevant for medtech regulatory software.
    
    Args:
        title (str): The job title to analyze
    
    Returns:
        Dict: Dictionary containing relevance and category
    """
    if not title:
        return {"is_relevant": False, "job_category": "Unknown"}
    
    prompt = """You are an expert in medical device industry sales and lead qualification. Your task is to analyze job titles to identify potential decision-makers for medical device regulatory compliance software.

Key responsibilities you're looking for:
- Regulatory affairs/compliance
- Quality management
- Risk management
- Medical device documentation
- Compliance strategy
- Quality assurance
- Regulatory submissions
- Standards compliance (ISO 13485, MDR, FDA)

Analyze this job title: "{title}"

Respond only with a JSON object in this exact format:
{{
    "is_relevant": true/false,
    "job_category": "brief category"
}}

Where:
- is_relevant: true if they likely deal with medical device regulations/quality/compliance
- job_category: exactly one of: CLINICAL, REGULATORY, QUALITY, CROSS_FUNCTIONAL, PMS, OTHER, NOT_RELEVANT - if is_relevant is false then pick NOT_RELEVANT"""

    try:
        response = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a lead qualification expert for medtech regulatory software."},
                {"role": "user", "content": prompt.format(title=title)}
            ],
            temperature=0.1
        )
        
        result = json.loads(response.choices[0].message.content.strip())
        return result
    except Exception as e:
        print(f"Error analyzing job title with LLM: {str(e)}")
        return {"is_relevant": False, "job_category": "Error"}

async def process_other_contacts_with_llm(other_contacts: List[Dict]) -> tuple[List[Dict], List[Dict]]:
    """
    Process other_contacts with LLM to further categorize them.
    Moves relevant contacts to matching_contacts with job_category at root level,
    and non-relevant contacts to excluded_contacts without job_category.
    
    Args:
        other_contacts (List[Dict]): List of contacts to analyze
    
    Returns:
        tuple[List[Dict], List[Dict]]: Tuple of (additional_matching_contacts, additional_excluded_contacts)
    """
    additional_matching = []
    additional_excluded = []
    
    for contact in other_contacts:
        title = contact.get('title', '')
        llm_analysis = analyze_job_title_with_llm(title)
        
        if llm_analysis['is_relevant']:
            # Add job_category to root level and add to matching contacts
            contact['job_category'] = llm_analysis['job_category']
            additional_matching.append(contact)
        else:
            # Move to excluded contacts without job_category
            additional_excluded.append(contact)
        
        # Add a small delay to avoid hitting OpenAI rate limits
        await asyncio.sleep(0.5)
    
    return additional_matching, additional_excluded

async def insert_apollo_company(organization: Dict) -> None:
    """
    Insert minimal Apollo company data into apollo_companies table.
    
    Args:
        organization (Dict): Organization data from Apollo contact
    """
    if not organization or not organization.get('id'):
        return
        
    # Check if company already exists
    existing_company = supabase.table('apollo_companies').select('apollo_id').eq('apollo_id', organization['id']).execute()
    
    if existing_company.data:
        return
        
    # Prepare minimal company data
    company_data = {
        'apollo_id': organization.get('id'),
        'name': organization.get('name'),
        'website_url': organization.get('website_url'),
        'linkedin_url': organization.get('linkedin_url'),
        'primary_domain': clean_domain(organization.get('website_url', ''))
    }
    
    try:
        supabase.table('apollo_companies').insert(company_data).execute()
        # print(f"Inserted Apollo company: {organization.get('name')}")
    except Exception as e:
        print(f"Error inserting Apollo company: {str(e)}")

async def save_contacts_to_database(matching_contacts: List[Dict], excluded_contacts: List[Dict]) -> None:
    """
    Save contacts and their employment history to the database.
    
    Args:
        matching_contacts (List[Dict]): List of contacts matching job titles (relevant)
        excluded_contacts (List[Dict]): List of contacts with excluded titles (not relevant)
    """
    all_contacts = []
    
    # Prepare matching contacts (is_relevant = true)
    for contact in matching_contacts:
        contact_data = {
            'apollo_id': contact.get('id'),
            'first_name': contact.get('first_name'),
            'last_name': contact.get('last_name'),
            'name': contact.get('name'),
            'linkedin_url': contact.get('linkedin_url'),
            'title': contact.get('title'),
            'email_status': contact.get('email_status'),
            'photo_url': contact.get('photo_url'),
            'twitter_url': contact.get('twitter_url'),
            'github_url': contact.get('github_url'),
            'facebook_url': contact.get('facebook_url'),
            'extrapolated_email_confidence': contact.get('extrapolated_email_confidence'),
            'headline': contact.get('headline'),
            'email': contact.get('email'),
            'organization_apollo_id': contact.get('organization', {}).get('id'),
            'organization_name': contact.get('organization', {}).get('name'),
            'organization_website': contact.get('organization', {}).get('website_url'),
            'organization_linkedin_url': contact.get('organization', {}).get('linkedin_url'),
            'state': contact.get('state'),
            'city': contact.get('city'),
            'country': contact.get('country'),
            'seniority': contact.get('seniority'),
            'email_domain_catchall': contact.get('email_domain_catchall'),
            'is_relevant': True,
            'job_category': contact.get('job_category')  # This was added by LLM analysis
        }
        all_contacts.append(contact_data)
    
    # Prepare excluded contacts (is_relevant = false)
    for contact in excluded_contacts:
        contact_data = {
            'apollo_id': contact.get('id'),
            'first_name': contact.get('first_name'),
            'last_name': contact.get('last_name'),
            'name': contact.get('name'),
            'linkedin_url': contact.get('linkedin_url'),
            'title': contact.get('title'),
            'email_status': contact.get('email_status'),
            'photo_url': contact.get('photo_url'),
            'twitter_url': contact.get('twitter_url'),
            'github_url': contact.get('github_url'),
            'facebook_url': contact.get('facebook_url'),
            'extrapolated_email_confidence': contact.get('extrapolated_email_confidence'),
            'headline': contact.get('headline'),
            'email': None,  # Set email to NULL for excluded contacts
            'organization_apollo_id': contact.get('organization', {}).get('id'),
            'organization_name': contact.get('organization', {}).get('name'),
            'organization_website': contact.get('organization', {}).get('website_url'),
            'organization_linkedin_url': contact.get('organization', {}).get('linkedin_url'),
            'state': contact.get('state'),
            'city': contact.get('city'),
            'country': contact.get('country'),
            'seniority': contact.get('seniority'),
            'email_domain_catchall': contact.get('email_domain_catchall'),
            'is_relevant': False,
            'job_category': None
        }
        all_contacts.append(contact_data)
    
    # Insert contacts and get their IDs
    for contact_data in all_contacts:
        apollo_id = contact_data['apollo_id']
        
        # Check if contact already exists
        existing_contact = supabase.table('contacts').select('id').eq('apollo_id', apollo_id).execute()
        
        if existing_contact.data:
            # print(f"Contact with Apollo ID {apollo_id} already exists, skipping...")
            continue
        
        # Get the original contact object to access organization data
        original_contact = next(
            (c for c in matching_contacts + excluded_contacts if c.get('id') == apollo_id),
            None
        )
        
        if not original_contact:
            continue
            
        try:
            # Try to insert the contact
            result = supabase.table('contacts').insert(contact_data).execute()
            
            if not result.data:
                print(f"Failed to insert contact with Apollo ID {apollo_id}")
                continue
                
            contact_id = result.data[0]['id']
            
            # Insert employment history
            for employment in original_contact.get('employment_history', []):
                employment_data = {
                    'contact_id': contact_id,
                    'current': employment.get('current'),
                    'description': employment.get('description'),
                    'end_date': employment.get('end_date'),
                    'organization_apollo_id': employment.get('organization_id'),
                    'organization_name': employment.get('organization_name'),
                    'raw_address': employment.get('raw_address'),
                    'start_date': employment.get('start_date'),
                    'title': employment.get('title')
                }
                
                supabase.table('apollo_employment_history').insert(employment_data).execute()
                
        except Exception as e:
            if 'violates foreign key constraint "fk_organization"' in str(e):
                # Insert the Apollo company first
                await insert_apollo_company(original_contact.get('organization', {}))
                # Try inserting the contact again
                try:
                    result = supabase.table('contacts').insert(contact_data).execute()
                    if result.data:
                        contact_id = result.data[0]['id']
                        # Insert employment history
                        for employment in original_contact.get('employment_history', []):
                            employment_data = {
                                'contact_id': contact_id,
                                'current': employment.get('current'),
                                'description': employment.get('description'),
                                'end_date': employment.get('end_date'),
                                'organization_apollo_id': employment.get('organization_id'),
                                'organization_name': employment.get('organization_name'),
                                'raw_address': employment.get('raw_address'),
                                'start_date': employment.get('start_date'),
                                'title': employment.get('title')
                            }
                            supabase.table('apollo_employment_history').insert(employment_data).execute()
                except Exception as inner_e:
                    print(f"Failed to insert contact after adding company. Error: {str(inner_e)}")
            else:
                print(f"Error inserting contact: {str(e)}")
    
    # print(f"Processed {len(all_contacts)} contacts")

def batch_contacts(contacts: List[Dict], batch_size: int = 10) -> List[List[Dict]]:
    """Split contacts into batches of specified size"""
    return [contacts[i:i + batch_size] for i in range(0, len(contacts), batch_size)]

async def enrich_contacts_batch(session, contacts: List[Dict]) -> Dict[str, Dict]:
    """
    Enrich a batch of contacts (up to 10) using Apollo's bulk match endpoint.
    Uses only Apollo IDs for reliable matching.
    """
    APOLLO_BULK_MATCH_URL = "https://api.apollo.io/api/v1/people/bulk_match"
    WEBHOOK_URL = os.environ.get("WEBHOOK_URL", "")
    
    if not WEBHOOK_URL:
        print("⚠️  Warning: WEBHOOK_URL not set in environment variables")
        return {}
    
    headers = {
        "Content-Type": "application/json",
        "Cache-Control": "no-cache",
        "X-Api-Key": APOLLO_API_KEY
    }
    
    # Prepare the details array using only Apollo IDs
    # Improve this. This is a bad position, should live in a different function
    details = []
    for contact in contacts:
        apollo_id = contact.get('apollo_id')
        if apollo_id:
            contact_details = {
                "id": apollo_id
            }
            details.append(contact_details)
    
    if not details:
        return {}
    
    params = {
        "reveal_personal_emails": "true",
        "reveal_phone_number": "true",
        "webhook_url": WEBHOOK_URL
    }
    
    max_retries = 24  
    
    for attempt in range(max_retries):
        try:
            async with session.post(
                APOLLO_BULK_MATCH_URL,
                headers=headers,
                params=params,
                json={"details": details}
            ) as response:
                response_json = await response.json()
                
                if response.status == 200:
                    # Create a mapping of Apollo IDs to enriched data
                    enriched_data = {}
                    for match in response_json.get('matches', []):

                        apollo_id = match.get('id')
                        if apollo_id:
                            enriched_data[apollo_id] = {
                                'email': match.get('email'),
                                'email_status': match.get('email_status')
                            }
                    return enriched_data
                elif response.status == 429:
                    should_retry = await handle_rate_limit_retry(response, attempt, max_retries)
                    if should_retry:
                        continue
                    else:
                        print("Failed to enrich contacts after max retries due to rate limiting.")
                        return {}
                else:
                    print(f"Failed to enrich contacts. Status: {response.status}")
                    print(response_json)
                    return {}
        except Exception as e:
            print(f"Error enriching contacts: {str(e)}")
            return {}
    
    return {}

async def process_company(session, company: Dict, job_titles: List[str]) -> None:
    """Process a single company"""
    if not company.get('website'):
        print(f"❌ {company['name']} - No website available")
        return
    
    domain = clean_domain(company['website'])
    print(f"\n{'='*50}")
    print(f"🏢 Company: {company['name']}")
    print(f"🌐 Website: {domain}")
    
    job_title_batches = split_into_batches(job_titles)
    all_contacts = []
    
    for job_title_batch in job_title_batches:
        result = await search_contacts(session, domain, job_title_batch)
        
        if result:
            contacts = result.get('people', [])
            all_contacts.extend(contacts)
        
        await asyncio.sleep(2)
    
    # Filter and categorize all contacts
    matching_contacts, excluded_contacts, other_contacts = filter_matching_contacts(all_contacts, domain, job_titles)
    
    # Process other_contacts with LLM and get additional matches and excludes
    additional_matching, additional_excluded = await process_other_contacts_with_llm(other_contacts)
    
    # Combine original matching contacts with additional ones found by LLM
    all_matching_contacts = matching_contacts + additional_matching
    # Combine original excluded contacts with additional ones from LLM
    all_excluded_contacts = excluded_contacts + additional_excluded

    print(f"✅ Matching contacts: {len(all_matching_contacts)}")
    print(f"❌ Excluded contacts: {len(all_excluded_contacts)}")
    
    # Enrich all matching contacts and get updated contacts with enriched data

    if all_matching_contacts:
        print(f"📝 Enriching {len(all_matching_contacts)} contacts...")
        enriched_matching_contacts = await enrich_all_contacts(session, all_matching_contacts)
    else:
        print("ℹ️ No contacts found to enrich")
        enriched_matching_contacts = []

    
    print(f"{'='*50}")

    
    # Save contacts to database instead of JSON
    if all_contacts:
        await save_contacts_to_database(enriched_matching_contacts, all_excluded_contacts)
    
    # Update company's scraping status
    supabase.table('eudamed_companies')\
        .update({"scraping_status": "FETCHED_APOLLO_CONTACTS"})\
        .eq('id', company['id'])\
        .execute()
    
    await asyncio.sleep(2)

async def enrich_all_contacts(session, matching_contacts: List[Dict]) -> List[Dict]:
    """
    Enrich all matching contacts with additional data from Apollo.
    
    Args:
        session: The aiohttp session
        matching_contacts (List[Dict]): List of all matching contacts to enrich
    
    Returns:
        List[Dict]: Updated list of contacts with enriched data
    """
    # print(f"\nEnriching {len(matching_contacts)} matching contacts...")

    # For all contacts change the apollo_id to id
    for contact in matching_contacts:
        contact['apollo_id'] = contact['id']
    
    # Split contacts into batches of 10
    contact_batches = batch_contacts(matching_contacts)
    
    # Create a copy of contacts to update
    enriched_contacts = matching_contacts.copy()
    
    for batch in contact_batches:
        enriched_data = await enrich_contacts_batch(session, batch)
        
        # Update contacts with enriched data
        for contact in enriched_contacts:
            apollo_id = contact.get('id')
            if apollo_id and apollo_id in enriched_data:
                contact.update(enriched_data[apollo_id])
                # Print newly enriched email
                if enriched_data[apollo_id].get('enriched_email'):
                    # print(f"Enriched email for {contact.get('name', 'Unknown')}: {enriched_data[apollo_id]['enriched_email']}")
                    pass
        
        # Add delay between batches to avoid rate limiting
        await asyncio.sleep(2)
    
    return enriched_contacts

async def process_all_companies(iso_code: str, limit: int = None) -> None:
    """Process all companies, with optional limit for testing"""
    # Load all job titles
    job_titles_data = load_job_titles()
    all_job_titles = []
    for category in job_titles_data.values():
        all_job_titles.extend(category)
    
    # Fetch companies
    companies = fetch_all_companies(supabase, iso_code)
    
    if not companies:
        print(f"❌ No companies found for {iso_code}")
        return
    
    # Filter out companies that have already been processed
    companies_to_process = [
        company for company in companies 
        if company.get('scraping_status') != 'FETCHED_APOLLO_CONTACTS'
    ]
    
    if not companies_to_process:
        print(f"✅ All companies for {iso_code} have already been processed")
        return
    
    # Limit companies for testing if specified
    if limit:
        companies_to_process = companies_to_process[:limit]
        print(f"\n🔍 Processing first {limit} companies")
    
    total_companies = len(companies_to_process)
    print(f"📊 Total companies to process: {total_companies}")
    print(f"⏭️  Skipping {len(companies) - total_companies} already processed companies\n")
    
    async with aiohttp.ClientSession() as session:
        for i, company in enumerate(companies_to_process, 1):
            print(f"\n👉 Processing company {i}/{total_companies}")
            await process_company(session, company, all_job_titles)

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        print("Usage: python get_apollo_contacts.py <iso_code>")
        sys.exit(1)
    
    iso_code = sys.argv[1].upper()
    # Process only first 5 companies for testing
    asyncio.run(process_all_companies(iso_code))
