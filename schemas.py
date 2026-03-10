from pydantic import BaseModel, Field, EmailStr, ConfigDict
from typing import Optional, List
from decimal import Decimal
from datetime import datetime

class PropertyCreate(BaseModel):
    title: str
    bedrooms: Optional[int] = None
    map_location: Optional[str] = None
    agent_email: Optional[str] = None
    property_type: Optional[str] = None
    image: Optional[str] = None
    description: Optional[str] = None
    price: Optional[Decimal] = None
    gallery: Optional[str] = None
    year_built: Optional[int] = None
    status: Optional[str] = None
    agent_name: Optional[str] = None
    bathrooms: Optional[int] = None
    agent_phone: Optional[str] = None
    size: Optional[Decimal] = None
    floors: Optional[int] = None
    owner: Optional[str] = None
    image_ids: Optional[List[int]] = []

class PropertyResponse(PropertyCreate):
    id: int 
    is_approved: bool = False 
    created_date: Optional[datetime] = None
    updated_date: Optional[datetime] = None
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
    company_name: str | None = None 

class AgentCreate(BaseModel):
    full_name: str
    email: EmailStr
    phone: str
    password: str
    rera_number: str | None = None
    agency_name: str | None = None
    city: str | None = None
    company_name: str | None = None

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
    city: Optional[str] = None
    profile_image_url: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str
    role: str

class ProfileUpdate(BaseModel):
    full_name: Optional[str] = None
    phone: Optional[str] = None
    city: Optional[str] = None
    company_name: Optional[str] = None

class BuyRequirementCreate(BaseModel):
    city: str
    property_type: str
    min_price: Optional[float] = None
    max_price: Optional[float] = None
    min_carpet_area: Optional[float] = None
    max_carpet_area: Optional[float] = None
    possession_status: str

class BuyRequirementResponse(BuyRequirementCreate):
    id: int
    customer_id: int
    model_config = ConfigDict(from_attributes=True)

class ContactOwner(BaseModel):
    property_id: int
    message: str