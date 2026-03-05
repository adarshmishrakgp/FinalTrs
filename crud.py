from sqlalchemy.orm import Session
from models import Property, CurrentProperty
from schemas import PropertyCreate, PropertyImage, PropertyResponse, CurrentPropertyCreate
from collections import defaultdict
import json
import io
import zipfile


def create_property(db: Session, property_data: PropertyCreate):
    db_property = Property(**property_data.model_dump())
    db.add(db_property)
    db.commit()
    db.refresh(db_property)
    return db_property

def get_images_as_zip(db: Session, image_ids: list[int]) -> bytes:
    """
    Fetch images from DB and return zip bytes
    """

    images = (
        db.query(PropertyImage)
        .filter(PropertyImage.id.in_(image_ids))
        .all()
    )

    if not images:
        return None

    # create zip in memory
    zip_buffer = io.BytesIO()

    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        for img in images:
            if img.image_data:
                filename = f"property_image_{img.id}.jpg"
                zip_file.writestr(filename, img.image_data)

    zip_buffer.seek(0)
    return zip_buffer.read()


#def get_all_properties(db: Session, skip: int = 0, limit: int = 10):
 #   return db.query(Property).offset(skip).limit(limit).all()

def get_all_properties(db: Session, skip: int = 0, limit: int = 10):
    properties = db.query(Property).all()
    if not properties:
        return []
    for p in properties:
        if isinstance(p.property_features, str):
            p.property_features = json.loads(p.property_features)

        if isinstance(p.facilities, str):
            p.facilities = json.loads(p.facilities)
    property_ids = [p.id for p in properties]
    # ✅ fetch all images in ONE query
    images = (
        db.query(PropertyImage.property_id, PropertyImage.id)
        .filter(PropertyImage.property_id.in_(property_ids))
        .all()
    )

    # ✅ group image ids by property
    image_map = defaultdict(list)
    for property_id, image_id in images:
        image_map[property_id].append(image_id)

    # ✅ build response
    response = []
    for prop in properties:
        prop_dict = PropertyResponse.model_validate(prop).model_dump()

        # attach image ids
        prop_dict["image_ids"] = image_map.get(prop.id, [])

        response.append(prop_dict)

    return response

def create_propertyNew(db: Session, property_data: CurrentPropertyCreate):
    db_obj = CurrentProperty(**property_data.model_dump(exclude_unset=True))
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj


def list_propertiesNew(db: Session, skip: int = 0, limit: int = 50):
    return db.query(CurrentProperty).offset(skip).limit(limit).all()


def get_property(db: Session, property_id: int):
    return db.query(CurrentProperty).filter(CurrentProperty.id == property_id).first()