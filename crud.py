from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from models import Property, PropertyImage
from schemas import PropertyCreate, PropertyResponse, ProfileUpdate, BuyRequirementCreate, ContactOwner
from models import Customer, BuyRequirement, Favourite, Enquiry, Agent, Builder
from collections import defaultdict
import io
import zipfile
from sqlalchemy import or_
from typing import Optional

def create_property(db: Session, property_data: PropertyCreate, is_approved: bool = False):
    try:
        prop_data_dict = property_data.model_dump(exclude={"image_ids"})
        
        db_property = Property(**prop_data_dict, is_approved=is_approved)
        db.add(db_property)
        db.commit()
        db.refresh(db_property)

        # VALIDATION: Only attempt to link images if the array actually has items
        if property_data.image_ids and len(property_data.image_ids) > 0:
            db.query(PropertyImage).filter(
                PropertyImage.id.in_(property_data.image_ids)
            ).update(
                {"property_id": db_property.id}, 
                synchronize_session=False
            )
            db.commit()

        return db_property
    except Exception as e:
        db.rollback()
        raise e

def get_images_as_zip(db: Session, image_ids: list[int]) -> bytes:
    if not image_ids:
        return None
    images = db.query(PropertyImage).filter(PropertyImage.id.in_(image_ids)).all()
    if not images:
        return None
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        for img in images:
            if img.image_data:
                filename = f"property_image_{img.id}.jpg"
                zip_file.writestr(filename, img.image_data)
    zip_buffer.seek(0)
    return zip_buffer.read()

def _attach_images_to_properties(db: Session, properties: list[Property]) -> list[dict]:
    if not properties:
        return []
    property_ids = [p.id for p in properties]
    images = (
        db.query(PropertyImage.property_id, PropertyImage.id)
        .filter(PropertyImage.property_id.in_(property_ids))
        .all()
    )
    image_map = defaultdict(list)
    for property_id, image_id in images:
        image_map[property_id].append(image_id)
    response = []
    for prop in properties:
        prop_dict = PropertyResponse.model_validate(prop).model_dump()
        prop_dict["image_ids"] = image_map.get(prop.id, [])
        response.append(prop_dict)
    return response

def get_all_properties(db: Session, skip: int = 0, limit: int = 10):
    properties = db.query(Property).filter(Property.is_approved == True).offset(skip).limit(limit).all()
    return _attach_images_to_properties(db, properties)

def search_properties(
    db: Session,
    search_query: Optional[str] = None,
    property_type: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    bedrooms: Optional[int] = None,
    status: Optional[str] = None,
    skip: int = 0,
    limit: int = 10
):
    query = db.query(Property).filter(Property.is_approved == True)
    if search_query:
        search_format = f"%{search_query}%"
        query = query.filter(
            or_(
                Property.title.ilike(search_format),
                Property.city.ilike(search_format),           # Updated mapping
                Property.map_address.ilike(search_format),    # Updated mapping
                Property.builder_name.ilike(search_format)    # Updated mapping
            )
        )

    if property_type: query = query.filter(Property.property_type.ilike(property_type))
    if min_price is not None: query = query.filter(Property.expected_price >= min_price)
    if max_price is not None: query = query.filter(Property.expected_price <= max_price)
    if bedrooms is not None: query = query.filter(Property.bedrooms == bedrooms)
    if status: query = query.filter(Property.possession_status.ilike(status)) # Updated mapping

    properties = query.offset(skip).limit(limit).all()
    return _attach_images_to_properties(db, properties)

# --- CUSTOMER PROFILE ---
def update_user_profile(db: Session, user_id: int, role: str, profile_data: ProfileUpdate):
    try:
        db_user = None
        if role == "customer":
            db_user = db.query(Customer).filter(Customer.id == user_id).first()
        elif role == "agent":
            db_user = db.query(Agent).filter(Agent.id == user_id).first()
        elif role == "builder":
            db_user = db.query(Builder).filter(Builder.id == user_id).first()
            
        if db_user:
            if profile_data.phone is not None:
                db_user.phone = profile_data.phone
            if profile_data.city is not None:
                db_user.city = profile_data.city
            if profile_data.company_name is not None and hasattr(db_user, 'company_name'):
                db_user.company_name = profile_data.company_name
            if profile_data.full_name is not None and hasattr(db_user, 'full_name'):
                db_user.full_name = profile_data.full_name
                
            db.commit()
            db.refresh(db_user)
            
        return db_user
    except Exception as e:
        db.rollback()
        raise e

