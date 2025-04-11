import os
from supabase import create_client, Client

async def fetch_comp_products(supabase: Client, uuid: str):
    return supabase.table('eudamed_products') \
        .select("id", "risk_class", "medicinal_product", "human_tissues", "animal_tissues", "human_product", "administering_medicine") \
        .eq("company_id", uuid) \
        .or_("legislation.eq.refdata.applicable-legislation.mdr,legislation.eq.refdata.applicable-legislation.mdd") \
        .execute()

async def fetch_apollo_company(supabase: Client, company):
    return supabase.table('apollo_companies') \
        .select("id", "eudamed_company_id", "estimated_num_employees", "annual_revenue") \
        .eq("eudamed_company_id", company['id']) \
        .execute()

async def update_company(supabase: Client, id, update_data):
    # Remove None values from the update dictionary
    details = {k: v for k, v in update_data.items() if v is not None}
    supabase.table('eudamed_companies').update(details).eq('id', id).execute()

async def ranking_score_products(supabase: Client, company):
    products = await fetch_comp_products(supabase, company['id'])

    product_totals_score = {
        "i": 0,
        "iia": 0,
        "iib": 0,
        "iii": 0,
        "medicinal_product": 0,
        "human_tissues": 0,
        "animal_tissues": 0,
        "human_product": 0,
        "administering_medicine": 0,
    }

    for product in products.data:
        # risk class
        match product['risk_class']:
            case "refdata.risk-class.class-i":
                product_totals_score["i"] += 1
            case "refdata.risk-class.class-iia":
                product_totals_score["iia"] += 1
            case "refdata.risk-class.class-iib":
                product_totals_score["iib"] += 1
            case "refdata.risk-class.class-iii":
                product_totals_score["iii"] += 1
            case _:
                pass
        
        # Other product attributes
        if product['medicinal_product']:
            product_totals_score["medicinal_product"] += 1
        if product['human_tissues']:
            product_totals_score["human_tissues"] += 1
        if product['animal_tissues']:
            product_totals_score["animal_tissues"] += 1
        if product['human_product']:
            product_totals_score["human_product"] += 1
        if product['administering_medicine']:
            product_totals_score["administering_medicine"] += 1

    # Calculate ranking score
    ranking_score = 0
    ranking_score += min(product_totals_score["i"] * 1, 10)
    ranking_score += min(product_totals_score["iia"] * 5, 20)
    ranking_score += min(product_totals_score["iib"] * 7, 20)
    ranking_score += min(product_totals_score["iii"] * 10, 30)
    ranking_score += min(product_totals_score["medicinal_product"] * 1, 5)
    ranking_score += min(product_totals_score["human_tissues"] * 5, 20)
    ranking_score += min(product_totals_score["animal_tissues"] * 5, 20)
    ranking_score += min(product_totals_score["human_product"] * 5, 20)
    ranking_score += min(product_totals_score["administering_medicine"] * 1, 5)

    return ranking_score

async def ranking_score_rev_empl(supabase: Client, company):
    apollo_companies = await fetch_apollo_company(supabase, company)
    apollo_company = apollo_companies.data[0] if apollo_companies.data else {}

    ranking_score = 0

    # Revenue score
    annual_revenue_score = (apollo_company.get('annual_revenue') or 0) * 0.00000002

    # Employee score
    empl_num = apollo_company.get('estimated_num_employees') or 0
    if (company.get('empl_website') or 0) > empl_num:
        empl_num = company.get('empl_website')
    empl_score = (empl_num * 0.02)

    ranking_score += min(annual_revenue_score, 20)
    ranking_score += min(empl_score, 20)

    return ranking_score

async def calculate_company_ranking(supabase: Client, company):
    ranking_score = 0
    ranking_score += await ranking_score_products(supabase, company)
    ranking_score += await ranking_score_rev_empl(supabase, company)

    # round to 2 decimal places
    return round(ranking_score, 2) 