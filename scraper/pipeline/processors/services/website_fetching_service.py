"""
Website Fetching Service

This service handles fetching company websites using the Perplexity AI API.
It provides a clean interface for website discovery and domain extraction.
"""

import os
import requests
import re
from typing import Optional
from dotenv import load_dotenv

from ui.progress_tracker import ProgressTracker
from config.settings import get_supabase_client

load_dotenv()


class WebsiteFetchingService:
    """Service for fetching company websites using Perplexity AI"""
    
    def __init__(self, progress: ProgressTracker):
        self.progress = progress
        self.supabase = get_supabase_client()
        self.perplexity_api_key = os.environ.get("PERPLEXITY_API_KEY")
    
    def should_fetch_website(self, company: dict) -> bool:
        """
        Determine if we should fetch a website for this company.
        Only fetch if:
        1. Company doesn't have an original_website already
        2. Perplexity API key is available
        """
        original_website = company.get('original_website')
        has_no_website = original_website is None or original_website == ''
        has_perplexity_key = self.perplexity_api_key is not None
        
        return has_no_website and has_perplexity_key
    
    def get_website_skip_reason(self, company: dict) -> str:
        """Get the reason why website fetching is being skipped"""
        original_website = company.get('original_website')
        if original_website is not None and original_website != '':
            return f"already has original_website: {original_website}"
        elif self.perplexity_api_key is None:
            return "no Perplexity API key"
        else:
            return "unknown reason"
    
    async def fetch_company_website(self, company_name: str) -> Optional[str]:
        """
        Use Perplexity's Sonar model to find the official website for a company.
        Returns the domain name or None if not found.
        """
        if not self.perplexity_api_key:
            self.progress.display_status_update(
                "No Perplexity API key available", 
                "yellow"
            )
            return None
            
        headers = {
            "Authorization": f"Bearer {self.perplexity_api_key}",
            "Content-Type": "application/json"
        }
        
        prompt = (
            f"What is the official website for the company '{company_name}'? "
            f"Please provide only the domain (with the format 'example.com' without www and without http/https) "
            f"or 'N/A' if you cannot find it. Do not provide any additional explanation."
        )
        
        data = {
            "model": "sonar",
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "max_tokens": 100
        }
        
        try:
            response = requests.post(
                "https://api.perplexity.ai/chat/completions", 
                headers=headers, 
                json=data,
                timeout=30
            )
            response.raise_for_status()
            result = response.json()
            
            content = result['choices'][0]['message']['content'].strip()
            
            # Clean up the response to extract just the domain
            domain = self._extract_domain_from_response(content)
            
            if domain:
                self.progress.display_status_update(
                    f"Found website for {company_name}: {domain}", 
                    "green"
                )
            else:
                self.progress.display_status_update(
                    f"Could not find website for {company_name}", 
                    "yellow"
                )
            
            return domain
            
        except Exception as e:
            self.progress.display_status_update(
                f"Error fetching website for {company_name}: {str(e)}", 
                "red"
            )
            return None
    
    def _extract_domain_from_response(self, content: str) -> Optional[str]:
        """Extract domain name from Perplexity API response"""
        content_lower = content.lower()
        
        # Check for negative responses
        negative_indicators = ['n/a', 'not found', 'cannot find', 'unable to find']
        if any(indicator in content_lower for indicator in negative_indicators):
            return None
                
        # Extract domain from the response (remove common prefixes/suffixes)
        lines = content.split('\n')
        for line in lines:
            line = line.strip()
            # Remove common text and extract domain-like strings
            if '.' in line and not line.startswith('http'):
                # Clean the line to extract just the domain
                domain_match = re.search(
                    r'([a-zA-Z0-9-]+\.(?:[a-zA-Z]{2,}|[a-zA-Z]{2,}\.[a-zA-Z]{2,}))', 
                    line
                )
                if domain_match:
                    return domain_match.group(1)
        
        return None
    
    async def update_company_website(self, company_id: str, website: str) -> dict:
        """Update company record with website directly in website field and mark as enriched"""
        update_data = {
            "website": website,
            "scraping_status": "FETCHED_WEBSITE_PERPLEXITY"
        }
        
        try:
            result = self.supabase.table("eudamed_company").update(
                update_data
            ).eq("id", company_id).execute()
            
            if result.data:
                self.progress.display_status_update(
                    f"Updated company {company_id} with website: {website}", 
                    "green"
                )
                return result.data[0]
            else:
                # Return original data with updates if DB update failed
                return {"id": company_id, **update_data}
        except Exception as e:
            self.progress.display_status_update(
                f"Error updating company {company_id}: {str(e)}", 
                "red"
            )
            return {"id": company_id, **update_data}
    
    async def mark_website_search_failed(self, company_id: str) -> None:
        """Mark company as unable to find website"""
        try:
            self.supabase.table("eudamed_company").update({
                "scraping_status": "ERROR_WEBSITE_SEARCH"
            }).eq("id", company_id).execute()
            
            self.progress.display_status_update(
                f"Marked company {company_id} as website search failed", 
                "yellow"
            )
        except Exception as e:
            self.progress.display_status_update(
                f"Error marking company {company_id} as failed: {str(e)}", 
                "red"
            ) 