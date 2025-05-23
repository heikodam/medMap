"""
Example Usage of the Modular EUDAMED Scraper

This script demonstrates how to use individual components of the modular scraper.
"""

import asyncio
from models.data_models import PipelineConfig, CompanyData
from ui.progress_tracker import ProgressTracker
from pipeline.company_processor import CompanyProcessor
from pipeline.device_processor import DeviceProcessor
from pipeline.certificate_processor import CertificateProcessor
from pipeline.orchestrator import PipelineOrchestrator

async def example_company_processing():
    """Example: Process companies for a specific country"""
    print("=== Example: Company Processing ===")
    
    progress = ProgressTracker()
    company_processor = CompanyProcessor(progress)
    
    # Fetch companies for a country (limit to 2 for demo)
    companies = company_processor.fetch_companies_for_country("UA")[:2]
    
    print(f"Found {len(companies)} companies")
    for company in companies:
        print(f"- {company.name} ({company.eudamed_uuid})")

async def example_device_processing():
    """Example: Process devices for a specific company"""
    print("\n=== Example: Device Processing ===")
    
    progress = ProgressTracker()
    device_processor = DeviceProcessor(progress)
    
    # Mock company data (in real usage, this would come from the database)
    mock_company = {
        'id': 'test-company-id',
        'name': 'Test Company',
        'eudamed_identifier': 'test-srn'  # This would be a real SRN
    }
    
    # This would normally fetch real devices
    print("Device processing requires a real company with SRN from the database")

async def example_certificate_processing():
    """Example: Process certificates"""
    print("\n=== Example: Certificate Processing ===")
    
    progress = ProgressTracker()
    certificate_processor = CertificateProcessor(progress)
    
    # Fetch certificates (limit to 2 for demo)
    certificates = certificate_processor.fetch_all_certificates()[:2]
    
    print(f"Found {len(certificates)} certificates")
    for cert in certificates:
        print(f"- {cert.certificate_number} ({cert.eudamed_uuid})")

async def example_full_pipeline():
    """Example: Run a complete pipeline with limits"""
    print("\n=== Example: Full Pipeline (Limited) ===")
    
    config = PipelineConfig(
        iso_code="UA",
        max_companies=1,          # Process only 1 company
        max_devices_per_company=2, # Process max 2 devices per company
        max_certificates=1         # Process only 1 certificate
    )
    
    orchestrator = PipelineOrchestrator()
    
    # This would run the full pipeline
    print("Full pipeline example - uncomment the line below to run:")
    print("# await orchestrator.run_complete_pipeline(config)")

async def main():
    """Run all examples"""
    await example_company_processing()
    await example_device_processing()
    await example_certificate_processing()
    await example_full_pipeline()
    
    print("\n=== Examples Complete ===")
    print("See README.md for more detailed usage instructions.")

if __name__ == "__main__":
    asyncio.run(main()) 