import json
import os
from typing import List, Dict, Any, Optional
from datetime import datetime
import uuid

class FileStorage:
    def __init__(self, data_dir: str = "data_storage"):
        self.data_dir = data_dir
        self.countries_file = os.path.join(data_dir, "countries.json")
        self._ensure_data_dir()
        self._load_data()
    
    def _ensure_data_dir(self):
        """Create data directory if it doesn't exist"""
        os.makedirs(self.data_dir, exist_ok=True)
        if not os.path.exists(self.countries_file):
            with open(self.countries_file, 'w') as f:
                json.dump([], f)
    
    def _load_data(self) -> List[Dict]:
        """Load countries data from file"""
        try:
            with open(self.countries_file, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return []
    
    def _save_data(self, data: List[Dict]):
        """Save countries data to file"""
        with open(self.countries_file, 'w') as f:
            json.dump(data, f, indent=2, default=str)
    
    def find_one(self, filter_dict: Dict) -> Optional[Dict]:
        """Find one document matching the filter"""
        data = self._load_data()
        for item in data:
            if self._matches_filter(item, filter_dict):
                return item
        return None
    
    def find(self, filter_dict: Dict = None, skip: int = 0, limit: int = 100, sort_field: str = None) -> List[Dict]:
        """Find documents matching the filter"""
        data = self._load_data()
        
        # Apply filter
        if filter_dict:
            data = [item for item in data if self._matches_filter(item, filter_dict)]
        
        # Apply sorting
        if sort_field:
            data.sort(key=lambda x: x.get(sort_field, ''))
        
        # Apply skip and limit
        return data[skip:skip + limit]
    
    def insert_one(self, document: Dict) -> str:
        """Insert a new document"""
        data = self._load_data()
        
        # Add ID if not present
        if '_id' not in document:
            document['_id'] = str(uuid.uuid4())
        
        # Add timestamps
        document['created_at'] = datetime.utcnow().isoformat()
        document['updated_at'] = datetime.utcnow().isoformat()
        
        data.append(document)
        self._save_data(data)
        return document['_id']
    
    def update_one(self, filter_dict: Dict, update_dict: Dict) -> bool:
        """Update one document"""
        data = self._load_data()
        
        for i, item in enumerate(data):
            if self._matches_filter(item, filter_dict):
                # Apply $set operations
                if '$set' in update_dict:
                    item.update(update_dict['$set'])
                else:
                    item.update(update_dict)
                
                item['updated_at'] = datetime.utcnow().isoformat()
                data[i] = item
                self._save_data(data)
                return True
        return False
    
    def delete_one(self, filter_dict: Dict) -> bool:
        """Delete one document"""
        data = self._load_data()
        
        for i, item in enumerate(data):
            if self._matches_filter(item, filter_dict):
                data.pop(i)
                self._save_data(data)
                return True
        return False
    
    def count_documents(self, filter_dict: Dict = None) -> int:
        """Count documents matching filter"""
        data = self._load_data()
        if not filter_dict:
            return len(data)
        
        count = 0
        for item in data:
            if self._matches_filter(item, filter_dict):
                count += 1
        return count
    
    def distinct(self, field: str, filter_dict: Dict = None) -> List[Any]:
        """Get distinct values for a field"""
        data = self._load_data()
        
        if filter_dict:
            data = [item for item in data if self._matches_filter(item, filter_dict)]
        
        values = set()
        for item in data:
            if field in item:
                values.add(item[field])
        
        return list(values)
    
    def text_search(self, query: str, fields: List[str] = None) -> List[Dict]:
        """Simple text search across specified fields"""
        if not fields:
            fields = ['name', 'summary', 'region']
        
        data = self._load_data()
        query_lower = query.lower()
        results = []
        
        for item in data:
            for field in fields:
                if field in item and query_lower in str(item[field]).lower():
                    results.append(item)
                    break
        
        return results
    
    def _matches_filter(self, item: Dict, filter_dict: Dict) -> bool:
        """Check if item matches the filter"""
        for key, value in filter_dict.items():
            if key == '$text':
                # Handle text search
                search_term = value.get('$search', '').lower()
                found = False
                for field in ['name', 'summary']:
                    if field in item and search_term in str(item[field]).lower():
                        found = True
                        break
                if not found:
                    return False
            elif key not in item:
                return False
            elif item[key] != value:
                return False
        return True

# Global file storage instance
file_storage = FileStorage() 