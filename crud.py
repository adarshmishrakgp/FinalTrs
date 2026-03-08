from sqlalchemy.orm import Session
from models import Property, PropertyImage
from schemas import PropertyCreate, PropertyResponse
from collections import defaultdict
import io
import zipfile
from sqlalchemy import or_
from typing import Optional

def create_property(db: Session, property_data: PropertyCreate):
    # Extract image_ids from the Pydantic model
    prop_data_dict = property_data.model_dump(exclude={"image_ids"})
    
    db_property = Property(**prop_data_dict)
    db.add(db_property)
    db.commit()
    db.refresh(db_property)

    # Link Images to Property if any were uploaded to S3
    if property_data.image_ids:
        db.query(PropertyImage).filter(
            PropertyImage.id.in_(property_data.image_ids)
        ).update(
            {"property_id": db_property.id}, 
            synchronize_session=False
        )
        db.commit()

    return db_property

def get_images_as_zip(db: Session, image_ids: list[int]) -> bytes:
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
    
    # Fetch image metadata
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
    properties = db.query(Property).offset(skip).limit(limit).all()
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
    query = db.query(Property)

    if search_query:
        search_format = f"%{search_query}%"
        query = query.filter(
            or_(
                Property.title.ilike(search_format),
                Property.map_location.ilike(search_format),
                Property.description.ilike(search_format),
                Property.agent_name.ilike(search_format)
            )
        )

    if property_type: query = query.filter(Property.property_type.ilike(property_type))
    if min_price is not None: query = query.filter(Property.price >= min_price)
    if max_price is not None: query = query.filter(Property.price <= max_price)
    if bedrooms is not None: query = query.filter(Property.bedrooms == bedrooms)
    if status: query = query.filter(Property.status.ilike(status))

    properties = query.offset(skip).limit(limit).all()
    return _attach_images_to_properties(db, properties)