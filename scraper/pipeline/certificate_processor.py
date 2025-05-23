import aiohttp
from typing import List, Dict, Any, Optional

from models.data_models import CertificateData
from database.operations import DatabaseOperations
from ui.progress_tracker import ProgressTracker
from get_certificates import fetch_certificates as fetch_certificates_list
from get_certificate_details import fetch_certificate_details, update_certificate, update_certificate_scopes, update_certificate_documents, update_notified_body
from config.settings import DEFAULT_PAGE_SIZE

class CertificateProcessor:
    """Handles certificate-related processing operations"""
    
    def __init__(self, progress_tracker: ProgressTracker):
        self.db = DatabaseOperations()
        self.progress = progress_tracker
    
    def fetch_all_certificates(self, page_size: int = DEFAULT_PAGE_SIZE) -> List[CertificateData]:
        """
        Get all certificates and return them as a list.
        This fetches certificates globally, not per country.
        """
        with self.progress.console.status("[bold green]Fetching all certificates...", spinner="dots"):
            all_certificates = []
            page = 0
            
            while True:
                data = fetch_certificates_list(page, page_size)
                
                if page == 0:
                    total_pages = data.get('totalPages', 1)
                    total_elements = data.get('totalElements', len(data['content']))
                    self.progress.display_status_update(
                        f"Found {total_elements} certificates in {total_pages} pages", 
                        "bold cyan"
                    )
                
                for certificate in data['content']:
                    certificate_data = CertificateData(
                        eudamed_uuid=certificate['uuid'],
                        certificate_number=certificate.get('certificateNumber', 'Unknown'),
                        json_dump=certificate
                    )
                    all_certificates.append(certificate_data)
                
                # Show progress for multi-page results
                if data.get('totalPages', 1) > 1:
                    self.progress.display_status_update(
                        f"Retrieved page {page+1}/{data.get('totalPages')} "
                        f"({len(all_certificates)}/{data.get('totalElements')} certificates)", 
                        "blue"
                    )
                
                if data['last']:
                    break
                
                page += 1
        
        # Update global stats
        self.progress.update_stats(total_certificates=len(all_certificates))
        
        # Show the summary panel
        self.progress.display_summary_panel(
            "EUDAMED Certificate Collection",
            "Certificate Collection Complete",
            "green"
        )
        
        return all_certificates
    
    async def process_certificate_details(self, certificate_data: CertificateData, 
                                        certificate_number: int = 0, 
                                        total_certificates: int = 0) -> Dict[str, Any]:
        """
        Get details for a specific certificate and save it to the database.
        This processes certificates independently from companies.
        """
        self.progress.display_status_update(
            f"Processing certificate {certificate_number+1}/{total_certificates}: "
            f"{certificate_data.certificate_number}", 
            "blue"
        )
        
        # First check if the certificate already exists
        with self.progress.console.status("[bold blue]Checking for existing certificate record...", spinner="dots"):
            existing_certificate = self.db.check_certificate_exists(certificate_data.eudamed_uuid)

        if existing_certificate:
            # Update existing certificate
            with self.progress.console.status("[bold blue]Updating existing certificate record...", spinner="dots"):
                certificate_record = self.db.update_certificate_record(certificate_data)
                self.progress.display_status_update(
                    f"Updated existing certificate: {certificate_data.certificate_number}", 
                    "yellow"
                )
        else:
            # Insert new certificate
            with self.progress.console.status("[bold blue]Creating new certificate record...", spinner="dots"):
                certificate_record = self.db.create_certificate_record(certificate_data)
                self.progress.display_status_update(
                    f"Created new certificate: {certificate_data.certificate_number}", 
                    "green"
                )
        
        # Now fetch and save the details
        with self.progress.console.status(
            f"[bold blue]Fetching details for certificate {certificate_data.certificate_number}...", 
            spinner="dots"
        ):
            async with aiohttp.ClientSession() as session:
                details = await fetch_certificate_details(session, certificate_record['eudamed_uuid'])
                
                if details is None:
                    self.progress.display_status_update(
                        f"Error fetching details for certificate {certificate_record['id']}", 
                        "bold red"
                    )
                    self.db.update_certificate_status(certificate_record['id'], "ERROR_GETTING_DETAILS")
                    return certificate_record
                
                # Check for error response
                if isinstance(details, dict) and 'httpStatusCode' in details:
                    self.progress.display_status_update(
                        f"Error fetching details for certificate {certificate_record['id']}: "
                        f"{details.get('httpStatus', 'Unknown error')}", 
                        "bold red"
                    )
                    self.db.update_certificate_status(certificate_record['id'], "ERROR_GETTING_DETAILS")
                    return certificate_record
        
        with self.progress.console.status("[bold blue]Updating certificate with details...", spinner="dots"):
            # Update certificate with details and related data
            await update_notified_body(details.get('notifiedBody', {}))
            await update_certificate(certificate_record['id'], details)
            await update_certificate_scopes(certificate_record['id'], details.get('scopes', []))
            await update_certificate_documents(certificate_record['id'], details.get('documents', []))
        
        # Update stats
        self.progress.increment_stats(processed_certificates=1)
        
        # Return the updated certificate record
        updated_certificate = certificate_record.copy()
        updated_certificate.update({"scraping_status": "PIPELINE_GOT_CERTIFICATE_DETAILS"})
        self.progress.display_status_update(
            f"Completed processing certificate: {certificate_record.get('certificate_number', 'Unknown')}", 
            "green"
        )
        return updated_certificate 