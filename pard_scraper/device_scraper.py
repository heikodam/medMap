import os
import json
import requests
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
import time
import hashlib

from utils import get_supabase_client, retry_supabase_operation

def get_company_id_by_man_organisation_id(man_organisation_id: int) -> Optional[str]:
    """
    Get the Supabase UUID for a company by its MAN_ORGANISATION_ID
    
    Args:
        man_organisation_id: The manufacturer organisation ID
        
    Returns:
        The UUID of the company in the Supabase table, or None if not found
    """
    if not man_organisation_id or man_organisation_id == "None":
        return None
    
    supabase = get_supabase_client()
    
    def fetch_company():
        return supabase.table("pard_company").select("id").eq("man_organisation_id", man_organisation_id).execute()
    
    result = retry_supabase_operation(fetch_company)
    
    if result.data and len(result.data) > 0:
        return result.data[0]["id"]
    
    return None

def format_device_data(device_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Format the device data for insertion into Supabase
    
    Args:
        device_data: Raw device data from the API
        
    Returns:
        Formatted device data ready for database insertion
    """
    # Get the company ID for the foreign key relationship
    pard_company_id = get_company_id_by_man_organisation_id(device_data.get("MAN_ORGANISATION_ID"))
    
    # Helper function to handle None values
    def clean_value(value):
        # Return None for both Python None values and string "None" values
        if value is None or value == "None":
            return None
        return value
    
    # Convert to snake_case and standardize data types
    formatted_data = {
        "pard_company_id": pard_company_id,
        "man_organisation_id": clean_value(device_data.get("MAN_ORGANISATION_ID")),
        "device_id": clean_value(device_data.get("DEVICE_ID")),
        "gmdn_code": clean_value(device_data.get("GMDN_CODE")),
        "gmdn_term_name": clean_value(device_data.get("GMDN_TERM_NAME", "")) or "",
        "device_sub_type_desc": clean_value(device_data.get("DEVICE_SUB_TYPE_DESC", "")) or "",
        "is_custom_made": clean_value(device_data.get("IS_CUSTOM_MADE", "")) or "",
        "is_performance_studies": clean_value(device_data.get("IS_PERFORMANCE_STUDIES", "")) or "",
        "device_reg_status_code": clean_value(device_data.get("DEVICE_REG_STATUS_CODE", "")) or "",
        "device_type_name": clean_value(device_data.get("DEVICE_TYPE_NAME", "")) or "",
        "last_updated_date": clean_value(device_data.get("LAST_UPDATED_DATE")),
        "certificate_id": clean_value(device_data.get("CERTIFICATE_ID")),
        "is_incorpporate_custommade_medical_device": clean_value(device_data.get("IS_INCORPPORATE_CUSTOMMADE_MEDICAL_DEVICE", "")) or ""
    }
    
    return formatted_data

def fetch_devices(page: int = 1, page_size: int = 100, man_organisation_id: Optional[int] = None) -> List[Dict[str, Any]]:
    """
    Fetch devices from the PARD API
    
    Args:
        page: Page number to fetch (not used in this API)
        page_size: Number of items per page (not used in this API)
        man_organisation_id: Optional manufacturer organisation ID to filter by
        
    Returns:
        List of device data dictionaries
    """
    api_url = "https://pard.mhra.gov.uk/searchDevicesAdvanced"
    
    # The search payload with empty fields to get all devices
    payload = {
        "searchTerm": {
            "manufacturerName": "",
            "referenceNumber": "",
            "deviceName": "",
            "deviceType": "",
            "gmdnCode": ""
        }
    }
    
    # If a specific manufacturer ID is provided, add it to the search
    if man_organisation_id:
        payload["searchTerm"]["manufacturerName"] = str(man_organisation_id)
    
    headers = {
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(api_url, headers=headers, json=payload)
        response.raise_for_status()
        
        # The API returns a list of devices directly
        return response.json()
    except requests.RequestException as e:
        print(f"Error fetching devices: {e}")
        return []

def generate_device_fingerprint(device_data: Dict[str, Any]) -> str:
    """
    Generate a unique fingerprint for a device using a combination of fields
    for cases where device_id is not available
    
    Args:
        device_data: The formatted device data
        
    Returns:
        A hash string that can be used as a unique identifier
    """
    # Create a string combining multiple fields that together can identify the device
    parts = [
        str(device_data.get("man_organisation_id") or ""),
        str(device_data.get("gmdn_code") or ""),
        str(device_data.get("gmdn_term_name") or ""),
        str(device_data.get("device_sub_type_desc") or ""),
        str(device_data.get("device_type_name") or "")
    ]
    
    # Join and hash to create a consistent fingerprint
    fingerprint_string = "|".join([p for p in parts if p])
    return hashlib.md5(fingerprint_string.encode()).hexdigest()

def save_devices_to_supabase(devices: List[Dict[str, Any]]) -> Tuple[int, int]:
    """
    Save devices to Supabase
    
    Args:
        devices: List of device data dictionaries
        
    Returns:
        Tuple of (saved_count, skipped_count)
    """
    if not devices:
        return (0, 0)
    
    supabase = get_supabase_client()
    saved_count = 0
    skipped_count = 0
    
    def deep_clean_none_values(data):
        """
        Recursively clean "None" string values in a dictionary
        
        Args:
            data: Dictionary or value to clean
            
        Returns:
            Cleaned data with all "None" strings converted to None
        """
        if isinstance(data, dict):
            return {k: deep_clean_none_values(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [deep_clean_none_values(item) for item in data]
        elif data == "None" or data == "none" or data == "NONE":
            print(f"Converting string '{data}' to None")
            return None
        elif isinstance(data, str) and data.strip() == "":
            # Empty strings for numeric fields could cause issues
            return None
        else:
            return data
    
    for device in devices:
        try:
            formatted_device = format_device_data(device)
            
            # Apply deep cleaning to entire formatted device
            formatted_device = deep_clean_none_values(formatted_device)
            
            # Debug output for integer fields
            if formatted_device["device_id"] == "None" or formatted_device["man_organisation_id"] == "None":
                print(f"WARNING: 'None' string found in data after cleaning:")
                print(f"  device_id = {formatted_device['device_id']} (type: {type(formatted_device['device_id']).__name__})")
                print(f"  man_organisation_id = {formatted_device['man_organisation_id']} (type: {type(formatted_device['man_organisation_id']).__name__})")
            
            # Skip devices without a company reference
            if not formatted_device["pard_company_id"]:
                skipped_count += 1
                continue
                
            # For devices with no device_id, generate a fingerprint and store it
            has_device_id = formatted_device["device_id"] is not None
            
            if not has_device_id:
                # Generate a fingerprint and add it to the device data
                fingerprint = generate_device_fingerprint(formatted_device)
                formatted_device["device_fingerprint"] = fingerprint
                print(f"Device without ID found. Generated fingerprint: {fingerprint}")
            
            # Check if device already exists - use either device_id or fingerprint
            if has_device_id:
                def check_device_exists():
                    return supabase.table("pard_device").select("id").eq("device_id", formatted_device["device_id"]).execute()
            else:
                def check_device_exists():
                    return supabase.table("pard_device").select("id").eq("device_fingerprint", formatted_device["device_fingerprint"]).execute()
            
            existing = retry_supabase_operation(check_device_exists)
            
            if existing.data:
                # Update existing device
                if has_device_id:
                    def update_device():
                        return supabase.table("pard_device").update(formatted_device).eq("device_id", formatted_device["device_id"]).execute()
                else:
                    def update_device():
                        return supabase.table("pard_device").update(formatted_device).eq("device_fingerprint", formatted_device["device_fingerprint"]).execute()
                
                retry_supabase_operation(update_device)
            else:
                # Insert new device
                def insert_device():
                    return supabase.table("pard_device").insert(formatted_device).execute()
                
                retry_supabase_operation(insert_device)
            
            saved_count += 1
            
            # Add a small delay between operations to avoid overwhelming the API
            time.sleep(0.1)
            
            # Print progress every 100 devices
            if saved_count % 100 == 0:
                print(f"Progress: {saved_count} devices saved, {skipped_count} skipped")
                
        except Exception as e:
            print(f"Error saving device {device.get('DEVICE_ID', 'Unknown')}: {e}")
            print(f"Problematic data: {json.dumps(formatted_device, default=str, indent=2)}")
            print(f"Raw device data: {json.dumps(device, default=str, indent=2)}")
            # Continue with next device instead of failing the entire batch
            skipped_count += 1
            continue
    
    return (saved_count, skipped_count)

def scrape_devices_for_company(man_organisation_id: int, max_pages: Optional[int] = None) -> Tuple[int, int]:
    """
    Scrape all devices for a specific company from the PARD API and save to Supabase
    
    Args:
        man_organisation_id: The manufacturer organisation ID to scrape devices for
        max_pages: Maximum number of pages to scrape (not used since the API returns all data at once)
        
    Returns:
        Tuple of (total_saved, total_skipped)
    """
    print(f"Fetching devices for company {man_organisation_id}...")
    devices = fetch_devices(man_organisation_id=man_organisation_id)
    
    if not devices:
        print(f"No devices found for company {man_organisation_id}")
        return (0, 0)
    
    print(f"Found {len(devices)} devices for company {man_organisation_id}")
    saved, skipped = save_devices_to_supabase(devices)
    print(f"Saved {saved} devices (skipped {skipped}) for company {man_organisation_id}")
    
    return (saved, skipped)

def scrape_all_devices(max_pages: Optional[int] = None, batch_size: int = 100, batch_delay: int = 2) -> Tuple[int, int]:
    """
    Scrape all devices from the PARD API and save to Supabase
    
    Args:
        max_pages: Maximum number of pages to scrape (not used since the API returns all data at once)
        batch_size: Number of devices to process in each batch
        batch_delay: Delay in seconds between batches
        
    Returns:
        Tuple of (total_saved, total_skipped)
    """
    print(f"Fetching all devices...")
    devices = fetch_devices()
    
    if not devices:
        print("No devices found")
        return (0, 0)
    
    print(f"Found {len(devices)} devices")
    
    # Process in batches
    total_saved = 0
    total_skipped = 0
    
    for i in range(0, len(devices), batch_size):
        batch = devices[i:i+batch_size]
        print(f"Processing batch {i//batch_size + 1}/{(len(devices) + batch_size - 1)//batch_size} ({len(batch)} devices)")
        
        saved, skipped = save_devices_to_supabase(batch)
        total_saved += saved
        total_skipped += skipped
        
        print(f"Batch complete: {saved} saved, {skipped} skipped. Total progress: {total_saved}/{len(devices)} ({total_saved/len(devices)*100:.1f}%)")
        
        # Add delay between batches to avoid overwhelming the API
        if i + batch_size < len(devices):
            print(f"Pausing for {batch_delay} seconds before next batch...")
            time.sleep(batch_delay)
    
    print(f"Completed: Saved {total_saved} devices (skipped {total_skipped})")
    
    return (total_saved, total_skipped)

if __name__ == "__main__":
    # For testing the scraper directly
    scrape_all_devices() 