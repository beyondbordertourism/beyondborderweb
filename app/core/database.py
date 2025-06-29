import os
import json
import uuid
import logging
import asyncio
from typing import Optional, List, Dict, Any
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorClient
from app.core.file_storage import file_storage

logger = logging.getLogger(__name__)

def get_database():
    """Get database instance"""
    return db.adapter

# Global database connection
class DatabaseConnection:
    def __init__(self):
        self.client = None
        self.adapter = None

db = DatabaseConnection()

async def connect_to_mongo():
    """Create database connection"""
    try:
        # Try to import config, fallback to environment variables
        try:
            import config
            MONGODB_URL = config.MONGODB_URL
            DATABASE_NAME = config.DATABASE_NAME
        except ImportError:
            # Fallback to environment variables
            MONGODB_URL = os.getenv("MONGODB_URL", "mongodb+srv://inshamanowar22:YVfCabwE81MkSY68@visa-countries.gsywcpw.mongodb.net/")
            DATABASE_NAME = os.getenv("DATABASE_NAME", "visa_website")
            
            # Replace placeholder with actual password from environment variable
            db_password = os.getenv("MONGODB_PASSWORD", "")
            if db_password and "your_password_here" in MONGODB_URL:
                MONGODB_URL = MONGODB_URL.replace("your_password_here", db_password)
        
        print(f"🔄 Attempting to connect to MongoDB...")
        
        # Add SSL/TLS configuration for better compatibility
        client = AsyncIOMotorClient(
            MONGODB_URL,
            serverSelectionTimeoutMS=30000,
            connectTimeoutMS=30000,
            socketTimeoutMS=30000,
            maxPoolSize=10,
            retryWrites=True,
            ssl=True,
            ssl_cert_reqs=None  # Don't require SSL certificates
        )
        
        # Test the connection with shorter timeout
        await asyncio.wait_for(client.admin.command('ping'), timeout=10)
        print(f"✅ Successfully connected to MongoDB!")
        
        database = client[DATABASE_NAME]
        db.client = client
        db.adapter = DatabaseAdapter(database)
        
        # Create indexes for better performance
        await create_indexes()
        
    except Exception as e:
        print(f"⚠️  MongoDB connection failed: {e}")
        print(f"⚠️  Using file storage - data will be persisted in local files")
        db.adapter = FileStorageAdapter()

async def close_mongo_connection():
    """Close database connection"""
    if db.client is not None:
        db.client.close()
        print("🔒 MongoDB connection closed")

async def create_indexes():
    """Create database indexes for better performance"""
    if not isinstance(db.adapter, DatabaseAdapter):
        return
        
    try:
        countries_collection = db.adapter.database.countries
        
        # Create indexes
        await countries_collection.create_index("slug", unique=True)
        await countries_collection.create_index("name")
        await countries_collection.create_index("region")
        await countries_collection.create_index("visa_required")
        await countries_collection.create_index("published")
        await countries_collection.create_index("featured")
        await countries_collection.create_index([("name", "text"), ("summary", "text")])  # Text search
        
        print("Database indexes created successfully")
    except Exception as e:
        logger.warning(f"Failed to create indexes: {e}")

