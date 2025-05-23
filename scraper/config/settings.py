import os
from dotenv import load_dotenv
from supabase import create_client, Client

# Load environment variables
load_dotenv()

# Supabase configuration
SUPABASE_URL: str = os.environ.get("SUPABASE_URL")
SUPABASE_KEY: str = os.environ.get("SUPABASE_KEY")

def get_supabase_client() -> Client:
    """Get configured Supabase client"""
    return create_client(SUPABASE_URL, SUPABASE_KEY)

# EUDAMED API configuration
EUDAMED_BASE_URLS = {
    "actors": "https://ec.europa.eu/tools/eudamed/api/actors",
    "eos": "https://ec.europa.eu/tools/eudamed/api/eos",
    "devices": "https://ec.europa.eu/tools/eudamed/api/devices/udiDiData",
    "device_details": "https://ec.europa.eu/tools/eudamed/api/devices/basicUdiData/udiDiData",
    "certificates": "https://ec.europa.eu/tools/eudamed/api/certificates",
    "certificates_search": "https://ec.europa.eu/tools/eudamed/api/certificates/search/"
}

# Default pagination settings
DEFAULT_PAGE_SIZE = 300
MAX_RETRY_ATTEMPTS = 3
RETRY_DELAY_SECONDS = 5

# Processing limits
DEFAULT_CONCURRENT_REQUESTS = 5 