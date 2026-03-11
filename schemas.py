from pydantic import BaseModel, Field, EmailStr, ConfigDict
from typing import Optional, List
from decimal import Decimal
from datetime import datetime
class PropertyCreate(BaseModel):
    title: str
    property_type: Optional[str] = None
    image: Optional[str] = None
    
    # Structural details
    bedrooms: Optional[int] = None
    bathrooms: Optional[int] = None
    balconies: Optional[int] = None
    floor_number: Optional[int] = None
    total_floors: Optional[int] = None
    parking_spaces: Optional[int] = None
    
    # Areas & Pricing
    carpet_area: Optional[Decimal] = None
    super_area: Optional[Decimal] = None
    expected_price: Optional[Decimal] = None
    booking_amount: Optional[Decimal] = None
    is_price_negotiable: Optional[bool] = False
    
    # Location
    city: Optional[str] = None
    map_address: Optional[str] = None
    nearby_landmarks: Optional[str] = None
    latitude: Optional[Decimal] = None
    longitude: Optional[Decimal] = None
    
    # Project & Builder Info
    project_name: Optional[str] = None
    builder_name: Optional[str] = None
    builder_logo: Optional[str] = None
    rera_id: Optional[str] = None
    
    # Status & Features
    facing: Optional[str] = None
    furnished_status: Optional[str] = None
    property_age: Optional[int] = None
    possession_status: Optional[str] = None
    property_post_status: Optional[str] = "ACTIVE"
    
    # Arrays
    facilities: Optional[List[str]] = []
    property_features: Optional[List[str]] = []

    # Keeping legacy fields just in case
    description: Optional[str] = None
    status: Optional[str] = None
    owner: Optional[str] = None
    agent_name: Optional[str] = None
    agent_email: Optional[str] = None
    agent_phone: Optional[str] = None
    image_ids: Optional[List[int]] = []

    # NEW: Tracking fields
    posted_by_id: Optional[int] = None
    posted_by_role: Optional[str] = None

    

class PropertyResponse(PropertyCreate):
    id: int 
    is_approved: bool 
    created_date: Optional[datetime] = None
    updated_date: Optional[datetime] = None
    
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