import os
import json
import logging
import asyncio
from typing import List, Optional, Dict, Any
from bson import ObjectId
from app.core.database import get_database
from app.core.database import db as core_db

logger = logging.getLogger(__name__)

class Database:
    """MongoDB database operations for countries"""
    
    def __init__(self):
        self.db = None
    
    def _get_db(self):
        """Get database adapter"""
        if self.db is None:
            from app.core.database import db
            if db.adapter is None:
                raise RuntimeError("Database not connected. Please ensure MongoDB connection is established.")
            self.db = db.adapter
        return self.db
    
    def _normalize_country(self, country: Dict) -> Dict:
        """Normalize country document from MongoDB to match expected format"""
        if country is None:
            return None
        
        # Use the slug 'id' field if present, otherwise fall back to _id
        if '_id' in country:
            if 'id' not in country or not country['id']:
                country['id'] = str(country['_id'])
            del country['_id']
        
        # Ensure all nested fields exist
        if 'visa_types' not in country:
            country['visa_types'] = []
        if 'documents' not in country:
            country['documents'] = []
        if 'processing_times' not in country:
            country['processing_times'] = []
        if 'application_methods' not in country:
            country['application_methods'] = []
        if 'embassies' not in country:
            country['embassies'] = []
        if 'important_notes' not in country:
            country['important_notes'] = []
        
        return country
    
    def get_all_countries(self) -> List[Dict]:
        """Get all countries from MongoDB (synchronous wrapper)"""
        loop = getattr(core_db, 'loop', None)
        if not loop or loop.is_closed():
            raise RuntimeError("Database event loop is not available")
        future = asyncio.run_coroutine_threadsafe(self._get_all_countries_async(), loop)
        return future.result()
    
    async def _get_all_countries_async(self) -> List[Dict]:
        """Get all countries from MongoDB (async implementation)"""
        try:
            db_adapter = self._get_db()
            # Access collection through adapter's __getitem__
            collection = db_adapter['countries']
            cursor = collection.find({})
            countries = await cursor.to_list(length=1000)
            return [self._normalize_country(c) for c in countries]
        except Exception as e:
            logger.error(f"Error getting all countries: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return []
    
    def get_country_by_id(self, id: str) -> Optional[Dict]:
        """Get a country by ID (synchronous wrapper)"""
        loop = getattr(core_db, 'loop', None)
        if not loop or loop.is_closed():
            raise RuntimeError("Database event loop is not available")
        future = asyncio.run_coroutine_threadsafe(self._get_country_by_id_async(id), loop)
        return future.result()
    
    async def _get_country_by_id_async(self, id: str) -> Optional[Dict]:
        """Get a country by ID (async implementation)"""
        try:
            db_adapter = self._get_db()
            collection = db_adapter['countries']
            
            # Try to find by id field (slug) first
            country = await collection.find_one({"id": id})
            if not country:
                # Try to find by _id as string (UUID)
                country = await collection.find_one({"_id": id})
            if not country:
                # Try to find by _id as ObjectId (if applicable)
                try:
                    country = await collection.find_one({"_id": ObjectId(id)})
                except Exception:
                    pass
            
            return self._normalize_country(country) if country else None
        except Exception as e:
            logger.error(f"Error getting country by id {id}: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return None
    
    def search_countries(self, query: str) -> List[Dict]:
        """Search countries by name, region, or summary (synchronous wrapper)"""
        loop = getattr(core_db, 'loop', None)
        if not loop or loop.is_closed():
            raise RuntimeError("Database event loop is not available")
        future = asyncio.run_coroutine_threadsafe(self._search_countries_async(query), loop)
        return future.result()
    
    async def _search_countries_async(self, query: str) -> List[Dict]:
        """Search countries by name, region, or summary (async implementation)"""
        try:
            db_adapter = self._get_db()
            collection = db_adapter['countries']
            
            # Create text search query
            search_query = {
                "$or": [
                    {"name": {"$regex": query, "$options": "i"}},
                    {"region": {"$regex": query, "$options": "i"}},
                    {"summary": {"$regex": query, "$options": "i"}}
                ]
            }
            
            cursor = collection.find(search_query).limit(10)
            countries = await cursor.to_list(length=10)
            return [self._normalize_country(c) for c in countries]
        except Exception as e:
            logger.error(f"Error searching countries: {e}")
            return []
    
    def add_country(self, data: Dict) -> Dict:
        """Add a new country (synchronous wrapper)"""
        loop = getattr(core_db, 'loop', None)
        if not loop or loop.is_closed():
            raise RuntimeError("Database event loop is not available")
        future = asyncio.run_coroutine_threadsafe(self._add_country_async(data), loop)
        return future.result()
    
    async def _add_country_async(self, data: Dict) -> Dict:
        """Add a new country (async implementation)"""
        try:
            db_adapter = self._get_db()
            collection = db_adapter['countries']
            
            # Ensure required fields
            country_doc = {
                "id": data.get('id'),
                "name": data.get('name'),
                "flag": data.get('flag'),
                "region": data.get('region'),
                "visa_required": data.get('visa_required'),
                "last_updated": data.get('last_updated'),
                "summary": data.get('summary'),
                "published": data.get('published', False),
                "featured": data.get('featured', False),
                "hero_image_url": data.get('hero_image_url'),
                "photo_requirements": data.get('photo_requirements') or {},
                "embassies": data.get('embassies') or [],
                "important_notes": data.get('important_notes') or [],
                "visa_types": data.get('visa_types') or [],
                "documents": data.get('documents') or [],
                "processing_times": data.get('processing_times') or [],
                "application_methods": data.get('application_methods') or []
            }
            
            await collection.insert_one(country_doc)
            return self._normalize_country(country_doc)
        except Exception as e:
            logger.error(f"Error adding country: {e}")
            raise
    
    def update_country(self, id: str, data: Dict) -> Optional[Dict]:
        """Update a country (synchronous wrapper)"""
        loop = getattr(core_db, 'loop', None)
        if not loop or loop.is_closed():
            raise RuntimeError("Database event loop is not available")
        future = asyncio.run_coroutine_threadsafe(self._update_country_async(id, data), loop)
        return future.result()
    
    async def _update_country_async(self, id: str, data: Dict) -> Optional[Dict]:
        """Update a country (async implementation)"""
        try:
            db_adapter = self._get_db()
            collection = db_adapter['countries']
            
            # Build update document
            update_doc = {}
            for key, value in data.items():
                if value is not None:
                    update_doc[key] = value
            
            if not update_doc:
                # No fields to update, return existing
                return await self._get_country_by_id_async(id)
            
            # Update the country
            result = await collection.update_one(
                {"id": id},
                {"$set": update_doc}
            )
            
            if result.modified_count > 0 or result.matched_count > 0:
                return await self._get_country_by_id_async(id)
            return None
        except Exception as e:
            logger.error(f"Error updating country {id}: {e}")
            return None
    
    def delete_country(self, id: str) -> bool:
        """Delete a country (synchronous wrapper)"""
        loop = getattr(core_db, 'loop', None)
        if not loop or loop.is_closed():
            raise RuntimeError("Database event loop is not available")
        future = asyncio.run_coroutine_threadsafe(self._delete_country_async(id), loop)
        return future.result()
    
    async def _delete_country_async(self, id: str) -> bool:
        """Delete a country (async implementation)"""
        try:
            db_adapter = self._get_db()
            collection = db_adapter['countries']
            result = await collection.delete_one({"id": id})
            return result.deleted_count > 0
        except Exception as e:
            logger.error(f"Error deleting country {id}: {e}")
            return False
    
    def update_visa_types(self, country_id: str, visa_types: List[Dict]):
        """Update visa types for a country (synchronous wrapper)"""
        loop = getattr(core_db, 'loop', None)
        if not loop or loop.is_closed():
            raise RuntimeError("Database event loop is not available")
        future = asyncio.run_coroutine_threadsafe(self._update_visa_types_async(country_id, visa_types), loop)
        return future.result()
    
    async def _update_visa_types_async(self, country_id: str, visa_types: List[Dict]):
        """Update visa types for a country (async implementation)"""
        try:
            db_adapter = self._get_db()
            collection = db_adapter['countries']
            
            # Clean up visa types (remove ids and country_id)
            cleaned_visa_types = []
            for vt in visa_types or []:
                vt_clean = dict(vt)
                vt_clean.pop('id', None)
                vt_clean.pop('country_id', None)
                # Clean fees within visa types
                if 'fees' in vt_clean:
                    cleaned_fees = []
                    for fee in vt_clean['fees'] or []:
                        fee_clean = dict(fee)
                        fee_clean.pop('id', None)
                        fee_clean.pop('visa_type_id', None)
                        cleaned_fees.append(fee_clean)
                    vt_clean['fees'] = cleaned_fees
                cleaned_visa_types.append(vt_clean)
            
            await collection.update_one(
                {"id": country_id},
                {"$set": {"visa_types": cleaned_visa_types}}
            )
        except Exception as e:
            logger.error(f"Error updating visa types for country {country_id}: {e}")
            raise
    
    def update_documents(self, country_id: str, documents: List[Dict]):
        """Update documents for a country (synchronous wrapper)"""
        loop = getattr(core_db, 'loop', None)
        if not loop or loop.is_closed():
            raise RuntimeError("Database event loop is not available")
        future = asyncio.run_coroutine_threadsafe(self._update_documents_async(country_id, documents), loop)
        return future.result()
    
    async def _update_documents_async(self, country_id: str, documents: List[Dict]):
        """Update documents for a country (async implementation)"""
        try:
            db_adapter = self._get_db()
            collection = db_adapter['countries']
            
            # Clean up documents
            cleaned_docs = []
            for doc in documents or []:
                doc_clean = dict(doc)
                doc_clean.pop('id', None)
                doc_clean.pop('country_id', None)
                cleaned_docs.append(doc_clean)
            
            await collection.update_one(
                {"id": country_id},
                {"$set": {"documents": cleaned_docs}}
            )
        except Exception as e:
            logger.error(f"Error updating documents for country {country_id}: {e}")
            raise
    
    def update_processing_times(self, country_id: str, times: List[Dict]):
        """Update processing times for a country (synchronous wrapper)"""
        loop = getattr(core_db, 'loop', None)
        if not loop or loop.is_closed():
            raise RuntimeError("Database event loop is not available")
        future = asyncio.run_coroutine_threadsafe(self._update_processing_times_async(country_id, times), loop)
        return future.result()
    
    async def _update_processing_times_async(self, country_id: str, times: List[Dict]):
        """Update processing times for a country (async implementation)"""
        try:
            db_adapter = self._get_db()
            collection = db_adapter['countries']
            
            # Clean up processing times
            cleaned_times = []
            for pt in times or []:
                pt_clean = dict(pt)
                pt_clean.pop('id', None)
                pt_clean.pop('country_id', None)
                cleaned_times.append(pt_clean)
            
            await collection.update_one(
                {"id": country_id},
                {"$set": {"processing_times": cleaned_times}}
            )
        except Exception as e:
            logger.error(f"Error updating processing times for country {country_id}: {e}")
            raise
    
    def update_application_methods(self, country_id: str, methods: List[Dict]):
        """Update application methods for a country (synchronous wrapper)"""
        loop = getattr(core_db, 'loop', None)
        if not loop or loop.is_closed():
            raise RuntimeError("Database event loop is not available")
        future = asyncio.run_coroutine_threadsafe(self._update_application_methods_async(country_id, methods), loop)
        return future.result()
    
    async def _update_application_methods_async(self, country_id: str, methods: List[Dict]):
        """Update application methods for a country (async implementation)"""
        try:
            db_adapter = self._get_db()
            collection = db_adapter['countries']
            
            # Clean up application methods
            cleaned_methods = []
            for am in methods or []:
                am_clean = dict(am)
                am_clean.pop('id', None)
                am_clean.pop('country_id', None)
                cleaned_methods.append(am_clean)
            
            await collection.update_one(
                {"id": country_id},
                {"$set": {"application_methods": cleaned_methods}}
            )
        except Exception as e:
            logger.error(f"Error updating application methods for country {country_id}: {e}")
            raise

# Create a singleton instance
db = Database() 
