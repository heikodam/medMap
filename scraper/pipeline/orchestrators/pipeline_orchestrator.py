from typing import List, Dict, Any, Optional
from prefect import flow

from models.data_models import PipelineConfig
from ui.progress_tracker import ProgressTracker
from pipeline.processors.company_processor import CompanyProcessor
from pipeline.processors.device_processor import DeviceProcessor
from pipeline.processors.certificate_processor import CertificateProcessor

class PipelineOrchestrator:
    """Main orchestrator for the EUDAMED scraping pipeline"""
    
    def __init__(self):
        self.progress = ProgressTracker()
        self.company_processor = CompanyProcessor(self.progress)
        self.device_processor = DeviceProcessor(self.progress)
        self.certificate_processor = CertificateProcessor(self.progress)
    
    async def process_single_company_complete(self, company_data, max_devices_per_company: Optional[int] = None, 
                                            company_index: int = 0, total_companies: int = 0) -> Dict[str, Any]:
        """
        Process a single company through the entire pipeline:
        1. Get and save company details
        2. Get devices for the company
        3. Get and save device details for each device
        """
        self.progress.display_progress_header(company_data.name, company_index, total_companies)
        
        # Step 1: Process company details
        updated_company = await self.company_processor.process_company_details(company_data)
        
        # Step 2: Get devices for this company
        devices = await self.device_processor.fetch_company_devices(updated_company)
        
        # Limit number of devices if specified
        if max_devices_per_company is not None and devices:
            original_count = len(devices)
            devices = devices[:max_devices_per_company]
            if original_count > max_devices_per_company:
                self.progress.display_status_update(
                    f"Limited to processing {max_devices_per_company}/{original_count} devices for company: {company_data.name}", 
                    "yellow"
                )
        
        # Step 3: Process each device
        processed_devices = []
        if devices:
            device_count = len(devices)
            self.progress.display_status_update(
                f"Processing {device_count} devices for {company_data.name}", 
                "bold blue"
            )
            
            for i, device in enumerate(devices):
                updated_device = await self.device_processor.process_device_details(device, i, device_count)
                processed_devices.append(updated_device)
                # Display simple progress update
                if i < device_count - 1:  # Don't show "finished" until we're really done
                    percent = int((i + 1) / device_count * 100)
                    self.progress.display_status_update(
                        f"Device progress: {i+1}/{device_count} ({percent}%)", 
                        "blue"
                    )
        
        # Show company completion summary
        self.progress.display_completion_summary(company_data.name, len(processed_devices))
        
        # Show updated summary table
        self.progress.display_summary_panel("Pipeline Progress", "", "blue")
        
        return {"company": updated_company, "devices": processed_devices}
    
    @flow(name="EUDAMED Company Pipeline")
    async def run_company_pipeline(self, config: PipelineConfig) -> List[Dict[str, Any]]:
        """
        Main pipeline flow that processes companies one by one, completely.
        For each company, we:
        1. Get company details
        2. Get company devices
        3. Get device details
        Then move to the next company.
        """
        # Display title
        self.progress.display_pipeline_title(
            config.iso_code, 
            config.max_companies, 
            config.max_devices_per_company, 
            "Company"
        )
        
        # Step 1: Get all companies for country (without saving to DB)
        companies = self.company_processor.fetch_companies_for_country(config.iso_code, config.page_size)
        
        # Limit number of companies if specified
        if config.max_companies is not None:
            original_count = len(companies)
            companies = companies[:config.max_companies]
            if original_count > config.max_companies:
                self.progress.display_status_update(
                    f"Limited to processing {config.max_companies}/{original_count} companies", 
                    "yellow"
                )
        
        total_companies = len(companies)
        
        # Step 2: Process each company completely (one at a time)
        results = []
        
        for index, company in enumerate(companies):
            # Show a simple text progress indicator
            percent = int((index) / total_companies * 100) if total_companies > 0 else 0
            self.progress.display_status_update(
                f"Overall progress: {index}/{total_companies} companies ({percent}%)", 
                "cyan"
            )
            
            # Process the company
            result = await self.process_single_company_complete(
                company, 
                config.max_devices_per_company,
                company_index=index,
                total_companies=total_companies
            )
            results.append(result)
        
        # Count total devices processed
        total_devices = sum(len(result["devices"]) for result in results)
        
        # Display final summary
        self.progress.display_final_summary(
            config.iso_code, 
            len(results), 
            total_devices, 
            pipeline_type="Company"
        )
        
        return results
    
    @flow(name="EUDAMED Certificate Pipeline")
    async def run_certificate_pipeline(self, config: PipelineConfig) -> List[Dict[str, Any]]:
        """
        Pipeline flow that processes all certificates.
        This runs independently from companies and processes certificates globally.
        """
        # Display title
        self.progress.display_pipeline_title(
            "Global", 
            config.max_certificates, 
            pipeline_type="Certificate"
        )
        
        # Step 1: Get all certificates (without saving to DB)
        certificates = self.certificate_processor.fetch_all_certificates(config.page_size)
        
        # Limit number of certificates if specified
        if config.max_certificates is not None:
            original_count = len(certificates)
            certificates = certificates[:config.max_certificates]
            if original_count > config.max_certificates:
                self.progress.display_status_update(
                    f"Limited to processing {config.max_certificates}/{original_count} certificates", 
                    "yellow"
                )
        
        total_certificates = len(certificates)
        
        # Step 2: Process each certificate
        processed_certificates = []
        
        for index, certificate in enumerate(certificates):
            # Show a simple text progress indicator
            percent = int((index) / total_certificates * 100) if total_certificates > 0 else 0
            self.progress.display_status_update(
                f"Certificate progress: {index}/{total_certificates} certificates ({percent}%)", 
                "cyan"
            )
            
            # Process the certificate
            result = await self.certificate_processor.process_certificate_details(
                certificate, 
                certificate_number=index,
                total_certificates=total_certificates
            )
            processed_certificates.append(result)
        
        # Display final summary
        self.progress.display_final_summary(
            "Global", 
            0,  # No companies in certificate pipeline
            0,  # No devices in certificate pipeline
            len(processed_certificates),
            "Certificate"
        )
        
        return processed_certificates
    
    @flow(name="EUDAMED Complete Pipeline")
    async def run_complete_pipeline(self, config: PipelineConfig) -> Dict[str, Any]:
        """
        Complete pipeline that processes both companies (with devices) and certificates.
        Always processes companies first, then certificates.
        """
        # Display title
        self.progress.display_pipeline_title(
            config.iso_code, 
            config.max_companies, 
            config.max_devices_per_company, 
            "Complete"
        )
        
        # Step 1: Process companies and devices
        company_results = await self.run_company_pipeline(config)
        
        # Step 2: Always process certificates after companies
        self.progress.display_status_update("Starting certificate processing...", "bold magenta")
        
        # Create certificate config
        cert_config = PipelineConfig(
            iso_code="Global",
            max_certificates=config.max_certificates,
            page_size=config.page_size
        )
        certificate_results = await self.run_certificate_pipeline(cert_config)
        
        # Final complete summary
        total_devices = sum(len(result["devices"]) for result in company_results)
        
        self.progress.display_final_summary(
            config.iso_code,
            len(company_results),
            total_devices,
            len(certificate_results),
            "Complete"
        )
        
        return {
            "companies": company_results,
            "certificates": certificate_results
        } 