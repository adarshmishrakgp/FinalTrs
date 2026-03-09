from sqlalchemy.orm import Session
import models
import schemas
from security import hash_password
from sqlalchemy.orm import Session
import models
import schemas
from security import hash_password

def create_customer(db: Session, data: schemas.CustomerCreate, profile_image_url: str = None):
    obj = models.Customer(
        full_name=data.full_name,
        email=data.email,
        phone=data.phone,
        password_hash=hash_password(data.password),
        city=data.city,
        profile_image_url=profile_image_url  # Saved here!
    )
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj

def create_agent(db: Session, data: schemas.AgentCreate, profile_image_url: str = None):
    obj = models.Agent(
        full_name=data.full_name,
        email=data.email,
        phone=data.phone,
        password_hash=hash_password(data.password),
        rera_number=data.rera_number,
        agency_name=data.agency_name,
        city=data.city,
        profile_image_url=profile_image_url  # Saved here!
    )
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj

def create_builder(db: Session, data: schemas.BuilderCreate, profile_image_url: str = None):
    obj = models.Builder(
        company_name=data.company_name,
        contact_person=data.contact_person,
        email=data.email,
        phone=data.phone,
        password_hash=hash_password(data.password),
        rera_number=data.rera_number,
        city=data.city,
        profile_image_url=profile_image_url  # Saved here!
    )
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj