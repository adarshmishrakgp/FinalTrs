from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
import models
import schemas
from security import hash_password

def create_customer(db: Session, data: schemas.CustomerCreate, profile_image_url: str = None):
    try:
        obj = models.Customer(
            full_name=data.full_name,
            email=data.email,
            phone=data.phone,
            password_hash=hash_password(data.password),
            city=data.city,
            company_name=getattr(data, 'company_name', None),
            profile_image_url=profile_image_url
        )
        db.add(obj)
        db.commit()
        db.refresh(obj)
        return obj
    except Exception as e:
        db.rollback()  
        raise e       

def create_agent(db: Session, data: schemas.AgentCreate, profile_image_url: str = None):
    try:
        obj = models.Agent(
            full_name=data.full_name,
            email=data.email,
            phone=data.phone,
            password_hash=hash_password(data.password),
            rera_number=data.rera_number,
            agency_name=getattr(data, 'agency_name', None),
            city=data.city,
            company_name=getattr(data, 'company_name', None), 
            profile_image_url=profile_image_url
        )
        db.add(obj)
        db.commit()
        db.refresh(obj)
        return obj
    except Exception as e:
        db.rollback()
        raise e

def create_builder(db: Session, data: schemas.BuilderCreate, profile_image_url: str = None):
    try:
        obj = models.Builder(
            company_name=data.company_name, 
            contact_person=getattr(data, 'contact_person', None),
            email=data.email,
            phone=data.phone,
            password_hash=hash_password(data.password),
            rera_number=getattr(data, 'rera_number', None),
            city=data.city,
            profile_image_url=profile_image_url
        )
        db.add(obj)
        db.commit()
        db.refresh(obj)
        return obj
    except Exception as e:
        db.rollback()
        raise e