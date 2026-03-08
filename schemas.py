from pydantic import BaseModel, Field, EmailStr, ConfigDict
from typing import Optional, List
from decimal import Decimal
from datetime import datetime

class PropertyCreate(BaseModel):
    title: str
    property_type: Optional[str] = None
    city: str
    project_name: Optional[str] = None
    possession_status: Optional[str] = None
    property_post_status: Optional[str] = None
    expected_price: Optional[Decimal] = None
    booking_amount: Optional[Decimal] = None
    is_price_negotiable: Optional[bool] = False
    carpet_area: Optional[Decimal] = None
    super_area: Optional[Decimal] = None
    bedrooms: Optional[int] = None
    bathrooms: Optional[int] = None
    balconies: Optional[int] = None
    rera_id: Optional[str] = None
    builder_name: Optional[str] = None
    builder_logo: Optional[str] = None
    nearby_landmarks: Optional[str] = None
    latitude: Optional[Decimal] = None
    longitude: Optional[Decimal] = None
    map_address: Optional[str] = None
    property_features: Optional[List[str]] = None
    facilities: Optional[List[str]] = None
    property_age: Optional[int] = None
    floor_number: Optional[int] = None
    total_floors: Optional[int] = None
    facing: Optional[str] = None
    furnished_status: Optional[str] = None
    parking_spaces: Optional[int] = None
    image_ids: Optional[List[int]] = []

class PropertyResponse(PropertyCreate):
    id: int 
    # owner_id: Optional[int] = None
    # owner_role: Optional[str] = None
    image_ids: List[int] = Field(default_factory=list)
    model_config = ConfigDict(from_attributes=True)

class ImageDownloadRequest(BaseModel):
    image_ids: List[int]
    model_config = ConfigDict(from_attributes=True)

class CustomerCreate(BaseModel):
    full_name: str
    email: EmailStr
    phone: str
    password: str
    city: str | None = None

class AgentCreate(BaseModel):
    full_name: str
    email: EmailStr
    phone: str
    password: str
    rera_number: str | None = None
    agency_name: str | None = None
    city: str | None = None

class BuilderCreate(BaseModel):
    company_name: str
    contact_person: str | None = None
    email: EmailStr
    phone: str
    password: str
    rera_number: str | None = None
    city: str | None = None

class UserResponse(BaseModel):
    id: int
    email: EmailStr
    role: str
    full_name: Optional[str] = None
    company_name: Optional[str] = None
    phone: str
    model_config = ConfigDict(from_attributes=True)

class CurrentPropertyBase(BaseModel):
    title: Optional[str] = None
    bedrooms: Optional[int] = None
    map_location: Optional[str] = None
    agent_email: Optional[str] = None
    property_type: Optional[str] = None
    image: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    gallery: Optional[str] = None
    year_built: Optional[int] = None
    status: Optional[str] = None
    agent_name: Optional[str] = None
    bathrooms: Optional[int] = None
    agent_phone: Optional[str] = None
    size: Optional[float] = None
    floors: Optional[int] = None
    owner: Optional[str] = None
    created_date: Optional[datetime] = None
    updated_date: Optional[datetime] = None

class CurrentPropertyCreate(CurrentPropertyBase):
    pass

class CurrentPropertyResponse(CurrentPropertyBase):
    id: int
    model_config = ConfigDict(from_attributes=True)

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str
    role: str