class FileStorageAdapter:
    """File storage adapter that mimics MongoDB operations"""
    
    def __init__(self, storage_dir="data_storage"):
        self.storage_dir = storage_dir
        os.makedirs(storage_dir, exist_ok=True)
        
    def __getitem__(self, collection_name):
        """Make the adapter subscriptable like MongoDB database"""
        return FileCollection(self.storage_dir, collection_name)
    
    def get_collection_path(self, collection_name):
        return os.path.join(self.storage_dir, f"{collection_name}.json")
    
    def load_collection(self, collection_name):
        path = self.get_collection_path(collection_name)
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return []
    
    def save_collection(self, collection_name, data):
        path = self.get_collection_path(collection_name)
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False, default=str)
    
    async def find_one(self, collection_name, filter_dict):
        data = self.load_collection(collection_name)
        for item in data:
            if all(item.get(k) == v for k, v in filter_dict.items()):
                return item
        return None
    
    async def find(self, collection_name, filter_dict=None, skip=0, limit=100, sort_field=None):
        data = self.load_collection(collection_name)
        
        if filter_dict:
            filtered_data = []
            for item in data:
                matches = True
                for k, v in filter_dict.items():
                    if k not in item or item[k] != v:
                        matches = False
                        break
                if matches:
                    filtered_data.append(item)
            data = filtered_data
        
        if sort_field:
            data.sort(key=lambda x: x.get(sort_field, ''))
        
        return data[skip:skip+limit] if limit else data[skip:]
    
    async def insert_one(self, collection_name, document):
        data = self.load_collection(collection_name)
        
        # Generate ID if not provided
        if '_id' not in document:
            document['_id'] = str(uuid.uuid4())
        
        data.append(document)
        self.save_collection(collection_name, data)
        
        return type('Result', (), {'inserted_id': document['_id']})()
    
    async def update_one(self, collection_name, filter_dict, update_dict):
        data = self.load_collection(collection_name)
        
        for item in data:
            if all(item.get(k) == v for k, v in filter_dict.items()):
                if '$set' in update_dict:
                    item.update(update_dict['$set'])
                else:
                    item.update(update_dict)
                self.save_collection(collection_name, data)
                return type('Result', (), {'modified_count': 1})()
        
        return type('Result', (), {'modified_count': 0})()
    
    async def delete_one(self, collection_name, filter_dict):
        data = self.load_collection(collection_name)
        
        for i, item in enumerate(data):
            if all(item.get(k) == v for k, v in filter_dict.items()):
                del data[i]
                self.save_collection(collection_name, data)
                return type('Result', (), {'deleted_count': 1})()
        
        return type('Result', (), {'deleted_count': 0})()
    
    async def delete_many(self, collection_name, filter_dict):
        """Delete multiple documents matching filter"""
        data = self.load_collection(collection_name)
        
        if not filter_dict:  # Delete all documents
            deleted_count = len(data)
            self.save_collection(collection_name, [])
            return type('Result', (), {'deleted_count': deleted_count})()
        
        # Delete matching documents
        original_count = len(data)
        filtered_data = []
        for item in data:
            matches = True
            for k, v in filter_dict.items():
                if k not in item or item[k] != v:
                    matches = False
                    break
            if not matches:  # Keep items that don't match
                filtered_data.append(item)
        
        self.save_collection(collection_name, filtered_data)
        deleted_count = original_count - len(filtered_data)
        return type('Result', (), {'deleted_count': deleted_count})()
    
    def aggregate(self, collection_name, pipeline):
        return FileStorageAggregationCursor(collection_name, pipeline, self)
    
    async def text_search(self, collection_name, search_term, limit=10):
        data = self.load_collection(collection_name)
        results = []
        search_lower = search_term.lower()
        
        for item in data:
            score = 0
            if 'name' in item and search_lower in item['name'].lower():
                score += 10
            if 'summary' in item and search_lower in item['summary'].lower():
                score += 5
            if 'region' in item and search_lower in item['region'].lower():
                score += 3
            
            if score > 0:
                results.append((item, score))
        
        results.sort(key=lambda x: x[1], reverse=True)
        return [item for item, score in results[:limit]]

class FileCollection:
    """File collection adapter that mimics MongoDB collection operations"""
    
    def __init__(self, storage_dir, collection_name):
        self.storage_dir = storage_dir
        self.collection_name = collection_name
        self.adapter = FileStorageAdapter(storage_dir)

    async def find_one(self, filter_dict):
        return await self.adapter.find_one(self.collection_name, filter_dict)

    def find(self, filter_dict=None, skip=0, limit=100, sort=None):
        return FileStorageCursor(self.collection_name, filter_dict, skip, limit, sort, self.adapter)

    async def insert_one(self, document):
        return await self.adapter.insert_one(self.collection_name, document)

    async def update_one(self, filter_dict, update_dict):
        return await self.adapter.update_one(self.collection_name, filter_dict, update_dict)

    async def delete_one(self, filter_dict):
        return await self.adapter.delete_one(self.collection_name, filter_dict)

    async def delete_many(self, filter_dict):
        return await self.adapter.delete_many(self.collection_name, filter_dict)

    def aggregate(self, pipeline):
        return FileStorageAggregationCursor(self.collection_name, pipeline, self.adapter)

    async def count_documents(self, filter_dict=None):
        data = self.adapter.load_collection(self.collection_name)
        
        if not filter_dict:
            return len(data)
        
        count = 0
        for item in data:
            matches = True
            for k, v in filter_dict.items():
                if k not in item or item[k] != v:
                    matches = False
                    break
            if matches:
                count += 1
        
        return count

    async def distinct(self, field, filter_dict=None):
        data = self.adapter.load_collection(self.collection_name)
        
        if filter_dict:
            filtered_data = []
            for item in data:
                matches = True
                for k, v in filter_dict.items():
                    if k not in item or item[k] != v:
                        matches = False
                        break
                if matches:
                    filtered_data.append(item)
            data = filtered_data
        
        values = set()
        for item in data:
            if field in item and item[field] is not None:
                values.add(item[field])
        
        return list(values)
    
    async def find_one_and_update(self, filter_dict, update_dict, return_document=None):
        """Find and update a document"""
        data = self.adapter.load_collection(self.collection_name)
        
        for item in data:
            if all(item.get(k) == v for k, v in filter_dict.items()):
                if '$set' in update_dict:
                    item.update(update_dict['$set'])
                else:
                    item.update(update_dict)
                self.adapter.save_collection(self.collection_name, data)
                return item
        
        return None

