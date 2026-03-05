#from fastapi import FastAPI

#app = FastAPI()
from fastapi import FastAPI, UploadFile, File, Form, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from database import get_db
from typing import List, Optional
import crud,registrationcrud
import schemas
import logging
import io
from schemas import ImageDownloadRequest
from crud import get_images_as_zip
from s3_service import upload_file_to_s3
from models import Property
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Property API")

# Allow requests from any frontend origin (all domains/ports)
origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

'''
# ✅ CREATE PROPERTY
@app.post("/createproperty")
def create_property(
    request: schemas.PropertyCreate,
    db: Session = Depends(get_db)
):
    try:
        # ✅ Create property object (FULL FIELD MAPPING)
        new_property = Property(
            title=request.title,
            property_type=request.property_type,
            city=request.city,
            project_name=request.project_name,

            possession_status=request.possession_status,
            property_post_status=request.property_post_status,

            expected_price=request.expected_price,
            booking_amount=request.booking_amount,
            is_price_negotiable=request.is_price_negotiable,

            carpet_area=request.carpet_area,
            super_area=request.super_area,

            bedrooms=request.bedrooms,
            bathrooms=request.bathrooms,
            balconies=request.balconies,

            rera_id=request.rera_id,
            builder_name=request.builder_name,
            builder_logo=request.builder_logo,

            nearby_landmarks=request.nearby_landmarks,
            latitude=request.latitude,
            longitude=request.longitude,
            map_address=request.map_address,

            property_features=request.property_features,
            facilities=request.facilities,

            property_age=request.property_age,
            floor_number=request.floor_number,
            total_floors=request.total_floors,

            facing=request.facing,
            furnished_status=request.furnished_status,
            parking_spaces=request.parking_spaces,
        )

        # ✅ Save property
        db.add(new_property)
        db.commit()
        db.refresh(new_property)

        # ✅ Link images (if provided)
        if request.image_ids:
            updated = (
                db.query(schemas.PropertyImage)
                .filter(schemas.PropertyImage.id.in_(request.image_ids))
                .update(
                    {"property_id": new_property.id},
                    synchronize_session=False
                )
            )

            if updated != len(request.image_ids):
                raise HTTPException(
                    status_code=400,
                    detail="Some image_ids are invalid"
                )

            db.commit()

        # ✅ Response
        return {
            "property_id": new_property.id,
            "message": "Property created successfully"
        }

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
'''

# ✅ GET ALL PROPERTIES
@app.get("/properties", response_model=list[schemas.PropertyResponse])
def get_properties(
    skip: int = 0,
    limit: int = 10,
    db: Session = Depends(get_db)
):
    return crud.get_all_properties(db, skip, limit)


@app.post("/property-images/download")
def download_property_images(
    request: ImageDownloadRequest,
    db: Session = Depends(get_db),
):
    """
    Download multiple property images as ZIP
    """

    if not request.image_ids:
        raise HTTPException(status_code=400, detail="image_ids required")

    zip_bytes = get_images_as_zip(db, request.image_ids)

    if not zip_bytes:
        raise HTTPException(status_code=404, detail="Images not found")

    return StreamingResponse(
        io.BytesIO(zip_bytes),
        media_type="application/zip",
        headers={
            "Content-Disposition": "attachment; filename=property_images.zip"
        },
    )




@app.post("/register/customer")
def register_customer(data: schemas.CustomerCreate, db: Session = Depends(get_db)):
    return registrationcrud.create_customer(db, data)


@app.post("/register/agent")
def register_agent(data: schemas.AgentCreate, db: Session = Depends(get_db)):
    return registrationcrud.create_agent(db, data)


@app.post("/register/builder")
def register_builder(data: schemas.BuilderCreate, db: Session = Depends(get_db)):
    return registrationcrud.create_builder(db, data)


@app.post("/current-properties/create", response_model=schemas.CurrentPropertyResponse)
def create_property(property_data: schemas.CurrentPropertyCreate, db: Session = Depends(get_db)):
    return crud.create_propertyNew(db, property_data)


@app.get("/current-properties", response_model=list[schemas.CurrentPropertyResponse])
def list_properties(skip: int = 0, limit: int = 50, db: Session = Depends(get_db)):
    return crud.list_propertiesNew(db, skip, limit)

@app.post("/upload-image")
async def upload_image(
    image: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    url = upload_file_to_s3(image, db)

    return {
        "message": "Image uploaded successfully",
        "image_url": url,
    }