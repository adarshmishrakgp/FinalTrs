from sqlalchemy import Column, BigInteger, String, Text, DECIMAL, Integer, DateTime, TIMESTAMP, func, LargeBinary, Boolean, ForeignKey, CheckConstraint
from database import Base

class Property(Base):
    __tablename__ = "properties"

    id = Column(BigInteger, primary_key=True, index=True)
    
    title = Column(String(255), nullable=False)
    bedrooms = Column(Integer, nullable=True)
    map_location = Column(String(255), nullable=True)
    agent_email = Column(String(255), nullable=True)
    property_type = Column(String(100), nullable=True)  # e.g., "Plot", "Apartment"
    image = Column(Text, nullable=True)                 # For Google Drive or S3 links
    description = Column(Text, nullable=True)
    price = Column(DECIMAL(15, 2), nullable=True)
    gallery = Column(Text, nullable=True)
    year_built = Column(Integer, nullable=True)
    status = Column(String(100), nullable=True)         # e.g., "Sell", "Rent"
    agent_name = Column(String(255), nullable=True)
    bathrooms = Column(Integer, nullable=True)
    agent_phone = Column(String(50), nullable=True)
    size = Column(DECIMAL(15, 2), nullable=True)        # Represents square footage/area
    floors = Column(Integer, nullable=True)
    is_approved = Column(Boolean, default=False)
    owner = Column(String(255), nullable=True)

    created_date = Column(DateTime, default=func.now())
    updated_date = Column(DateTime, default=func.now(), onupdate=func.now())

    __table_args__ = (
        CheckConstraint('price >= 0', name='check_price_positive'),
        CheckConstraint('bedrooms >= 0', name='check_bedrooms_positive'),
        CheckConstraint('bathrooms >= 0', name='check_bathrooms_positive'),
        CheckConstraint('size >= 0', name='check_size_positive'),
    )

# ===== PROPERTY IMAGES =====
class PropertyImage(Base):
    __tablename__ = "property_images"
    id = Column(BigInteger, primary_key=True, index=True)
    property_id = Column(BigInteger, ForeignKey("properties.id", ondelete="CASCADE"), index=True, nullable=True) 
    image_url = Column(String(500), nullable=True)
    image_data = Column(LargeBinary, nullable=True)
    created_at = Column(TIMESTAMP, server_default=func.now())

# ===== USERS =====
class Customer(Base):
    __tablename__ = "customers"
    id = Column(BigInteger, primary_key=True, index=True)
    full_name = Column(String(150))
    email = Column(String(150), unique=True, index=True)
    phone = Column(String(20), unique=True)
    password_hash = Column(String(255))
    city = Column(String(100))
    created_at = Column(TIMESTAMP, server_default=func.now())
    profile_image_url = Column(String(255), nullable=True)
    company_name = Column(String(200), nullable=True)

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
    created_at = Column(TIMESTAMP, server_default=func.now())
    profile_image_url = Column(String(255), nullable=True)
    company_name = Column(String(200), nullable=True)

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
    created_at = Column(TIMESTAMP, server_default=func.now())
    profile_image_url = Column(String(255), nullable=True)

class AWSConfig(Base):
    __tablename__ = "aws_config"
    id = Column(BigInteger, primary_key=True, index=True)
    aws_access_key_id = Column(String(255), nullable=False)
    aws_secret_access_key = Column(String(255), nullable=False)
    aws_region = Column(String(100), nullable=False)
    aws_s3_bucket = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

class BuyRequirement(Base):
    __tablename__ = "buy_requirements"
    id = Column(BigInteger, primary_key=True, index=True)
    customer_id = Column(BigInteger, ForeignKey("customers.id", ondelete="CASCADE"), index=True)
    city = Column(String(100))
    property_type = Column(String(100))
    min_price = Column(DECIMAL(15, 2), nullable=True)
    max_price = Column(DECIMAL(15, 2), nullable=True)
    min_carpet_area = Column(DECIMAL(15, 2), nullable=True)
    max_carpet_area = Column(DECIMAL(15, 2), nullable=True)
    possession_status = Column(String(100))
    created_at = Column(TIMESTAMP, server_default=func.now())
    
    __table_args__ = (
        CheckConstraint('min_price >= 0', name='check_req_min_price'),
        CheckConstraint('max_price >= min_price', name='check_req_max_price'),
    )

class Favourite(Base):
    __tablename__ = "favourites"
    id = Column(BigInteger, primary_key=True, index=True)
    customer_id = Column(BigInteger, ForeignKey("customers.id", ondelete="CASCADE"), index=True)
    property_id = Column(BigInteger, ForeignKey("properties.id", ondelete="CASCADE"), index=True)
    created_at = Column(TIMESTAMP, server_default=func.now())

class Enquiry(Base):
    __tablename__ = "enquiries"
    id = Column(BigInteger, primary_key=True, index=True)
    customer_id = Column(BigInteger, ForeignKey("customers.id", ondelete="CASCADE"), index=True)
    property_id = Column(BigInteger, ForeignKey("properties.id", ondelete="CASCADE"), index=True)
    message = Column(Text)
    created_at = Column(TIMESTAMP, server_default=func.now())