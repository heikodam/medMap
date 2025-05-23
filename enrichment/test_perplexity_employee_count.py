#!/usr/bin/env python3
"""
Test script for Perplexity employee count search functionality.
Usage: python test_perplexity_employee_count.py <company_name> [website]
"""

import os
import sys
import requests
import re
from dotenv import load_dotenv

load_dotenv()

PERPLEXITY_API_KEY = os.environ.get("PERPLEXITY_API_KEY")

def perplexity_get_employee_count(company_name, website=None):
    """
    Use Perplexity's Sonar model to find the number of employees for a company.
    Returns the employee count as integer or None if not found.
    """
    if not PERPLEXITY_API_KEY:
        print("Error: PERPLEXITY_API_KEY not found in environment variables")
        return None
        
    headers = {
        "Authorization": f"Bearer {PERPLEXITY_API_KEY}",
        "Content-Type": "application/json"
    }
    
    # Include website in the prompt if available
    if website:
        prompt = f"How many employees work at {company_name} (website: {website}) worldwide? You are only allowed to look at the website ({website}) and not any other website. Please provide only the number of employees. If you cannot find a specific number, respond with 'Unknown'."
        print(f"Searching for employee count of '{company_name}' with website '{website}'...")
    else:
        prompt = f"How many employees work at {company_name} worldwide? You are only allowed to look at the website ({website}) and not any other website. Please provide only the number of employees. If you cannot find a specific number, respond with 'Unknown'."
        print(f"Searching for employee count of '{company_name}' (no website provided)...")
    
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
        print(f"Raw Perplexity response: {content}")
        
        # Extract number from response
        content_lower = content.lower()
        if 'unknown' in content_lower or 'not found' in content_lower or 'cannot find' in content_lower:
            print("No specific employee count found.")
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
                    extracted_count = int(number_str)
                    print(f"Extracted employee count: {extracted_count:,}")
                    return extracted_count
        
        print("Could not extract a valid employee count from the response.")
        return None
        
    except Exception as e:
        print(f"Error getting employee count for {company_name}: {str(e)}")
        return None

def main():
    if len(sys.argv) < 2 or len(sys.argv) > 3:
        print("Usage: python test_perplexity_employee_count.py <company_name> [website]")
        print("Examples:")
        print("  python test_perplexity_employee_count.py 'Apple Inc'")
        print("  python test_perplexity_employee_count.py 'Apple Inc' 'apple.com'")
        print("  python test_perplexity_employee_count.py 'Microsoft Corporation' 'microsoft.com'")
        sys.exit(1)
    
    company_name = sys.argv[1]
    website = sys.argv[2] if len(sys.argv) == 3 else None
    
    print(f"Testing Perplexity employee count search for: {company_name}")
    if website:
        print(f"Website provided: {website}")
    else:
        print("No website provided - searching by company name only")
    print("-" * 60)
    
    result = perplexity_get_employee_count(company_name, website)
    
    print("-" * 60)
    if result:
        print(f"✅ Success! Found employee count: {result:,} employees")
    else:
        print("❌ No employee count found or error occurred.")

if __name__ == "__main__":
    main() 