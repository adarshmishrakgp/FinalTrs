from fastapi import FastAPI, UploadFile, File, Form, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta
from typing import List, Optional
import io
import logging
import csv
import io
from fastapi.responses import StreamingResponse
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
        
    user.role = role 
    return user

@app.post("/login", response_model=schemas.Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
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
        if current_user.role not in ["agent", "builder"]:
            raise HTTPException(status_code=403, detail="Customers cannot create properties.")
            
        new_property = crud.create_property(db=db, property_data=request)
        
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
    search_query: Optional[str] = Query(None, description="Search by title, location, description, or agent"),
    property_type: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    bedrooms: Optional[int] = None,
    status: Optional[str] = Query(None, description="e.g., Sell, Rent"),
    skip: int = 0,
    limit: int = 10,
    db: Session = Depends(get_db)
):
    return crud.search_properties(
        db=db, search_query=search_query, property_type=property_type, 
        min_price=min_price, max_price=max_price, bedrooms=bedrooms, 
        status=status, skip=skip, limit=limit
    )

@app.get("/properties/{property_id}", response_model=schemas.PropertyResponse)
def get_property_by_id(property_id: int, db: Session = Depends(get_db)):
    property_obj = db.query(models.Property).filter(models.Property.id == property_id).first()
    if not property_obj:
        raise HTTPException(status_code=404, detail="Property not found")
        
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
    url = upload_file_to_s3(image, db)
    
    db_image = models.PropertyImage(image_url=url)
    db.add(db_image)
    db.commit()
    db.refresh(db_image)

    return {
        "message": "Image uploaded successfully",
        "image_url": url,
        "image_id": db_image.id 
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
# 📊 MASTER SHEET IMPORT / EXPORT
# ==========================================

@app.post("/properties/import")
async def import_properties_from_csv(
    file: UploadFile = File(...), 
    db: Session = Depends(get_db),
    # current_user = Depends(get_current_user) # Uncomment to secure this route
):
    """
    Upload your Master Sheet (CSV format). 
    This reads the file and extracts all details into the database.
    """
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Only CSV files are allowed. Please save your Excel sheet as a CSV.")

    contents = await file.read()
    decoded = contents.decode('utf-8')
    reader = csv.DictReader(io.StringIO(decoded))

    imported_count = 0
    
    for row in reader:
        # ✅ FIX: Safely remove commas and handle conversions
        def parse_int(val):
            if val and str(val).strip():
                clean_val = str(val).replace(',', '').strip()
                try:
                    return int(float(clean_val)) # float() first in case it's something like '1.0'
                except ValueError:
                    return None
            return None
            
        def parse_float(val):
            if val and str(val).strip():
                clean_val = str(val).replace(',', '').strip()
                try:
                    return float(clean_val)
                except ValueError:
                    return None
            return None

        # Map the CSV columns exactly to the Property model
        new_property = models.Property(
            title=row.get("Title", "Untitled"),
            bedrooms=parse_int(row.get("Bedrooms")),
            map_location=row.get("Map Location"),
            agent_email=row.get("Agent Email"),
            property_type=row.get("Property Type"),
            image=row.get("Image"),
            description=row.get("Description"),
            price=parse_float(row.get("Price")),
            gallery=row.get("Gallery"),
            year_built=parse_int(row.get("Year Built")),
            status=row.get("Status"),
            agent_name=row.get("Agent Name"),
            bathrooms=parse_int(row.get("Bathrooms")),
            agent_phone=row.get("Agent Phone"),
            size=parse_float(row.get("Size")),
            floors=parse_int(row.get("Floors")),
            owner=row.get("Owner")
        )
        db.add(new_property)
        imported_count += 1

    try:
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error during import: {str(e)}")

    return {"message": f"Successfully imported {imported_count} properties from the Master Sheet."}


@app.get("/properties/export")
def export_properties_to_csv(db: Session = Depends(get_db)):
    """
    Downloads the current live database back into a Master Sheet (CSV).
    Any new properties added via the app will be included here.
    """
    properties = db.query(models.Property).all()

    # Create an in-memory string buffer
    output = io.StringIO()
    
    # Define the exact headers matching your Master Sheet
    fieldnames = [
        "Title", "Bedrooms", "Map Location", "Agent Email", "Property Type", 
        "Image", "Description", "Price", "Gallery", "Year Built", 
        "Status", "Agent Name", "Bathrooms", "Agent Phone", "Size", 
        "Floors", "ID", "Created Date", "Updated Date", "Owner"
    ]
    
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()

    for prop in properties:
        writer.writerow({
            "Title": prop.title,
            "Bedrooms": prop.bedrooms,
            "Map Location": prop.map_location,
            "Agent Email": prop.agent_email,
            "Property Type": prop.property_type,
            "Image": prop.image,
            "Description": prop.description,
            "Price": prop.price,
            "Gallery": prop.gallery,
            "Year Built": prop.year_built,
            "Status": prop.status,
            "Agent Name": prop.agent_name,
            "Bathrooms": prop.bathrooms,
            "Agent Phone": prop.agent_phone,
            "Size": prop.size,
            "Floors": prop.floors,
            "ID": prop.id,
            "Created Date": prop.created_date.strftime("%Y-%m-%d %H:%M:%S") if prop.created_date else "",
            "Updated Date": prop.updated_date.strftime("%Y-%m-%d %H:%M:%S") if prop.updated_date else "",
            "Owner": prop.owner
        })

    output.seek(0)
    
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=updated_master_sheet.csv"}
    )

