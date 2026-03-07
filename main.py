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
from fastapi.middleware.cors import CORSMiddleware
from security import verify_password, create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES
from datetime import timedelta
from fastapi import Query
import models

app = FastAPI(title="Property API")

# Allow requests from any frontend origin (all domains/ports)
origins = ["*"]

from fastapi.security import OAuth2PasswordBearer
from security import decode_access_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

async def get_current_user(token: str = Depends(oauth2_scheme)):
    payload = decode_access_token(token)
    if payload is None:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return payload

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.post("/createproperty", response_model=schemas.PropertyResponse)
def create_property(
    request: schemas.PropertyCreate, 
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    try:
        user_id = current_user.get("user_id")
        new_property = crud.create_property(db, request, owner_id=user_id)
        return new_property

    except Exception as e:
        db.rollback()
        logging.error(f"Error creating property: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

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
 # 🔐 Just requires login
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

@app.post("/login", response_model=schemas.Token)
def login(login_data: schemas.LoginRequest, db: Session = Depends(get_db)):
    user = db.query(models.Customer).filter(models.Customer.email == login_data.email).first()
    role = "customer"
    if not user:
        user = db.query(models.Agent).filter(models.Agent.email == login_data.email).first()
        role = "agent"
    if not user:
        user = db.query(models.Builder).filter(models.Builder.email == login_data.email).first()
        role = "builder"
    if not user or not verify_password(login_data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email, "role": role, "user_id": user.id},
        expires_delta=access_token_expires
    )

    return {"access_token": access_token, "token_type": "bearer", "role": role}

@app.get("/properties/search", response_model=list[schemas.PropertyResponse])
def search_properties_api(
    search_query: Optional[str] = Query(None, description="Search by title, city, project name or builder name"),
    property_type: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    bedrooms: Optional[int] = None,
    bathrooms: Optional[int] = None,          
    property_post_status: Optional[str] = None,
    possession_status: Optional[str] = None,   
    is_price_negotiable: Optional[bool] = None,
    skip: int = 0,
    limit: int = 10,
    db: Session = Depends(get_db)
):
    properties = crud.search_properties(
        db=db, 
        search_query=search_query, 
        property_type=property_type, 
        min_price=min_price, 
        max_price=max_price, 
        bedrooms=bedrooms, 
        bathrooms=bathrooms,
        property_post_status=property_post_status,
        possession_status=possession_status,
        is_price_negotiable=is_price_negotiable,
        skip=skip, 
        limit=limit
    )
    
    import json
    for p in properties:
        if isinstance(p.property_features, str):
            p.property_features = json.loads(p.property_features)
        if isinstance(p.facilities, str):
            p.facilities = json.loads(p.facilities)
            
    return properties

@app.get("/properties/{property_id}", response_model=schemas.PropertyResponse)
def get_property_by_id(property_id: int, db: Session = Depends(get_db)):
    property_obj = db.query(models.Property).filter(models.Property.id == property_id).first()
    
    if not property_obj:
        raise HTTPException(status_code=404, detail="Property not found")
        
    import json
    if isinstance(property_obj.property_features, str):
        property_obj.property_features = json.loads(property_obj.property_features)
    if isinstance(property_obj.facilities, str):
        property_obj.facilities = json.loads(property_obj.facilities)
        
    return property_obj
