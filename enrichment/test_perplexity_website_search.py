#!/usr/bin/env python3
"""
Test script for Perplexity website search functionality.
Usage: python test_perplexity_website_search.py <company_name>
"""

import os
import sys
import requests
import re
from dotenv import load_dotenv

load_dotenv()

PERPLEXITY_API_KEY = os.environ.get("PERPLEXITY_API_KEY")

def perplexity_search_website(company_name):
    """
    Use Perplexity's Sonar model to find the official website for a company.
    Returns the domain name or None if not found.
    """
    if not PERPLEXITY_API_KEY:
        print("Error: PERPLEXITY_API_KEY not found in environment variables")
        return None
        
    headers = {
        "Authorization": f"Bearer {PERPLEXITY_API_KEY}",
        "Content-Type": "application/json"
    }
    
    prompt = f"What is the official website for the company '{company_name}'? Please provide only the domain (with the format 'example.com' without www and without http/https) or 'N/A' if you cannot find it. Do not provide any additional explanation."
    
    data = {
        "model": "sonar",
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "max_tokens": 100
    }
    
    try:
        print(f"Searching for official website of '{company_name}'...")
        response = requests.post("https://api.perplexity.ai/chat/completions", headers=headers, json=data)
        response.raise_for_status()
        result = response.json()
        
        content = result['choices'][0]['message']['content'].strip()
        print(f"Raw Perplexity response: {content}")
        
        # Clean up the response to extract just the domain
        content_lower = content.lower()
        if content_lower == 'n/a' or 'n/a' in content_lower or 'not found' in content_lower or 'cannot find' in content_lower:
            print("No website found.")
            return None
            
        # Extract domain from the response (remove common prefixes/suffixes)
        lines = content.split('\n')
        for line in lines:
            line = line.strip()
            # Remove common text and extract domain-like strings
            if '.' in line and not line.startswith('http'):
                # Clean the line to extract just the domain
                domain_match = re.search(r'([a-zA-Z0-9-]+\.(?:[a-zA-Z]{2,}|[a-zA-Z]{2,}\.[a-zA-Z]{2,}))', line)
                if domain_match:
                    domain = domain_match.group(1)
                    print(f"Extracted domain: {domain}")
                    return domain
        
        print("Could not extract a valid domain from the response.")
        return None
        
    except Exception as e:
        print(f"Error searching for {company_name}: {str(e)}")
        return None

def main():
    if len(sys.argv) != 2:
        print("Usage: python test_perplexity_website_search.py <company_name>")
        print("Example: python test_perplexity_website_search.py 'Apple Inc'")
        sys.exit(1)
    
    company_name = sys.argv[1]
    
    print(f"Testing Perplexity website search for: {company_name}")
    print("-" * 50)
    
    result = perplexity_search_website(company_name)
    
    print("-" * 50)
    if result:
        print(f"✅ Success! Found website: {result}")
    else:
        print("❌ No website found or error occurred.")

if __name__ == "__main__":
    main() 