def get_current_customer(current_user = Depends(get_current_user)):
    if getattr(current_user, "role", None) != "customer":
        raise HTTPException(status_code=403, detail="Customer access only")
    return current_user

# ==========================================
# 👤 CUSTOMER API ROUTES
# ==========================================

# 1. Get Profile
@app.get("/api/customer/profile", response_model=schemas.UserResponse)
def get_profile(user = Depends(get_current_customer)):
    return user

# 2. Update Profile
@app.put("/api/customer/profile")
def update_profile(data: schemas.ProfileUpdate, db: Session = Depends(get_db), user = Depends(get_current_customer)):
    updated_user = crud.update_customer_profile(db, user.id, data)
    return {"message": "Profile updated", "data": updated_user}

# 3. Post Buy Requirement
@app.post("/api/customer/buy-requirements", response_model=schemas.BuyRequirementResponse)
def post_requirement(data: schemas.BuyRequirementCreate, db: Session = Depends(get_db), user = Depends(get_current_customer)):
    return crud.create_buy_requirement(db, data, user.id)

# 4. Get My Requirements
@app.get("/api/customer/buy-requirements", response_model=list[schemas.BuyRequirementResponse])
def get_my_requirements(db: Session = Depends(get_db), user = Depends(get_current_customer)):
    return crud.get_customer_requirements(db, user.id)

# 5. Delete Requirement
@app.delete("/api/customer/buy-requirements/{req_id}")
def delete_requirement(req_id: int, db: Session = Depends(get_db), user = Depends(get_current_customer)):
    success = crud.delete_buy_requirement(db, req_id, user.id)
    if not success:
        raise HTTPException(status_code=404, detail="Requirement not found")
    return {"message": "Requirement deleted"}

# 6. Add Favourite
@app.post("/api/customer/favourites/{property_id}")
def add_favourite(property_id: int, db: Session = Depends(get_db), user = Depends(get_current_customer)):
    crud.add_favourite(db, property_id, user.id)
    return {"message": "Property added to favourite"}

# 7. Get Favourite Properties
@app.get("/api/customer/favourites", response_model=list[schemas.PropertyResponse])
def get_favourites(db: Session = Depends(get_db), user = Depends(get_current_customer)):
    return crud.get_customer_favourites(db, user.id)

# 8. Contact Owner
@app.post("/api/customer/contact-owner")
def contact_owner(data: schemas.ContactOwner, db: Session = Depends(get_db), user = Depends(get_current_customer)):
    crud.create_enquiry(db, data, user.id)
    return {
        "message": "Enquiry sent successfully",
        "property_id": data.property_id,
        "customer_id": user.id
    }