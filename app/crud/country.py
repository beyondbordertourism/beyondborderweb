from typing import List, Optional, Dict, Any
from bson import ObjectId
from pymongo import ReturnDocument
from app.core.database import get_database
from app.models.country import Country, CountryCreate, CountryUpdate
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class CountryCRUD:
    def __init__(self):
        self.collection_name = "countries"

    def get_collection(self):
        db = get_database()
        if db is None:
            logger.warning("Database not available")
            return None
        return db[self.collection_name]

    async def create(self, country_data: CountryCreate) -> Country:
        collection = self.get_collection()
        if collection is None:
            raise Exception("Database not available")
        
        # Convert to dict and add timestamps
        country_dict = country_data.model_dump()
        country_dict["created_at"] = datetime.utcnow()
        country_dict["updated_at"] = datetime.utcnow()
        
        result = await collection.insert_one(country_dict)
        
        # Fetch the created document
        created_country = await collection.find_one({"_id": result.inserted_id})
        return Country(**created_country)

    async def get_by_id(self, country_id: str) -> Optional[Country]:
        collection = self.get_collection()
        if collection is None:
            return None
            
        if not ObjectId.is_valid(country_id):
            return None
            
        country = await collection.find_one({"_id": ObjectId(country_id)})
        return Country(**country) if country else None

    async def get_by_slug(self, slug: str) -> Optional[Country]:
        collection = self.get_collection()
        if collection is None:
            return None
        country = await collection.find_one({"slug": slug})
        return Country(**country) if country else None

    async def get_all(
        self, 
        skip: int = 0, 
        limit: int = 100, 
        published_only: bool = False,
        region: Optional[str] = None,
        visa_required: Optional[bool] = None,
        published: Optional[bool] = None,
        search: Optional[str] = None,
        sort: Optional[str] = None,
        **kwargs
    ) -> List[Country]:
        collection = self.get_collection()
        if collection is None:
            return []
        
        # Build filter
        filter_dict = {}
        
        # Handle published filter (for admin interface)
        if published_only:
            filter_dict["published"] = True
        elif published is not None:
            filter_dict["published"] = published
        
        # Add other filters
        if region:
            filter_dict["region"] = region
        if visa_required is not None:
            filter_dict["visa_required"] = visa_required
        
        # Add search functionality
        if search:
            # Use regex for flexible search across name, summary, and slug
            search_regex = {"$regex": search, "$options": "i"}
            filter_dict["$or"] = [
                {"name": search_regex},
                {"slug": search_regex},
                {"summary": search_regex}
            ]
        
        # Determine sort order
        sort_field = "updated_at"
        sort_direction = -1
        
        if sort:
            if sort == "name":
                sort_field = "name"
                sort_direction = 1  # Ascending for name
            elif sort == "created_at":
                sort_field = "created_at"
                sort_direction = -1  # Descending for created_at (newest first)
            elif sort == "updated_at":
                sort_field = "updated_at"
                sort_direction = -1  # Descending for updated_at (newest first)
        
        cursor = collection.find(filter_dict).skip(skip).limit(limit).sort(sort_field, sort_direction)
        countries = await cursor.to_list(length=limit)
        
        return [Country(**country) for country in countries]

    async def count_all(
        self, 
        published_only: bool = False,
        region: Optional[str] = None,
        visa_required: Optional[bool] = None,
        published: Optional[bool] = None,
        search: Optional[str] = None,
        **kwargs
    ) -> int:
        collection = self.get_collection()
        if collection is None:
            return 0
        
        # Build filter (same as get_all)
        filter_dict = {}
        
        # Handle published filter (for admin interface)
        if published_only:
            filter_dict["published"] = True
        elif published is not None:
            filter_dict["published"] = published
        
        # Add other filters
        if region:
            filter_dict["region"] = region
        if visa_required is not None:
            filter_dict["visa_required"] = visa_required
        
        # Add search functionality
        if search:
            # Use regex for flexible search across name, summary, and slug
            search_regex = {"$regex": search, "$options": "i"}
            filter_dict["$or"] = [
                {"name": search_regex},
                {"slug": search_regex},
                {"summary": search_regex}
            ]
        
        return await collection.count_documents(filter_dict)

    async def get_featured(self, limit: int = 6) -> List[Country]:
        collection = self.get_collection()
        if collection is None:
            return []
        cursor = collection.find({"featured": True, "published": True}).limit(limit)
        countries = await cursor.to_list(length=limit)
        return [Country(**country) for country in countries]

    async def search(self, query: str, limit: int = 20) -> List[Country]:
        collection = self.get_collection()
        if collection is None:
            return []
        
        # Text search
        cursor = collection.find(
            {"$text": {"$search": query}, "published": True}
        ).limit(limit)
        
        countries = await cursor.to_list(length=limit)
        return [Country(**country) for country in countries]

    async def get_regions(self) -> List[str]:
        collection = self.get_collection()
        if collection is None:
            return []
        regions = await collection.distinct("region", {"published": True})
        return sorted(regions)

    async def update(self, country_id: str, country_data: CountryUpdate) -> Optional[Country]:
        collection = self.get_collection()
        if collection is None:
            return None
        
        if not ObjectId.is_valid(country_id):
            return None
        
        # Prepare update data
        update_dict = {k: v for k, v in country_data.model_dump().items() if v is not None}
        update_dict["updated_at"] = datetime.utcnow()
        
        updated_country = await collection.find_one_and_update(
            {"_id": ObjectId(country_id)},
            {"$set": update_dict},
            return_document=ReturnDocument.AFTER
        )
        
        return Country(**updated_country) if updated_country else None

    async def delete(self, country_id: str) -> bool:
        collection = self.get_collection()
        if collection is None:
            return False
        
        if not ObjectId.is_valid(country_id):
            return False
        
        result = await collection.delete_one({"_id": ObjectId(country_id)})
        return result.deleted_count > 0

    async def get_stats(self) -> Dict[str, Any]:
        collection = self.get_collection()
        if collection is None:
            return {
                "total_countries": 0,
                "published_countries": 0,
                "featured_countries": 0,
                "region_distribution": [],
                "visa_required": 0,
                "visa_free": 0
            }
        
        total_countries = await collection.count_documents({})
        published_countries = await collection.count_documents({"published": True})
        featured_countries = await collection.count_documents({"featured": True})
        
        # Get region distribution
        pipeline = [
            {"$match": {"published": True}},
            {"$group": {"_id": "$region", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}}
        ]
        region_stats = await collection.aggregate(pipeline).to_list(length=None)
        
        # Get visa requirement distribution
        visa_required_count = await collection.count_documents({"visa_required": True, "published": True})
        visa_free_count = await collection.count_documents({"visa_required": False, "published": True})
        
        return {
            "total_countries": total_countries,
            "published_countries": published_countries,
            "featured_countries": featured_countries,
            "region_distribution": region_stats,
            "visa_required": visa_required_count,
            "visa_free": visa_free_count
        }

# Create instance
country_crud = CountryCRUD() 