# --- BUY REQUIREMENTS ---
def create_buy_requirement(db: Session, req_data: BuyRequirementCreate, customer_id: int):
    try:
        db_req = BuyRequirement(**req_data.model_dump(), customer_id=customer_id)
        db.add(db_req)
        db.commit()
        db.refresh(db_req)
        return db_req
    except Exception as e:
        db.rollback()
        raise e

def get_customer_requirements(db: Session, customer_id: int):
    return db.query(BuyRequirement).filter(BuyRequirement.customer_id == customer_id).all()

def delete_buy_requirement(db: Session, req_id: int, customer_id: int):
    try:
        db_req = db.query(BuyRequirement).filter(BuyRequirement.id == req_id, BuyRequirement.customer_id == customer_id).first()
        if db_req:
            db.delete(db_req)
            db.commit()
            return True
        return False
    except Exception as e:
        db.rollback()
        raise e

# --- FAVOURITES ---
def add_favourite(db: Session, property_id: int, customer_id: int):
    try:
        prop_exists = db.query(Property).filter(Property.id == property_id).first()
        if not prop_exists:
            raise ValueError(f"Property with id {property_id} does not exist.")

        existing = db.query(Favourite).filter(Favourite.property_id == property_id, Favourite.customer_id == customer_id).first()
        if existing:
            return existing
            
        new_fav = Favourite(property_id=property_id, customer_id=customer_id)
        db.add(new_fav)
        db.commit()
        return new_fav
    except Exception as e:
        db.rollback()
        raise e

def get_customer_favourites(db: Session, customer_id: int):
    favs = db.query(Favourite).filter(Favourite.customer_id == customer_id).all()
    property_ids = [fav.property_id for fav in favs]
    properties = db.query(Property).filter(Property.id.in_(property_ids)).all()
    return _attach_images_to_properties(db, properties)

# --- ENQUIRIES ---
def create_enquiry(db: Session, data: ContactOwner, customer_id: int):
    try:
        prop_exists = db.query(Property).filter(Property.id == data.property_id).first()
        if not prop_exists:
            raise ValueError(f"Property with id {data.property_id} does not exist.")

        new_enquiry = Enquiry(customer_id=customer_id, property_id=data.property_id, message=data.message)
        db.add(new_enquiry)
        db.commit()
        return new_enquiry
    except Exception as e:
        db.rollback()
        raise e

def get_pending_properties(db: Session, skip: int = 0, limit: int = 10):
    properties = db.query(Property).filter(Property.is_approved == False).offset(skip).limit(limit).all()
    return _attach_images_to_properties(db, properties)

def get_matching_properties_for_requirement(db: Session, req_id: int, customer_id: int):
    req = db.query(BuyRequirement).filter(
        BuyRequirement.id == req_id, 
        BuyRequirement.customer_id == customer_id
    ).first()

    if not req:
        return None 
    query = db.query(Property).filter(Property.is_approved == True)

    if req.property_type:
        query = query.filter(Property.property_type.ilike(f"%{req.property_type}%"))
        
    if req.min_price is not None:
        query = query.filter(Property.expected_price >= req.min_price)
        
    if req.max_price is not None:
        query = query.filter(Property.expected_price <= req.max_price)
        
    if req.min_carpet_area is not None:
        query = query.filter(Property.carpet_area >= req.min_carpet_area)
        
    if req.max_carpet_area is not None:
        query = query.filter(Property.carpet_area <= req.max_carpet_area)
        
    if req.city:
        city_format = f"%{req.city}%"
        query = query.filter(
            or_(
                Property.city.ilike(city_format),
                Property.map_address.ilike(city_format),
                Property.title.ilike(city_format)
            )
        )

    matched_properties = query.all()
    return _attach_images_to_properties(db, matched_properties)