#!/usr/bin/env python3
"""
Test script to verify our scraper changes
"""
import os
import sys
import time
from utils import get_supabase_client, retry_supabase_operation

def test_supabase_connection():
    """Test connection to Supabase"""
    print("Testing Supabase connection...")
    supabase = get_supabase_client()
    
    def test_query():
        return supabase.table("pard_companies").select("id").limit(1).execute()
    
    try:
        result = retry_supabase_operation(test_query)
        print(f"Connection successful! Result: {result.data}")
        return True
    except Exception as e:
        print(f"Connection failed: {e}")
        return False

def main():
    """Main test function"""
    # Check if environment variables are set
    if not os.environ.get("SUPABASE_URL") or not os.environ.get("SUPABASE_KEY"):
        print("ERROR: SUPABASE_URL and SUPABASE_KEY environment variables must be set")
        sys.exit(1)
    
    # Test connection
    if test_supabase_connection():
        print("Test passed!")
    else:
        print("Test failed!")

if __name__ == "__main__":
    main() 