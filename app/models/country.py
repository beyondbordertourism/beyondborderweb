from pydantic import BaseModel, Field, ConfigDict, field_validator
from typing import Optional, List, Dict, Any, Union
from datetime import datetime
from uuid import UUID
import json

class Fee(BaseModel):
    id: Optional[UUID] = None
    visa_type_id: Optional[UUID] = None
    type: str
    amount: Optional[str] = None
    original_currency: Optional[str] = None
    note: Optional[str] = None
    processing_time: Optional[str] = None
    available: bool = True

class ProcessingTime(BaseModel):
    id: Optional[UUID] = None
    country_id: Optional[str] = None
    type: str
    duration: str
    notes: Optional[str] = None

class Document(BaseModel):
    id: Optional[UUID] = None
    country_id: Optional[str] = None
    name: str
    type: str
    specifications: Union[List[Dict[str, Any]], Dict[str, Any]] = Field(default_factory=list)
    required: bool = True

    @field_validator('specifications', mode='before')
    def parse_specifications(cls, v):
        if isinstance(v, str):
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                return []
        if v is None:
            return []
        return v

class VisaType(BaseModel):
    id: Optional[UUID] = None
    country_id: Optional[str] = None
    name: str
    purpose: Optional[str] = None
    entry_type: Optional[str] = None
    validity: Optional[str] = None
    stay_duration: Optional[str] = None
    extendable: Optional[bool] = None
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

class ApplicationProcess(BaseModel):
    id: Optional[UUID] = None
    country_id: Optional[str] = None
    method: str
    note: Optional[str] = None
    steps: List[Union[str, ApplicationMethod]] = []
    alternative_method: Dict[str, Any] = {}

    @field_validator('steps', mode='before')
    def parse_steps(cls, v):
        if isinstance(v, str):
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                return []
        if v is None:
            return []
        return v

class Embassy(BaseModel):
    city: str
    address: Optional[str] = None
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
        from_attributes=True
    )
    
    id: str = Field(..., alias='slug')  # This is the slug in Supabase
    name: str
    flag: Optional[str] = None
    region: Optional[str] = None
    visa_required: Optional[bool] = None
    last_updated: Optional[str] = None
    summary: Optional[str] = None
    
    # Related data
    visa_types: List[VisaType] = []
    documents: List[Document] = []
    processing_times: List[ProcessingTime] = []
    application_methods: List[ApplicationProcess] = []
    embassies: Optional[List[Embassy]] = []
    photo_requirements: Optional[Dict[str, Any]] = None
    important_notes: Optional[List[ImportantNote]] = []

class CountryCreate(BaseModel):
    id: str = Field(..., alias='slug')
    name: str
    flag: Optional[str] = None
    region: Optional[str] = None
    visa_required: Optional[bool] = None
    last_updated: Optional[str] = None
    summary: Optional[str] = None

class CountryUpdate(BaseModel):
    name: Optional[str] = None
    flag: Optional[str] = None
    region: Optional[str] = None
    visa_required: Optional[bool] = None
    last_updated: Optional[str] = None
    summary: Optional[str] = None

    def model_dump(self, **kwargs):
        """Override model_dump to ensure ID is converted to string"""
        data = super().model_dump(**kwargs)
        if 'id' in data and isinstance(data['id'], UUID):
            data['id'] = str(data['id'])
        return data 