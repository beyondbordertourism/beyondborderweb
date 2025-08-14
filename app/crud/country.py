from typing import List, Optional, Dict, Any
from app.core.db import Database
from app.models.country import Country, CountryCreate, CountryUpdate

class CountryCRUD:
    def __init__(self):
        self.db = Database()

    def create(self, country_data: CountryCreate) -> Dict:
        return self.db.add_country(country_data.model_dump())

    def get_by_id(self, id: str) -> Optional[Dict]:
        return self.db.get_country_by_id(id)

    def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
        published: Optional[bool] = None,
        region: Optional[str] = None,
        search: Optional[str] = None,
        sort: Optional[str] = None,
    ) -> List[Dict]:
        countries = self.db.get_all_countries()

        # Apply filters
        if published is not None:
            countries = [c for c in countries if c.get('published') == published]
        if region:
            countries = [c for c in countries if c.get('region') == region]
        if search:
            search = search.lower()
            countries = [c for c in countries if search in c.get('name', '').lower() or search in c.get('summary', '').lower()]

        # Apply sorting
        if sort:
            reverse = False
            if sort.startswith('-'):
                sort = sort[1:]
                reverse = True
            countries = sorted(countries, key=lambda x: x.get(sort, ''), reverse=reverse)

        return countries[skip:skip + limit]
        
    def update(self, id: str, country_data: CountryUpdate) -> Optional[Dict]:
        # Only allow scalar fields that map to columns in countries table
        allowed_fields = {
            'name', 'flag', 'region', 'visa_required', 'last_updated',
            'summary', 'published', 'featured', 'photo_requirements',
            'embassies', 'important_notes', 'hero_image_url'
        }
        raw = country_data.model_dump(exclude_unset=True)
        filtered = {k: v for k, v in raw.items() if k in allowed_fields}
        return self.db.update_country(id, filtered)

    def delete(self, id: str) -> bool:
        return self.db.delete_country(id)

    def search(self, query: str) -> List[Dict]:
        return self.db.search_countries(query)

country_crud = CountryCRUD() 