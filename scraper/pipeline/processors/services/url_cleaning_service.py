"""
URL Cleaning Service

This service handles cleaning and normalizing website URLs for companies.
It uses OpenAI's GPT model to clean up website URLs to a standard format.
"""

import os
import openai
from typing import Optional, Dict, Any
from dotenv import load_dotenv

from ui.progress_tracker import ProgressTracker
from config.settings import get_supabase_client

load_dotenv()

class UrlCleaningService:
    """Service for cleaning and normalizing company website URLs"""
    
    def __init__(self, progress: ProgressTracker):
        self.progress = progress
        self.supabase = get_supabase_client()
        
        # OpenAI setup
        openai.api_key = os.environ.get("OPENAI_API_KEY")
        self.openai_available = openai.api_key is not None
    
    def _should_clean_url(self, company: Dict[str, Any]) -> bool:
        """
        Determine if we should clean a URL for this company.
        Only clean if:
        1. Company has an original_website field
        2. Company doesn't already have a cleaned website (not marked as CLEANED_WEBSITE)
        3. OpenAI API key is available
        """
        original_website = company.get('original_website')
        has_original_website = original_website is not None and original_website != ''
        
        scraping_status = company.get('scraping_status', '')
        already_cleaned = scraping_status == 'CLEANED_WEBSITE'
        
        return has_original_website and not already_cleaned and self.openai_available
    
    async def _clean_website_url(self, website: str) -> Optional[str]:
        """
        Use OpenAI GPT to clean up a website URL to a standard format.
        Returns the cleaned domain or None if cleaning fails.
        """
        if not self.openai_available:
            return None
            
        try:
            response = openai.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": """
                        You are a helpful assistant that cleans up website URLs but does not change the url itself. 
                        You will be provided with domain a value such as "http://www.domain.com or domain.at" and 
                        should only return 1 url that looks like this domain.com. 
                        Do not change the name or spelling of the domain itself - just clean it up. 
                        If in the value there are more than 1 domain, pick the more international one and always only 
                        return one. 

                        Examples:
                        Input: https://contact-endoscopy.com/
                        Output: contact-endoscopy.com

                        Input: ww.tqdnipro.com
                        Output: tqdnipro.com
                        
                    """},
                    {"role": "user", "content": website}
                ]
            )
            
            cleaned_url = response.choices[0].message.content.strip()
            return cleaned_url
            
        except Exception as e:
            self.progress.display_status_update(
                f"Error cleaning URL '{website}': {str(e)}", 
                "red"
            )
            return None
    
    async def _update_company_cleaned_url(self, company_id: str, cleaned_website: str, original_website: str) -> Dict[str, Any]:
        """Update company record with cleaned website and mark as cleaned"""
        update_data = {
            "website": cleaned_website,
            "original_website": original_website,
            "scraping_status": "CLEANED_WEBSITE"
        }
        
        result = self.supabase.table("eudamed_company").update(
            update_data
        ).eq("id", company_id).execute()
        
        if result.data:
            return result.data[0]
        else:
            # Return original data with updates if DB update failed
            return {"id": company_id, **update_data}
    
    async def _mark_no_website_to_clean(self, company_id: str) -> Dict[str, Any]:
        """Mark company as having no website to clean (original_website is None)"""
        update_data = {
            "scraping_status": "CLEANED_WEBSITE"
        }
        
        result = self.supabase.table("eudamed_company").update(
            update_data
        ).eq("id", company_id).execute()
        
        if result.data:
            return result.data[0]
        else:
            return {"id": company_id, **update_data}
    
    async def process_company_url_cleaning(self, company: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process URL cleaning for a single company.
        
        Args:
            company: Company data dictionary
            
        Returns:
            Updated company data with cleaned URL
        """
        company_name = company.get('name', 'Unknown')
        original_website = company.get('original_website')
        
        # Check if company needs URL cleaning
        if self._should_clean_url(company):
            self.progress.display_status_update(
                f"Cleaning URL for {company_name}", 
                "cyan"
            )
            
            cleaned_website = await self._clean_website_url(original_website)
            if cleaned_website:
                # Update company with cleaned website
                updated_company = await self._update_company_cleaned_url(
                    company['id'], 
                    cleaned_website, 
                    original_website
                )
                self.progress.display_status_update(
                    f"✅ Cleaned URL for {company_name}: {original_website} → {cleaned_website}", 
                    "green"
                )
                return updated_company
            else:
                # Mark as unable to clean URL but still update status
                updated_company = await self._update_company_cleaned_url(
                    company['id'], 
                    original_website,  # Keep original if cleaning failed
                    original_website
                )
                self.progress.display_status_update(
                    f"⚠️  Could not clean URL for {company_name}, keeping original: {original_website}", 
                    "yellow"
                )
                return updated_company
        
        elif original_website is None or original_website == '':
            # No website to clean, mark as cleaned
            self.progress.display_status_update(
                f"No website to clean for {company_name}", 
                "blue"
            )
            updated_company = await self._mark_no_website_to_clean(company['id'])
            return updated_company
        
        else:
            # Skip URL cleaning (already cleaned or no OpenAI key)
            reason = "already cleaned" if company.get('scraping_status') == 'CLEANED_WEBSITE' else "no OpenAI API key"
            self.progress.display_status_update(
                f"Skipping URL cleaning for {company_name} ({reason})", 
                "yellow"
            )
            return company 