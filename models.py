from sqlalchemy import Column, BigInteger, String, Text, DECIMAL, Integer, DateTime, TIMESTAMP, func, Enum, Boolean, \
    SmallInteger, text, TypeDecorator, TEXT
from database import Base
from typing import Optional, List
import enum
import json



class JSONEncodedList(TypeDecorator):
    impl = TEXT

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        return json.dumps(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        return json.loads(value)

# ===== ENUMS =====

class PropertyType(str, enum.Enum):
    APARTMENT = "APARTMENT"
    VILLA = "VILLA"
    HOUSE = "HOUSE"
    PLOT = "PLOT"
    OFFICE = "OFFICE"
    SHOP = "SHOP"
    WAREHOUSE = "WAREHOUSE"
    STUDIO = "STUDIO"
    PENTHOUSE = "PENTHOUSE"
    FARMHOUSE = "FARMHOUSE"


class PossessionStatus(str, enum.Enum):
    READY_TO_MOVE = "READY_TO_MOVE"
    UNDER_CONSTRUCTION = "UNDER_CONSTRUCTION"
    NEW_LAUNCH = "NEW_LAUNCH"
    RESALE = "RESALE"
    UPCOMING = "UPCOMING"


class PropertyPostStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    SOLD = "SOLD"
    RENTED = "RENTED"
    WITHDRAWN = "WITHDRAWN"
    EXPIRED = "EXPIRED"


class Facing(str, enum.Enum):
    NORTH = "NORTH"
    SOUTH = "SOUTH"
    EAST = "EAST"
    WEST = "WEST"
    NORTH_EAST = "NORTH_EAST"
    NORTH_WEST = "NORTH_WEST"
    SOUTH_EAST = "SOUTH_EAST"
    SOUTH_WEST = "SOUTH_WEST"


class FurnishedStatus(str, enum.Enum):
    UNFURNISHED = "UNFURNISHED"
    SEMI_FURNISHED = "SEMI_FURNISHED"
    FULLY_FURNISHED = "FULLY_FURNISHED"


# ===== MODEL =====

class Property(Base):
    __tablename__ = "properties"

    id = Column(BigInteger, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    property_type = Column(Enum(PropertyType))
    city = Column(String(100), nullable=False)
    project_name = Column(String(255))

    possession_status = Column(Enum(PossessionStatus))
    property_post_status = Column(
        Enum(PropertyPostStatus),
        default=PropertyPostStatus.ACTIVE
    )

    expected_price = Column(DECIMAL(15, 2))
    booking_amount = Column(DECIMAL(15, 2))
    is_price_negotiable = Column(Boolean, default=False)

    carpet_area = Column(DECIMAL(8, 2))
    super_area = Column(DECIMAL(8, 2))

    bedrooms = Column(SmallInteger)
    bathrooms = Column(SmallInteger)
    balconies = Column(SmallInteger)

    rera_id = Column(String(50))
    builder_name = Column(String(255))
    builder_logo = Column(String(500))

    nearby_landmarks = Column(Text)
    latitude = Column(DECIMAL(10, 8))
    longitude = Column(DECIMAL(11, 8))
    map_address = Column(Text)

    property_features = Column(JSONEncodedList)  # storing JSON as text
    facilities = Column(JSONEncodedList)

    property_age = Column(SmallInteger)
    floor_number = Column(SmallInteger)
    total_floors = Column(SmallInteger)

    facing = Column(Enum(Facing))
    furnished_status = Column(Enum(FurnishedStatus))

    parking_spaces = Column(SmallInteger, default=0)
    ##image_ids: Optional[List[int]] = []

class Customer(Base):
    __tablename__ = "customers"

    id = Column(BigInteger, primary_key=True, index=True)
    full_name = Column(String(150))
    email = Column(String(150), unique=True, index=True)
    phone = Column(String(20), unique=True)
    password_hash = Column(String(255))
    city = Column(String(100))
    created_at = Column(TIMESTAMP, server_default=text("CURRENT_TIMESTAMP"))


class Agent(Base):
    __tablename__ = "agents"

    id = Column(BigInteger, primary_key=True, index=True)
    full_name = Column(String(150))
    email = Column(String(150), unique=True, index=True)
    phone = Column(String(20), unique=True)
    password_hash = Column(String(255))
    rera_number = Column(String(100))
    agency_name = Column(String(150))
    city = Column(String(100))
    created_at = Column(TIMESTAMP, server_default=text("CURRENT_TIMESTAMP"))


class Builder(Base):
    __tablename__ = "builders"

    id = Column(BigInteger, primary_key=True, index=True)
    company_name = Column(String(200))
    contact_person = Column(String(150))
    email = Column(String(150), unique=True, index=True)
    phone = Column(String(20), unique=True)
    password_hash = Column(String(255))
    rera_number = Column(String(100))
    city = Column(String(100))
    created_at = Column(TIMESTAMP, server_default=text("CURRENT_TIMESTAMP"))

class CurrentProperty(Base):
    __tablename__ = "current_properties"

    id = Column(BigInteger, primary_key=True, index=True)

    title = Column(String(255))
    bedrooms = Column(String(50))
    map_location = Column(String(255))
    agent_email = Column(String(255))
    property_type = Column(String(50))
    image = Column(Text)
    description = Column(Text)
    price = Column(DECIMAL(15, 2))
    gallery = Column(Text)
    year_built = Column(Integer)
    status = Column(String(50))
    agent_name = Column(String(255))
    bathrooms = Column(Integer)
    agent_phone = Column(String(50))
    size = Column(DECIMAL(12, 2))
    floors = Column(Integer)
    owner = Column(String(255))
    created_date = Column(DateTime)
    updated_date = Column(DateTime)

    created_at = Column(TIMESTAMP, server_default=func.now())