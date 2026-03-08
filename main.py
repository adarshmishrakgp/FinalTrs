from fastapi import FastAPI, UploadFile, File, Form, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta
from typing import List, Optional
import io
import logging

from database import get_db, engine, Base
import models
import schemas
import crud
import registrationcrud
from s3_service import upload_file_to_s3
from security import verify_password, create_access_token, decode_access_token, ACCESS_TOKEN_EXPIRE_MINUTES

# Initialize Database tables if they don't exist
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Property API")

# Allow requests from any frontend origin
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

# ==========================================
# 🔐 AUTHENTICATION & USERS
# ==========================================
def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    payload = decode_access_token(token)
    if payload is None:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
        
    user_email = payload.get("sub")
    role = payload.get("role")
    
    user = None
    if role == "customer":
        user = db.query(models.Customer).filter(models.Customer.email == user_email).first()
    elif role == "agent":
        user = db.query(models.Agent).filter(models.Agent.email == user_email).first()
    elif role == "builder":
        user = db.query(models.Builder).filter(models.Builder.email == user_email).first()

    if not user:
        raise HTTPException(status_code=401, detail="User not found")
        
    user.role = role # Dynamically attach role
    return user

@app.post("/login", response_model=schemas.Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    # Standardised for Swagger UI and generic frontend use
    user = db.query(models.Customer).filter(models.Customer.email == form_data.username).first()
    role = "customer"
    
    if not user:
        user = db.query(models.Agent).filter(models.Agent.email == form_data.username).first()
        role = "agent"
    if not user:
        user = db.query(models.Builder).filter(models.Builder.email == form_data.username).first()
        role = "builder"
        
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")
        
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email, "role": role, "user_id": user.id},
        expires_delta=access_token_expires
    )

    return {"access_token": access_token, "token_type": "bearer", "role": role}

@app.get("/users/me", response_model=schemas.UserResponse)
def get_current_user_profile(current_user = Depends(get_current_user)):
    """Fetch the profile of the currently logged in user"""
    return {
        "id": current_user.id,
        "email": current_user.email,
        "role": getattr(current_user, "role", "unknown"),
        "full_name": getattr(current_user, "full_name", None),
        "company_name": getattr(current_user, "company_name", None),
        "phone": current_user.phone
    }

# ==========================================
# 🏠 REGISTRATION
# ==========================================
@app.post("/register/customer")
def register_customer(data: schemas.CustomerCreate, db: Session = Depends(get_db)):
    return registrationcrud.create_customer(db, data)

@app.post("/register/agent")
def register_agent(data: schemas.AgentCreate, db: Session = Depends(get_db)):
    return registrationcrud.create_agent(db, data)

@app.post("/register/builder")
def register_builder(data: schemas.BuilderCreate, db: Session = Depends(get_db)):
    return registrationcrud.create_builder(db, data)

# ==========================================
# 🏙️ PROPERTIES
# ==========================================
@app.post("/createproperty", response_model=schemas.PropertyResponse)
def create_property(
    request: schemas.PropertyCreate, 
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    try:
        # Check permissions
        if current_user.role not in ["agent", "builder"]:
            raise HTTPException(status_code=403, detail="Customers cannot create properties.")
            
        new_property = crud.create_property(
            db=db, 
            property_data=request, 
            # owner_id=current_user.id,
            # owner_role=current_user.role
        )
        
        # Format for response
        prop_dict = schemas.PropertyResponse.model_validate(new_property).model_dump()
        prop_dict["image_ids"] = request.image_ids
        return prop_dict

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logging.error(f"Error creating property: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

@app.get("/properties", response_model=list[schemas.PropertyResponse])
def get_properties(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    return crud.get_all_properties(db, skip, limit)

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
    return crud.search_properties(
        db=db, search_query=search_query, property_type=property_type, 
        min_price=min_price, max_price=max_price, bedrooms=bedrooms, 
        bathrooms=bathrooms, property_post_status=property_post_status,
        possession_status=possession_status, is_price_negotiable=is_price_negotiable,
        skip=skip, limit=limit
    )

@app.get("/properties/{property_id}", response_model=schemas.PropertyResponse)
def get_property_by_id(property_id: int, db: Session = Depends(get_db)):
    property_obj = db.query(models.Property).filter(models.Property.id == property_id).first()
    if not property_obj:
        raise HTTPException(status_code=404, detail="Property not found")
        
    # Get associated images
    images = db.query(models.PropertyImage).filter(models.PropertyImage.property_id == property_id).all()
    image_ids = [img.id for img in images]
    
    response_dict = schemas.PropertyResponse.model_validate(property_obj).model_dump()
    response_dict["image_ids"] = image_ids
    return response_dict

# ==========================================
# 🖼️ IMAGES
# ==========================================
@app.post("/upload-image")
async def upload_image(
    image: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """ Uploads an image to S3 AND registers it in the database to get an ID """
    url = upload_file_to_s3(image, db)
    
    # Save to database to generate an ID
    db_image = models.PropertyImage(
        image_url=url,
        # Leaving image_data blank to save DB space since it's on S3
    )
    db.add(db_image)
    db.commit()
    db.refresh(db_image)

    return {
        "message": "Image uploaded successfully",
        "image_url": url,
        "image_id": db_image.id # Frontend uses this to link to the property!
    }

@app.post("/property-images/download")
def download_property_images(
    request: schemas.ImageDownloadRequest,
    db: Session = Depends(get_db),
):
    if not request.image_ids:
        raise HTTPException(status_code=400, detail="image_ids required")

    zip_bytes = crud.get_images_as_zip(db, request.image_ids)
    if not zip_bytes:
        raise HTTPException(status_code=404, detail="Images not found")

    return StreamingResponse(
        io.BytesIO(zip_bytes),
        media_type="application/zip",
        headers={"Content-Disposition": "attachment; filename=property_images.zip"},
    )

# ==========================================
# 📋 LEGACY / CURRENT PROPERTIES
# ==========================================
@app.post("/current-properties/create", response_model=schemas.CurrentPropertyResponse)
def create_current_property_api(property_data: schemas.CurrentPropertyCreate, db: Session = Depends(get_db)):
    return crud.create_current_property(db, property_data)

@app.get("/current-properties", response_model=list[schemas.CurrentPropertyResponse])
def list_current_properties_api(skip: int = 0, limit: int = 50, db: Session = Depends(get_db)):
    return crud.list_current_properties(db, skip, limit)