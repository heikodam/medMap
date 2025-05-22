from supabase import Client

def fetch_all_companies(supabase: Client, iso_code: str, additional_filters=None):
    """
    Fetch all companies from Supabase with pagination.
    
    Args:
        supabase: Supabase client instance
        iso_code: ISO code to filter by
        additional_filters: Function that takes a query and adds additional filters
    
    Returns:
        List of all companies matching the criteria
    """
    page_size = 1000
    all_companies = []
    
    while True:
        # Start with base query
        query = supabase.table('eudamed_company')\
            .select('*')\
            .eq('iso_code', iso_code)\
            .eq('eudamed_type', 'MF')
        
        # Apply additional filters if provided
        if additional_filters:
            query = additional_filters(query)
        
        # Add pagination
        query = query.range(len(all_companies), len(all_companies) + page_size - 1)
        
        # Execute query
        result = query.execute()
        
        if not result.data:
            break
            
        all_companies.extend(result.data)
        
        if len(result.data) < page_size:
            break
    
    return all_companies 