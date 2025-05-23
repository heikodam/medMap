"""
Enrichment Processor

This processor coordinates enrichment steps that add additional data to companies,
devices, and other entities after the main scraping is complete.
"""

from typing import Dict, Any

from ui.progress_tracker import ProgressTracker
from .services.url_cleaning_service import UrlCleaningService
from .services.employee_count_service import EmployeeCountService
from .services.website_fetching_service import WebsiteFetchingService


class EnrichmentProcessor:
    """Processor for coordinating enrichment steps like website fetching and URL cleaning"""
    
    def __init__(self, progress: ProgressTracker):
        self.progress = progress
        
        # Initialize services
        self.website_fetching_service = WebsiteFetchingService(progress)
        self.url_cleaning_service = UrlCleaningService(progress)
        self.employee_count_service = EmployeeCountService(progress)
    
    async def process_company_enrichment(self, company: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process enrichment for a single company.
        This includes:
        1. Website fetching (if needed) - stores directly in website field
        2. URL cleaning (for companies with original_website from EUDAMED) - cleans into website field
        3. Employee count fetching (using cleaned website) - stores in empl_website field
        """
        enriched_company = company.copy()
        
        # Step 1: Website fetching (if needed)
        if self.website_fetching_service.should_fetch_website(company):
            self.progress.display_status_update(
                f"Fetching website for {company['name']}", 
                "cyan"
            )
            
            website = await self.website_fetching_service.fetch_company_website(company['name'])
            if website:
                # Update company with website directly in website field
                enriched_company = await self.website_fetching_service.update_company_website(
                    company['id'], website
                )
                self.progress.display_status_update(
                    f"✅ Found website for {company['name']}: {website}", 
                    "green"
                )
            else:
                # Mark as unable to find website
                await self.website_fetching_service.mark_website_search_failed(company['id'])
                self.progress.display_status_update(
                    f"❌ Could not find website for {company['name']}", 
                    "yellow"
                )
        else:
            skip_reason = self.website_fetching_service.get_website_skip_reason(company)
            self.progress.display_status_update(
                f"Skipping website enrichment for {company['name']} ({skip_reason})", 
                "yellow"
            )
        
        # Step 2: URL cleaning (for all companies, regardless of previous step)
        # This step processes companies that have an original_website field
        enriched_company = await self.url_cleaning_service.process_company_url_cleaning(enriched_company)
        
        # Step 3: Employee count fetching (after URL cleaning to use cleaned website)
        # This step processes companies that have a website field
        enriched_company = await self.employee_count_service.process_company_employee_count(enriched_company)
        
        return enriched_company
 