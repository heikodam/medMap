import aiohttp
from typing import List, Dict, Any, Optional

from models.data_models import DeviceData
from database.operations import DatabaseOperations
from ui.progress_tracker import ProgressTracker
from legacy.get_company_devices import fetch_devices
from legacy.get_company_devices_details import fetch_device_details, update_product

class DeviceProcessor:
    """Handles device-related processing operations"""
    
    def __init__(self, progress_tracker: ProgressTracker):
        self.db = DatabaseOperations()
        self.progress = progress_tracker
    
    async def fetch_company_devices(self, company: Dict[str, Any]) -> List[DeviceData]:
        """
        Get all devices for a specific company.
        Only fetch, don't save devices.
        """
        self.progress.display_status_update(
            f"Fetching devices for company: {company['name']}", 
            "bold blue"
        )
        
        devices = []
        
        # Check if we have an SRN to query with (in eudamed_identifier column)
        srn = company.get('eudamed_identifier')
        if not srn:
            self.progress.display_status_update(
                f"No SRN found for company {company['name']} - cannot fetch devices", 
                "bold red"
            )
            self.db.update_company_status(company['id'], "MISSING_SRN_FOR_DEVICES")
            
            # Update stats
            self.progress.increment_stats(companies_without_devices=1)
            return []
        
        # Debug: Print the SRN we're using
        self.progress.display_status_update(f"Using SRN for device query: {srn}", "blue")
        
        self.progress.display_status_update(f"Starting device fetching for {company['name']}...", "blue")
        
        async with aiohttp.ClientSession() as session:
            try:
                page = 0
                total_pages = 1
                total_elements = 0
                
                while True:
                    try:
                        with self.progress.console.status(f"[bold blue]Fetching devices page {page+1}...", spinner="dots"):
                            data = await fetch_devices(session, srn, page)
                        
                        # If this is the first page, update the total
                        if page == 0 and isinstance(data, dict):
                            total_pages = data.get('totalPages', 1)
                            total_elements = data.get('totalElements', 0)
                            if total_elements > 0:
                                self.progress.display_status_update(
                                    f"Found {total_elements} devices in {total_pages} pages", 
                                    "cyan"
                                )
                        
                        if not data or not isinstance(data, dict) or not data.get('content'):
                            self.progress.display_status_update(
                                f"No devices data returned for page {page}", 
                                "yellow"
                            )
                            break
                        
                        # Update progress
                        self.progress.display_status_update(
                            f"Processing page {page+1}/{total_pages} with {len(data['content'])} devices", 
                            "blue"
                        )
                        
                        for device in data['content']:
                            device_data = DeviceData(
                                eudamed_uuid=device['uuid'],
                                name=device.get('tradeName', 'Unknown device'),
                                company_id=company['id']
                            )
                            devices.append(device_data)
                        
                        if data.get('last', True):
                            break
                        
                        page += 1
                    except Exception as e:
                        self.progress.display_status_update(
                            f"Error fetching devices on page {page}: {str(e)}", 
                            "bold red"
                        )
                        # Try to continue with next page if possible
                        page += 1
                        if page > 5:  # Safety limit
                            break
                
                # Update company scraping status, but don't save any devices yet
                with self.progress.console.status("[bold blue]Updating company status...", spinner="dots"):
                    self.db.update_company_status(company['id'], "PIPELINE_COLLECTED_DEVICES")
                
                # Update stats
                if devices:
                    self.progress.increment_stats(
                        companies_with_devices=1,
                        total_devices=len(devices)
                    )
                else:
                    self.progress.increment_stats(companies_without_devices=1)
                
            except Exception as e:
                self.progress.display_status_update(
                    f"Error fetching devices for company {company['id']}: {str(e)}", 
                    "bold red"
                )
                self.db.update_company_status(company['id'], "ERROR_GETTING_DEVICES")
                return []
        
        # Show a nice device summary
        self.progress.display_devices_summary(company['name'], len(devices))
        
        return devices
    
    async def process_device_details(self, device_data: DeviceData, device_number: int = 0, 
                                   total_devices: int = 0) -> Dict[str, Any]:
        """
        Get details for a specific device and save it to the database.
        """
        self.progress.display_status_update(
            f"Processing device {device_number+1}/{total_devices}: {device_data.name}", 
            "blue"
        )
        
        # First check if the device already exists
        with self.progress.console.status("[bold blue]Checking for existing device record...", spinner="dots"):
            existing_device = self.db.check_device_exists(device_data.eudamed_uuid)

        if existing_device:
            # Update existing device
            with self.progress.console.status("[bold blue]Updating existing device record...", spinner="dots"):
                device_record = self.db.update_device_record(device_data)
                self.progress.display_status_update(f"Updated existing device: {device_data.name}", "yellow")
        else:
            # Insert new device
            with self.progress.console.status("[bold blue]Creating new device record...", spinner="dots"):
                device_record = self.db.create_device_record(device_data)
                self.progress.display_status_update(f"Created new device: {device_data.name}", "green")
        
        # Now fetch and save the details
        with self.progress.console.status(f"[bold blue]Fetching details for device {device_data.name}...", spinner="dots"):
            async with aiohttp.ClientSession() as session:
                details = await fetch_device_details(session, device_record['eudamed_uuid'])
                
                if details is None:
                    self.progress.display_status_update(
                        f"Error fetching details for device {device_record['id']}", 
                        "bold red"
                    )
                    self.db.update_device_status(device_record['id'], "ERROR_GETTING_DETAILS")
                    return device_record
                
                # Check for error response
                if isinstance(details, dict) and 'httpStatusCode' in details:
                    self.progress.display_status_update(
                        f"Error fetching details for device {device_record['id']}: "
                        f"{details.get('httpStatus', 'Unknown error')}", 
                        "bold red"
                    )
                    self.db.update_device_status(device_record['id'], "ERROR_GETTING_DETAILS")
                    return device_record
        
        with self.progress.console.status("[bold blue]Updating device with details...", spinner="dots"):
            # Update device with details
            await update_product(device_record['id'], details)
        
        # Update stats
        self.progress.increment_stats(processed_devices=1)
        
        # Return the updated device record
        updated_device = device_record.copy()
        updated_device.update({"scraping_status": "PIPELINE_GOT_DEVICE_DETAILS"})
        self.progress.display_status_update(
            f"Completed processing device: {device_record['name']}", 
            "green"
        )
        return updated_device 