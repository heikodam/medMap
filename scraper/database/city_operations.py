from .base_database_operations import BaseDatabaseOperations


class CityDatabaseOperations(BaseDatabaseOperations):
    """Database operations specific to cities"""
    
    async def get_or_create_city(self, city_name: str) -> str:
        """Get or create a city record and return its ID"""
        existing_city = self.supabase.table('city').select('id').eq('name', city_name).execute()
        if existing_city.data:
            return existing_city.data[0]['id']
        else:
            new_city = self.supabase.table('city').insert({'name': city_name}).execute()
            return new_city.data[0]['id'] 