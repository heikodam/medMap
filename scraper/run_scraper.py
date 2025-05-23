"""
EUDAMED Scraper Pipeline - Main Entry Point

This is the simplified main file that orchestrates the entire EUDAMED scraping pipeline.
It uses a modular architecture with clean separation of concerns.

Usage:
    python run_scraper.py <iso_code> [limit] [--enrichment]

Examples:
    python run_scraper.py UA                    # Process all companies, devices, and certificates for Ukraine
    python run_scraper.py UA 5                  # Process max 5 companies, 5 devices per company, 5 certificates
    python run_scraper.py UA --enrichment       # Process all companies with enrichment steps (website fetching)
    python run_scraper.py UA 5 --enrichment     # Process max 5 companies with enrichment steps
"""

import os
import sys
import asyncio
import argparse
from models.data_models import PipelineConfig
from pipeline import PipelineOrchestrator

async def run_pipeline(iso_code: str, limit: int = None, enable_enrichment: bool = False) -> None:
    """
    Main entry point for running the complete EUDAMED pipeline
    
    Args:
        iso_code: Country ISO code (e.g., 'UA' for Ukraine)
        limit: Optional limit for processing (applies to companies, devices per company, and certificates)
        enable_enrichment: Whether to run enrichment steps like website fetching
    """
    # Create pipeline configuration
    config = PipelineConfig(
        iso_code=iso_code,
        max_companies=limit,
        max_devices_per_company=limit,
        max_certificates=limit,
        enable_enrichment=enable_enrichment
    )
    
    # Initialize and run the orchestrator
    orchestrator = PipelineOrchestrator()
    await orchestrator.run_complete_pipeline(config)

def main():
    """CLI entry point with argument parsing and validation"""
    parser = argparse.ArgumentParser(
        description='EUDAMED Scraper Pipeline',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_scraper.py UA                    # Process all companies, devices, and certificates for Ukraine
  python run_scraper.py UA 5                  # Process max 5 companies, 5 devices per company, 5 certificates
  python run_scraper.py UA --enrichment       # Process all companies with enrichment steps (website fetching)
  python run_scraper.py UA 5 --enrichment     # Process max 5 companies with enrichment steps
        """
    )
    
    parser.add_argument('iso_code', help='Country ISO code (e.g., UA, DE, FR)')
    parser.add_argument('limit', nargs='?', type=int, default=None, 
                       help='Optional limit for processing (applies to companies, devices per company, and certificates)')
    parser.add_argument('--enrichment', action='store_true', 
                       help='Enable enrichment steps like website fetching using Perplexity API')
    
    args = parser.parse_args()
    
    iso_code = args.iso_code.upper()  # Ensure uppercase for consistency
    limit = args.limit
    enable_enrichment = args.enrichment
    
    # Validate ISO code format (basic validation)
    if len(iso_code) != 2 or not iso_code.isalpha():
        print(f"Error: Invalid ISO code '{iso_code}'. Must be a 2-letter country code (e.g., 'UA', 'DE', 'FR')")
        sys.exit(1)
    
    # Clear terminal for a fresh start
    os.system('cls' if os.name == 'nt' else 'clear')
    
    # Show enrichment status
    if enable_enrichment:
        print("🔍 Enrichment enabled: Will fetch company websites using Perplexity API")
        print("-" * 60)
    
    # Run the pipeline
    asyncio.run(run_pipeline(iso_code, limit, enable_enrichment))

if __name__ == "__main__":
    main() 