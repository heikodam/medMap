import aiohttp
from typing import List, Dict, Any, Optional

from models.data_models import CompanyData
from database.operations import DatabaseOperations
from ui.progress_tracker import ProgressTracker
from pipeline.contact_processor import ContactProcessor
from get_company_id import fetch_companies as fetch_companies_list
from get_company_details import fetch_company_details, update_company, insert_contact_person
from config.settings import DEFAULT_PAGE_SIZE

class CompanyProcessor:
    """Handles company-related processing operations"""
    
    def __init__(self, progress_tracker: ProgressTracker):
        self.db = DatabaseOperations()
        self.progress = progress_tracker
        self.contact_processor = ContactProcessor(progress_tracker)
    
    def fetch_companies_for_country(self, iso_code: str, page_size: int = DEFAULT_PAGE_SIZE) -> List[CompanyData]:
        """
        Fetch all companies for a specific country and return them as a list.
        This only fetches data, does not save to DB.
        """
        self.progress.start_timer()
        
        with self.progress.console.status(f"[bold green]Fetching companies for {iso_code}...", spinner="dots"):
            all_companies = []
            page = 0
            
            while True:
                data = fetch_companies_list(iso_code, page, page_size)
                
                if page == 0:
                    total_pages = data.get('totalPages', 1)
                    total_elements = data.get('totalElements', len(data['content']))
                    self.progress.display_status_update(
                        f"Found {total_elements} companies in {total_pages} pages for {iso_code}", 
                        "bold cyan"
                    )
                
                for company in data['content']:
                    company_data = CompanyData(
                        eudamed_uuid=company['uuid'],
                        name=company['name'],
                        iso_code=iso_code,
                        eudamed_identifier=company.get('srn')
                    )
                    all_companies.append(company_data)
                
                # Show progress for multi-page results
                if data.get('totalPages', 1) > 1:
                    self.progress.display_status_update(
                        f"Retrieved page {page+1}/{data.get('totalPages')} "
                        f"({len(all_companies)}/{data.get('totalElements')} companies)", 
                        "blue"
                    )
                
                if data['last']:
                    break
                
                page += 1
        
        # Update global stats
        self.progress.update_stats(total_companies=len(all_companies))
        
        # Show the summary panel
        self.progress.display_summary_panel(
            f"EUDAMED Pipeline - {iso_code}",
            "Step 1: Company Collection Complete",
            "green"
        )
        
        return all_companies
    
    async def process_company_details(self, company_data: CompanyData) -> Dict[str, Any]:
        """
        Get details for a specific company, save both the company and its details.
        """
        self.progress.display_company_panel(
            company_data.name, 
            company_data.eudamed_uuid, 
            company_data.iso_code
        )
        
        # First check if the company already exists
        with self.progress.console.status("[bold blue]Checking database for existing company record...", spinner="dots"):
            existing_company = self.db.check_company_exists(company_data.eudamed_uuid)
        
        if existing_company:
            self.progress.display_status_update(
                f"Company already exists with UUID: {company_data.eudamed_uuid}", 
                "yellow"
            )
            company_record = existing_company
        else:
            self.progress.display_status_update("Creating new company record in database", "blue")
            company_record = self.db.create_company_record(company_data)
        
        # Now fetch and save the details
        with self.progress.console.status(f"[bold blue]Fetching details for {company_data.name}...", spinner="dots"):
            async with aiohttp.ClientSession() as session:
                details = await fetch_company_details(session, company_record['eudamed_uuid'])
                
                if details is None:
                    self.progress.display_status_update(
                        f"Error fetching details for company {company_record['id']}", 
                        "bold red"
                    )
                    self.db.update_company_status(company_record['id'], "ERROR")
                    return company_record
                
                # Check for error response
                if 'httpStatusCode' in details:
                    self.progress.display_status_update(
                        f"Error fetching details for company {company_record['id']}: "
                        f"{details.get('httpStatus', 'Unknown error')}", 
                        "bold red"
                    )
                    self.db.update_company_status(company_record['id'], "ERROR")
                    return company_record
        
        with self.progress.console.status("[bold blue]Updating company with details...", spinner="dots"):
            # Update the company with details
            await update_company(company_record['id'], details)
            
            # Extract the SRN from company details if not already set
            if not company_record.get('eudamed_identifier') and 'actorDataPublicView' in details:
                actor_data = details['actorDataPublicView']
                srn = actor_data.get('srn')
                if srn:
                    self.db.update_company_srn(company_record['id'], srn)
                    company_record['eudamed_identifier'] = srn
                    self.progress.display_status_update(f"Found and updated SRN: {srn}", "green")
        
        # Process contact persons for this company
        with self.progress.console.status("[bold blue]Processing contact persons...", spinner="dots"):
            try:
                contact_count = await self.contact_processor.process_contacts_for_company(
                    company_record['id'], 
                    details
                )
                
                # Update contact statistics
                if contact_count > 0:
                    self.progress.increment_stats(
                        total_contacts=contact_count,
                        processed_contacts=contact_count,
                        companies_with_contacts=1
                    )
                    self.progress.display_status_update(
                        f"Processed {contact_count} contact person(s)", 
                        "green"
                    )
                else:
                    self.progress.increment_stats(companies_without_contacts=1)
                    
            except Exception as e:
                self.progress.increment_stats(companies_without_contacts=1)
                self.progress.display_status_update(
                    f"Error processing contacts: {str(e)}", 
                    "red"
                )
        
        # Return the updated company record
        updated_company = company_record.copy()
        updated_company.update({"scraping_status": "PIPELINE_GOT_COMPANY_DETAILS"})
        
        # Update stats
        self.progress.increment_stats(processed_companies=1)
        
        self.progress.display_status_update(
            f"Completed company details for: {company_data.name}", 
            "bold green"
        )
        
        return updated_company 