class FileStorageCursor:
    """File storage cursor that mimics MongoDB cursor"""
    
    def __init__(self, collection_name, filter_dict, skip, limit, sort, adapter):
        self.collection_name = collection_name
        self.filter_dict = filter_dict
        self._skip = skip
        self._limit = limit
        self._sort = sort
        self.adapter = adapter
    
    def skip(self, count):
        """Skip documents"""
        self._skip = count
        return self
    
    def limit(self, count):
        """Limit documents"""
        self._limit = count
        return self
    
    def sort(self, field, direction=1):
        """Sort documents"""
        self._sort = {field: direction}
        return self

    async def to_list(self, length=None):
        data = self.adapter.load_collection(self.collection_name)
        
        if self.filter_dict:
            filtered_data = []
            for item in data:
                matches = True
                for k, v in self.filter_dict.items():
                    if k == "$text":
                        # Handle text search
                        search_term = v.get("$search", "").lower()
                        text_match = False
                        if 'name' in item and search_term in item['name'].lower():
                            text_match = True
                        elif 'summary' in item and search_term in item['summary'].lower():
                            text_match = True
                        if not text_match:
                            matches = False
                            break
                    elif k not in item or item[k] != v:
                        matches = False
                        break
                if matches:
                    filtered_data.append(item)
            data = filtered_data
        
        if self._sort:
            sort_field = list(self._sort.keys())[0] if isinstance(self._sort, dict) else self._sort
            reverse = False
            if isinstance(self._sort, dict):
                reverse = list(self._sort.values())[0] == -1
            data.sort(key=lambda x: x.get(sort_field, ''), reverse=reverse)
        
        result = data[self._skip:self._skip+self._limit] if self._limit else data[self._skip:]
        return result[:length] if length else result

class FileStorageAggregationCursor:
    """File storage aggregation cursor"""
    
    def __init__(self, collection_name, pipeline, adapter):
        self.collection_name = collection_name
        self.pipeline = pipeline
        self.adapter = adapter
    
    async def to_list(self, length=None):
        data = self.adapter.load_collection(self.collection_name)
        
        # Simple aggregation processing
        for stage in self.pipeline:
            if '$match' in stage:
                match_conditions = stage['$match']
                filtered_data = []
                for item in data:
                    matches = True
                    for k, v in match_conditions.items():
                        if k not in item or item[k] != v:
                            matches = False
                            break
                    if matches:
                        filtered_data.append(item)
                data = filtered_data
            
            elif '$group' in stage:
                group_stage = stage['$group']
                group_id = group_stage.get('_id')
                
                if group_id is None:
                    # Count all documents
                    result = [{'_id': None, 'count': len(data)}]
                    data = result
                elif isinstance(group_id, str) and group_id.startswith('$'):
                    # Group by field
                    field = group_id[1:]  # Remove $
                    groups = {}
                    for item in data:
                        key = item.get(field)
                        if key not in groups:
                            groups[key] = []
                        groups[key].append(item)
                    
                    result = []
                    for key, items in groups.items():
                        group_result = {'_id': key}
                        # Handle aggregation operations
                        for op_key, op_value in group_stage.items():
                            if op_key != '_id':
                                if op_key == 'count' and op_value == {'$sum': 1}:
                                    group_result['count'] = len(items)
                        result.append(group_result)
                    data = result
            
            elif '$sort' in stage:
                sort_stage = stage['$sort']
                if isinstance(sort_stage, dict):
                    sort_field = list(sort_stage.keys())[0]
                    sort_direction = list(sort_stage.values())[0]
                    data.sort(key=lambda x: x.get(sort_field, 0), reverse=(sort_direction == -1))
        
        return data[:length] if length else data

class DatabaseAdapter:
    """MongoDB adapter"""
    
    def __init__(self, database):
        self.database = database
    
    def __getitem__(self, collection_name):
        """Make the adapter subscriptable like MongoDB database"""
        return self.database[collection_name]
    
    async def find_one(self, collection_name, filter_dict):
        collection = self.database[collection_name]
        return await collection.find_one(filter_dict)
    
    async def find(self, collection_name, filter_dict=None, skip=0, limit=100, sort_field=None):
        collection = self.database[collection_name]
        cursor = collection.find(filter_dict or {}).skip(skip).limit(limit)
        if sort_field:
            cursor = cursor.sort(sort_field, 1)
        return await cursor.to_list(length=limit)
    
    async def insert_one(self, collection_name, document):
        collection = self.database[collection_name]
        return await collection.insert_one(document)
    
    async def update_one(self, collection_name, filter_dict, update_dict):
        collection = self.database[collection_name]
        return await collection.update_one(filter_dict, update_dict)
    
    async def delete_one(self, collection_name, filter_dict):
        collection = self.database[collection_name]
        return await collection.delete_one(filter_dict)
    
    def aggregate(self, collection_name, pipeline):
        collection = self.database[collection_name]
        return collection.aggregate(pipeline)
    
    async def text_search(self, collection_name, search_term, limit=10):
        collection = self.database[collection_name]
        cursor = collection.find(
            {"$text": {"$search": search_term}}
        ).limit(limit)
        return await cursor.to_list(length=limit) 