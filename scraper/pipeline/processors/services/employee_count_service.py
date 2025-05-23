"""
Employee Count Service

This service handles fetching employee count information for companies.
It uses Perplexity's Sonar model to find the number of employees for a company
based on their website information.
"""

import os
import requests
import re
from typing import Optional, Dict, Any
from dotenv import load_dotenv

from ui.progress_tracker import ProgressTracker
from config.settings import get_supabase_client

load_dotenv()

class EmployeeCountService:
    """Service for fetching company employee count information"""
    
    def __init__(self, progress: ProgressTracker):
        self.progress = progress
        self.supabase = get_supabase_client()
        
        # Perplexity setup
        self.perplexity_api_key = os.environ.get("PERPLEXITY_API_KEY")
        self.perplexity_available = self.perplexity_api_key is not None
    
    def _should_fetch_employee_count(self, company: Dict[str, Any]) -> bool:
        """
        Determine if we should fetch employee count for this company.
        Only fetch if:
        1. Company has a website field
        2. Company doesn't already have employee count data (not marked as having employee count)
        3. Perplexity API key is available
        """
        website = company.get('website')
        has_website = website is not None and website != ''
        
        scraping_status = company.get('scraping_status', '')
        already_has_employee_count = scraping_status in [
            'GOT_EMPL_WEBSITE_PERPLEXITY', 
            'GOT_EMPL_WEBSITE_PERPLEXITY_NO_SITE',
            'ERROR_EMPLOYEE_COUNT_FETCH'
        ]
        
        return has_website and not already_has_employee_count and self.perplexity_available
    
    async def _fetch_employee_count(self, company_name: str, website: Optional[str] = None) -> Optional[int]:
        """
        Use Perplexity's Sonar model to find the number of employees for a company.
        Returns the employee count as integer or None if not found.
        """
        if not self.perplexity_available:
            return None
            
        headers = {
            "Authorization": f"Bearer {self.perplexity_api_key}",
            "Content-Type": "application/json"
        }
        
        # Include website in the prompt if available
        if website:
            prompt = f"How many employees work at {company_name} (website: {website}) worldwide? Please provide only the number of employees. If you cannot find a specific number, respond with 'Unknown'."
        else:
            prompt = f"How many employees work at {company_name} worldwide? Please provide only the number of employees. If you cannot find a specific number, respond with 'Unknown'."
        
        data = {
            "model": "sonar",
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "max_tokens": 150
        }
        
        try:
            response = requests.post("https://api.perplexity.ai/chat/completions", headers=headers, json=data)
            response.raise_for_status()
            result = response.json()
            
            content = result['choices'][0]['message']['content'].strip()
            
            # Extract number from response
            content_lower = content.lower()
            if 'unknown' in content_lower or 'not found' in content_lower or 'cannot find' in content_lower:
                return None
            
            # Look for numbers in the response
            # Handle various formats like "1,000", "1000", "approximately 1000", etc.
            number_patterns = [
                r'(\d{1,3}(?:,\d{3})+)',  # Numbers with commas like 1,000
                r'(\d+,?\d*)',            # General numbers
            ]
            
            for pattern in number_patterns:
                matches = re.findall(pattern, content)
                if matches:
                    # Take the first number found
                    number_str = matches[0].replace(',', '')
                    if number_str.isdigit():
                        return int(number_str)
            
            return None
            
        except Exception as e:
            self.progress.display_status_update(
                f"Error fetching employee count for {company_name}: {str(e)}", 
                "red"
            )
            return None
    
    async def _update_company_employee_count(self, company_id: str, employee_count: Optional[int], has_website: bool) -> Dict[str, Any]:
        """Update company record with employee count and mark as processed"""
        if has_website:
            update_data = {
                "empl_website": employee_count,
                "scraping_status": "GOT_EMPL_WEBSITE_PERPLEXITY"
            }
        else:
            update_data = {
                "empl_website": employee_count,
                "scraping_status": "GOT_EMPL_WEBSITE_PERPLEXITY_NO_SITE"
            }
        
        result = self.supabase.table("eudamed_company").update(
            update_data
        ).eq("id", company_id).execute()
        
        if result.data:
            return result.data[0]
        else:
            # Return original data with updates if DB update failed
            return {"id": company_id, **update_data}
    
    async def _mark_employee_count_error(self, company_id: str) -> Dict[str, Any]:
        """Mark company as having error during employee count fetch"""
        update_data = {
            "scraping_status": "ERROR_EMPLOYEE_COUNT_FETCH"
        }
        
        result = self.supabase.table("eudamed_company").update(
            update_data
        ).eq("id", company_id).execute()
        
        if result.data:
            return result.data[0]
        else:
            return {"id": company_id, **update_data}
    
    async def process_company_employee_count(self, company: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process employee count fetching for a single company.
        
        Args:
            company: Company data dictionary
            
        Returns:
            Updated company data with employee count
        """
        company_name = company.get('name', 'Unknown')
        website = company.get('website')
        
        # Check if company needs employee count fetching
        if self._should_fetch_employee_count(company):
            self.progress.display_status_update(
                f"Fetching employee count for {company_name}", 
                "cyan"
            )
            
            employee_count = await self._fetch_employee_count(company_name, website)
            
            # Update company with employee count (even if None)
            updated_company = await self._update_company_employee_count(
                company['id'], 
                employee_count, 
                has_website=True
            )
            
            if employee_count is not None:
                self.progress.display_status_update(
                    f"✅ Found employee count for {company_name}: {employee_count}", 
                    "green"
                )
            else:
                self.progress.display_status_update(
                    f"⚠️  Could not find employee count for {company_name}", 
                    "yellow"
                )
            
            return updated_company
        
        elif not website:
            # No website available, can't fetch employee count
            self.progress.display_status_update(
                f"No website available for {company_name}, skipping employee count", 
                "blue"
            )
            return company
        
        else:
            # Skip employee count fetching (already processed or no Perplexity key)
            scraping_status = company.get('scraping_status', '')
            if scraping_status in ['GOT_EMPL_WEBSITE_PERPLEXITY', 'GOT_EMPL_WEBSITE_PERPLEXITY_NO_SITE']:
                reason = "already processed"
            elif not self.perplexity_available:
                reason = "no Perplexity API key"
            else:
                reason = "unknown"
                
            self.progress.display_status_update(
                f"Skipping employee count for {company_name} ({reason})", 
                "yellow"
            )
            return company 