# Apollo Contact Enrichment with Phone Numbers

This guide explains how to fetch and enrich contacts from Apollo, including getting their phone numbers via webhooks.

## Prerequisites

1. Python 3.8+
2. Apollo API Key
3. Supabase credentials
4. ngrok installed (`brew install ngrok` on macOS)

## Setup Process

### 1. Install Dependencies

```bash
pip install fastapi uvicorn python-dotenv supabase aiohttp
```

### 2. Environment Variables

Create or update your `.env` file with:
```
APOLLO_API_KEY=your_apollo_api_key
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key
```

### 3. Start the Webhook Server

The webhook server receives phone number data from Apollo. Run it in a terminal:

```bash
python enrichment/contacts/webhook_server.py
```

This starts a FastAPI server on port 8000.

### 4. Start ngrok

Open a new terminal and start ngrok to expose your local webhook server:

```bash
ngrok http 8000
```

You'll see output like:
```
Forwarding https://xxxx-xxxx-xxxx-xxxx.ngrok-free.app -> http://localhost:8000
```

### 5. Update Webhook URL

Add the ngrok URL to your `.env` file:
```bash
echo "WEBHOOK_URL=https://xxxx-xxxx-xxxx-xxxx.ngrok-free.app/webhook" >> .env
```

Replace the URL with your actual ngrok URL and append `/webhook` at the end.

### 6. Run the Contact Enrichment

In a third terminal, run:

```bash
python -m enrichment.contacts.get_apollo_contacts <ISO_CODE>
```

Replace `<ISO_CODE>` with your target country code (e.g., 'DE', 'US').

## How It Works

1. `get_apollo_contacts.py`:
   - Fetches contacts from Apollo based on job titles
   - Filters relevant contacts
   - Sends enrichment requests to Apollo for emails and phone numbers
   - Saves contact data to JSON files in `temp_data/`

2. `webhook_server.py`:
   - Receives webhook calls from Apollo with phone number data
   - Temporarily stores phone numbers in JSON files
   - (When uncommented) Saves phone numbers to Supabase database

## Important Notes

1. Keep both the webhook server and ngrok running while fetching contacts
2. The ngrok URL changes each time you restart ngrok (free tier)
3. Phone numbers are currently saved to JSON files in `temp_data/`
4. Uncomment the Supabase code in `webhook_server.py` to store numbers in the database

## Troubleshooting

1. If no phone numbers are received:
   - Check if webhook server is running
   - Verify ngrok is running and URL is correct in .env
   - Check Apollo credits and rate limits

2. If webhook server fails to start:
   - Check if port 8000 is available
   - Verify all dependencies are installed

## File Structure

```
enrichment/
└── contacts/
    ├── get_apollo_contacts.py    # Main script for fetching contacts
    ├── webhook_server.py         # Webhook server for phone numbers
    └── temp_data/               # Temporary storage for JSON files
``` 