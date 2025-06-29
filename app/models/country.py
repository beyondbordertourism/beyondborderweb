from pydantic import BaseModel, Field, ConfigDict, field_validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from bson import ObjectId

class PyObjectId(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v, _info=None):
        if isinstance(v, ObjectId):
            return v
        if isinstance(v, str):
            # Handle UUID strings from file storage
            if len(v) == 36 and v.count('-') == 4:  # UUID format
                return v
            # Handle ObjectId strings
            if ObjectId.is_valid(v):
                return ObjectId(v)
        raise ValueError("Invalid objectid")

    @classmethod
    def __get_pydantic_json_schema__(cls, field_schema):
        field_schema.update(type="string")
        return field_schema

class Fee(BaseModel):
    type: str
    amount_inr: Optional[float] = None
    amount_usd: Optional[float] = None
    amount_local: Optional[float] = None
    local_currency: Optional[str] = None
    notes: Optional[str] = None

class ProcessingTime(BaseModel):
    type: str  # "regular", "express", "priority"
    duration: str  # "3-5 working days"
    notes: Optional[str] = None

class Document(BaseModel):
    name: str
    required: bool = True
    category: str  # "mandatory", "for_minors", "for_business", etc.
    details: Optional[str] = None
    format: Optional[str] = None  # "original", "photocopy", "scan"

class PhotoRequirement(BaseModel):
    size: str  # "35mm x 45mm"
    background: str = "white"
    format: Optional[str] = None  # "JPEG", "printed"
    specifications: List[str] = []

class VisaType(BaseModel):
    name: str
    purpose: str
    entry_type: str  # "single", "multiple"
    validity: str
    stay_duration: str
    extendable: bool = False
    fees: List[Fee] = []
    conditions: List[str] = []
    notes: Optional[str] = None
    processing_time: Optional[str] = None

class ApplicationMethod(BaseModel):
    name: str  # "embassy", "online", "voa", "agent"
    description: str
    requirements: List[str] = []
    processing_time: Optional[str] = None
    available: bool = True

class Embassy(BaseModel):
    city: str
    address: str
    phone: Optional[str] = None
    email: Optional[str] = None
    website: Optional[str] = None

class ImportantNote(BaseModel):
    type: str  # "warning", "tip", "requirement"
    content: str
    priority: str = "medium"  # "high", "medium", "low"

class Section(BaseModel):
    title: str
    content: str
    order: int
    subsections: List[Dict[str, Any]] = []

class Country(BaseModel):
    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str}
    )
    
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    slug: str  # URL-friendly name like "singapore", "south-korea"
    name: str
    flag: str
    region: str
    visa_required: bool
    last_updated: str
    summary: str
    
    # Visa Information
    visa_types: List[VisaType] = []
    documents: List[Document] = []
    photo_requirements: PhotoRequirement
    processing_times: List[ProcessingTime] = []
    fees: List[Fee] = []
    
    # Application Process
    application_methods: List[ApplicationMethod] = []
    embassies: List[Embassy] = []
    entry_points: Optional[Dict[str, List[str]]] = None  # airports, land_borders, seaports
    
    # Special Information
    visa_free_transit: Optional[Dict[str, Any]] = None
    special_conditions: List[str] = []
    important_notes: List[ImportantNote] = []
    
    # Content Sections (for flexible content)
    sections: List[Section] = []
    
    # SEO and Meta
    meta_title: Optional[str] = None
    meta_description: Optional[str] = None
    keywords: List[str] = []
    
    # Admin fields
    published: bool = True
    featured: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    def model_dump(self, **kwargs):
        """Override model_dump to ensure ID is converted to string"""
        data = super().model_dump(**kwargs)
        if 'id' in data and isinstance(data['id'], ObjectId):
            data['id'] = str(data['id'])
        return data

class CountryCreate(BaseModel):
    slug: str
    name: str
    flag: str
    region: str
    visa_required: bool
    last_updated: str
    summary: str
    visa_types: List[VisaType] = []
    documents: List[Document] = []
    photo_requirements: PhotoRequirement
    processing_times: List[ProcessingTime] = []
    fees: List[Fee] = []
    application_methods: List[ApplicationMethod] = []
    embassies: List[Embassy] = []
    entry_points: Optional[Dict[str, List[str]]] = None
    visa_free_transit: Optional[Dict[str, Any]] = None
    special_conditions: List[str] = []
    important_notes: List[ImportantNote] = []
    sections: List[Section] = []
    meta_title: Optional[str] = None
    meta_description: Optional[str] = None
    keywords: List[str] = []
    published: bool = True
    featured: bool = False

class CountryUpdate(BaseModel):
    name: Optional[str] = None
    flag: Optional[str] = None
    region: Optional[str] = None
    visa_required: Optional[bool] = None
    summary: Optional[str] = None
    visa_types: Optional[List[VisaType]] = None
    documents: Optional[List[Document]] = None
    photo_requirements: Optional[PhotoRequirement] = None
    processing_times: Optional[List[ProcessingTime]] = None
    fees: Optional[List[Fee]] = None
    application_methods: Optional[List[ApplicationMethod]] = None
    embassies: Optional[List[Embassy]] = None
    entry_points: Optional[Dict[str, List[str]]] = None
    visa_free_transit: Optional[Dict[str, Any]] = None
    special_conditions: Optional[List[str]] = None
    important_notes: Optional[List[ImportantNote]] = None
    sections: Optional[List[Section]] = None
    meta_title: Optional[str] = None
    meta_description: Optional[str] = None
    keywords: Optional[List[str]] = None
    published: Optional[bool] = None
    featured: Optional[bool] = None
    updated_at: datetime = Field(default_factory=datetime.utcnow) 