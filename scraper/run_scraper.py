"""
EUDAMED Scraper Pipeline - Main Entry Point

This is the simplified main file that orchestrates the entire EUDAMED scraping pipeline.
It uses a modular architecture with clean separation of concerns.

Usage:
    python run_scraper_pipeline_new.py <iso_code> [limit]

Examples:
    python run_scraper_pipeline_new.py UA        # Process all companies, devices, and certificates for Ukraine
    python run_scraper_pipeline_new.py UA 5      # Process max 5 companies, 5 devices per company, 5 certificates
"""

import os
import sys
import asyncio
from models.data_models import PipelineConfig
from pipeline import PipelineOrchestrator

async def run_pipeline(iso_code: str, limit: int = None) -> None:
    """
    Main entry point for running the complete EUDAMED pipeline
    
    Args:
        iso_code: Country ISO code (e.g., 'UA' for Ukraine)
        limit: Optional limit for processing (applies to companies, devices per company, and certificates)
    """
    # Create pipeline configuration
    config = PipelineConfig(
        iso_code=iso_code,
        max_companies=limit,
        max_devices_per_company=limit,
        max_certificates=limit
    )
    
    # Initialize and run the orchestrator
    orchestrator = PipelineOrchestrator()
    await orchestrator.run_complete_pipeline(config)

def main():
    """CLI entry point with argument parsing and validation"""
    if len(sys.argv) < 2:
        print("Usage: python run_scraper_pipeline_new.py <iso_code> [limit]")
        print("Examples:")
        print("  python run_scraper_pipeline_new.py UA        # Process all companies, devices, and certificates for Ukraine")
        print("  python run_scraper_pipeline_new.py UA 5      # Process max 5 companies, 5 devices per company, 5 certificates")
        sys.exit(1)
    
    iso_code = sys.argv[1].upper()  # Ensure uppercase for consistency
    limit = int(sys.argv[2]) if len(sys.argv) > 2 else None
    
    # Validate ISO code format (basic validation)
    if len(iso_code) != 2 or not iso_code.isalpha():
        print(f"Error: Invalid ISO code '{iso_code}'. Must be a 2-letter country code (e.g., 'UA', 'DE', 'FR')")
        sys.exit(1)
    
    # Clear terminal for a fresh start
    os.system('cls' if os.name == 'nt' else 'clear')
    
    # Run the pipeline
    asyncio.run(run_pipeline(iso_code, limit))

if __name__ == "__main__":
    main() 