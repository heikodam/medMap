import os
import requests
from googleapiclient.discovery import build
from bs4 import BeautifulSoup
import openai
from dotenv import load_dotenv


load_dotenv()


# Set up API keys (replace with your actual keys)
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")
GOOGLE_CSE_ID = os.environ.get("GOOGLE_CSE_ID")

openai.api_key = OPENAI_API_KEY

def google_search(query, num_results=5):
    service = build("customsearch", "v1", developerKey=GOOGLE_API_KEY)
    result = service.cse().list(q=query, cx=GOOGLE_CSE_ID, num=num_results).execute()
    return result.get('items', [])

def extract_text_from_url(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    return soup.get_text()

def get_employee_count(website):
    # Perform Google search
    query = f"How many people work at {website}"
    search_results = google_search(query)
    
    # Extract text from search results
    texts = []
    for item in search_results:
        url = item['link']
        text = extract_text_from_url(url)
        texts.append(text[:5000])  # Limit text length to avoid token limits
    
    # Combine texts
    combined_text = "\n\n".join(texts)
    
    # Use GPT to extract the employee count
    prompt = f"Based on the following text, how many employees work at {website} worldwide? Please respond with only a number. If you can't find a specific number, respond with 'Unknown'.\n\n{combined_text}"
    
    response = openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a helpful assistant that extracts employee counts from text."},
            {"role": "user", "content": prompt}
        ]
    )

    content = response.choices[0].message.content.strip()
    if content.isdigit():
        return int(content)
    else:
        return None

    # return response.choices[0].message['content'].strip()

# Example usage
# website = "zeiss.com"
# website = "resmed.com"
website = "dentsplysirona.com" # This one is tricky
# website = "medicon.de"
# website = "erbe-med.com" # This one is tricky
employee_count = get_employee_count(website)
print(f"Number of employees at {website}: {employee_count}")