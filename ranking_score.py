import os
import asyncio
import aiohttp
from dotenv import load_dotenv
from supabase import create_client, Client

# Load environment variables
load_dotenv()

# Supabase setup
url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url, key)

# EUDAMED API URL
base_url = "https://ec.europa.eu/tools/eudamed/api/devices/basicUdiData/udiDiData"

async def fetch_companies(batch_size=1000, from_=0):
    return supabase.table('eudamed_companies') \
        .select("id", "name") \
        .eq("iso_code", "DE") \
        .eq("eudamed_type", "MF") \
        .neq("scraping_status", "UPDATED_RANKING_SCORE") \
        .range(from_, from_ + batch_size - 1) \
        .execute()


async def update_company(id, update_data):
        
    # Remove None values from the update dictionary
    details = {k: v for k, v in update_data.items() if v is not None}
    
    supabase.table('eudamed_companies').update(details).eq('id', id).execute()


async def fetch_comp_products(uuid):
    return supabase.table('eudamed_products') \
        .select("id", "risk_class") \
        .eq("company_id", uuid) \
        .eq("active", True) \
        .eq("manufacturer_latest_version", True) \
        .execute()

async def fetch_apollo_company(company):
    return supabase.table('apollo_companies') \
        .select("id", "eudamed_company_id", "estimated_num_employees", "annual_revenue") \
        .eq("eudamed_company_id", company['id']) \
        .execute()

async def ranking_score_products(company):
    products = await fetch_comp_products(company['id'])

    product_risk_classes = {
        "i": 0,
        "iia": 0,
        "iib": 0,
        "iii": 0,
    }

    for product in products.data:
         match product['risk_class']:
            case "refdata.risk-class.class-a":
                product_risk_classes["i"] += 1
            case "refdata.risk-class.class-iia":
                product_risk_classes["iia"] += 1
            case "refdata.risk-class.class-iib":
                product_risk_classes["iib"] += 1
            case "refdata.risk-class.class-iii":
                product_risk_classes["iii"] += 1
            case _:
                pass

    ranking_score = 0
    ranking_score += min(product_risk_classes["i"] * 1, 10)
    ranking_score += min(product_risk_classes["iia"] * 5, 20)
    ranking_score += min(product_risk_classes["iib"] * 7, 20)
    ranking_score += min(product_risk_classes["iii"] * 10, 30)

    return ranking_score

async def ranking_score_rev_empl(company):
    apollo_companies = await fetch_apollo_company(company)
    apollo_company = apollo_companies.data[0] if apollo_companies.data else {}

    ranking_score = 0

    # Revenue * 0,00000002
    annual_revenue_score = (apollo_company.get('annual_revenue') or 0) * 0.00000002

    # Employees * 0.02
    empl_score = (apollo_company.get('estimated_num_employees') or 0) * 0.02

    ranking_score += min(annual_revenue_score, 20)
    ranking_score += min(empl_score, 20)

    return ranking_score


async def process_company(session, company):

    ranking_score = 0
    ranking_score += await ranking_score_products(company)
    ranking_score += await ranking_score_rev_empl(company)

    # round to 2 decimal places
    ranking_score = round(ranking_score, 2)

    update_data = {
        "ranking_score": ranking_score,
        "scraping_status": "UPDATED_RANKING_SCORE"
    }

    await update_company(company['id'], update_data)

    print(f"Risk score for {company['id']} {company['name']} to {ranking_score}")

async def process_companies_batch(companies):
    async with aiohttp.ClientSession() as session:
        tasks = [process_company(session, company) for company in companies]
        await asyncio.gather(*tasks)

async def process_all_companies():
    batch_size = 100
    from_ = 0
    total_processed = 0

    while True:
        companies = await fetch_companies(batch_size, from_)
        
        if not companies.data:
            print("No companies found.")
            break
        
        await process_companies_batch(companies.data)
        
        total_processed += len(companies.data)
        from_ += batch_size
        
        print(f"Processed {total_processed} companies so far.")
        
        if len(companies.data) < batch_size:
            break
        
    print(f"Finished processing all companies. Total processed: {total_processed}")

# Run the script
asyncio.run(process_all_companies())


