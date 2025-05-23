"""
Example Usage of the Modular EUDAMED Scraper

This script demonstrates how to use individual components of the modular scraper.
"""

import asyncio
import sys
from models.data_models import PipelineConfig, CompanyData
from ui.progress_tracker import ProgressTracker
from pipeline.processors.company_processor import CompanyProcessor
from pipeline.processors.device_processor import DeviceProcessor
from pipeline.processors.certificate_processor import CertificateProcessor
from pipeline.orchestrators.pipeline_orchestrator import PipelineOrchestrator
from database.operations import DatabaseOperations
from models.data_models import ContactData

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

async def example_contact_change_tracking():
    """
    Example demonstrating the new contact change tracking functionality.
    
    Scenario: Company has existing contacts, EUDAMED returns updated/new contacts,
    system detects what changed, what's new, and what's no longer present.
    """
    db_ops = DatabaseOperations()
    
    # Generate a scrape run ID for this session
    scrape_run_id = db_ops.generate_scrape_run_id()
    print(f"Starting scrape session: {scrape_run_id}")
    
    # Example company ID (replace with actual UUID from your database)
    company_id = "612f0198-2aa3-4c7f-b330-abc33ddaae38"  # Example from your data
    
    # SCENARIO: EUDAMED returns these contacts for the company
    eudamed_contacts = [
        ContactData(
            company_id=company_id,
            first_name="Robert",
            family_name="Fuschelberger", 
            email="robert.new@kiweno.com",  # Email changed!
            phone="+436643783195",
            position="CTO"  # Position added!
        ),
        ContactData(
            company_id=company_id,
            first_name="Sarah",
            family_name="Johnson",  # New person!
            email="sarah.johnson@kiweno.com", 
            phone="+436643783200",
            position="Quality Manager"
        )
    ]
    
    print(f"\n📡 Processing {len(eudamed_contacts)} contacts from EUDAMED...")
    
    # Process contacts with change tracking
    stats = db_ops.process_company_contacts_with_change_tracking(
        company_id=company_id,
        new_contacts=eudamed_contacts,
        scrape_run_id=scrape_run_id
    )
    
    print(f"\n📊 Contact Processing Results:")
    print(f"   ✅ Created: {stats['created']}")
    print(f"   🔄 Updated: {stats['updated']}")
    print(f"   ❌ Deactivated: {stats['deactivated']}")
    print(f"   ⚪ Unchanged: {stats['unchanged']}")
    
    # Show recent changes for this company
    print(f"\n📋 Recent change history for this company:")
    changes = db_ops.get_contact_change_history(company_id=company_id, days_back=1)
    
    for change in changes[:10]:  # Show last 10 changes
        print(f"   {change['change_type']}: {change['change_summary']}")
        if change.get('changed_fields'):
            print(f"      Changed fields: {change['changed_fields']}")
        print(f"      At: {change['change_detected_at']}")
        print()

async def example_contact_identification():
    """
    Example showing how the contact identification strategy works
    """
    db_ops = DatabaseOperations()
    
    print("🔍 Contact Identification Strategy Examples:")
    print("=" * 50)
    
    # Example 1: Full identification (first_name + family_name + email)
    contact1 = ContactData(
        company_id="test-company-123",
        first_name="John",
        family_name="Doe", 
        email="john.doe@company.com"
    )
    key1 = db_ops.get_contact_identity_key(contact1)
    print(f"Full ID: {key1}")
    
    # Example 2: Same person, different email (would match on name if email missing)
    contact2 = ContactData(
        company_id="test-company-123",
        first_name="John",
        family_name="Doe", 
        email="j.doe@company.com"  # Different email
    )
    key2 = db_ops.get_contact_identity_key(contact2)
    print(f"Diff email: {key2}")
    
    # Example 3: Generic company email (multiple people might have same email)
    contact3 = ContactData(
        company_id="test-company-123",
        first_name="Jane",
        family_name="Smith", 
        email="info@company.com"  # Generic email
    )
    key3 = db_ops.get_contact_identity_key(contact3)
    print(f"Generic email: {key3}")
    
    print(f"\n✅ Each person gets unique identification even with generic emails!")

async def example_change_detection():
    """
    Example showing change detection between existing and new contact data
    """
    db_ops = DatabaseOperations()
    
    print("🔄 Change Detection Examples:")
    print("=" * 40)
    
    # Simulate existing contact from database
    existing_contact = {
        'id': 123,
        'first_name': 'John',
        'family_name': 'Doe',
        'position': 'Quality Manager',
        'email': 'john.doe@company.com',
        'phone': '+1234567890',
        'city_id': 1,
        'iso_code': 'US'
    }
    
    # Simulate new data from EUDAMED
    new_contact_data = ContactData(
        company_id="test-company",
        first_name="John",
        family_name="Doe",
        position="Senior Quality Manager",  # Position changed!
        email="j.doe@company.com",  # Email changed!
        phone="+1234567890",  # Same
        city_id=1,  # Same
        iso_code="US"  # Same
    )
    
    # Detect changes
    changed_fields, has_changes = db_ops.detect_contact_changes(existing_contact, new_contact_data)
    
    print(f"Has changes: {has_changes}")
    print(f"Changed fields: {changed_fields}")
    
    # Generate change summary
    summary = db_ops.generate_change_summary('UPDATED', existing_contact, new_contact_data, changed_fields)
    print(f"Change summary: {summary}")

def main():
    """Main function to run examples"""
    print("🚀 EUDAMED Contact Change Tracking Examples")
    print("=" * 60)
    
    if len(sys.argv) > 1:
        example_type = sys.argv[1]
        
        if example_type == "tracking":
            asyncio.run(example_contact_change_tracking())
        elif example_type == "identification":
            asyncio.run(example_contact_identification())
        elif example_type == "detection":
            asyncio.run(example_change_detection())
        else:
            print("Usage: python example_usage.py [tracking|identification|detection]")
    else:
        print("Available examples:")
        print("  python example_usage.py tracking      - Full contact change tracking demo")
        print("  python example_usage.py identification - Contact identification strategy")
        print("  python example_usage.py detection     - Change detection demo")

if __name__ == "__main__":
    main() 