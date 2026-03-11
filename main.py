from fastapi import FastAPI, UploadFile, File, Form, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from datetime import timedelta
from typing import List, Optional
import io
import logging
import csv
from database import get_db, engine, Base
import models
import schemas
import crud
import registrationcrud
from s3_service import upload_file_to_s3
from security import verify_password, create_access_token, decode_access_token, ACCESS_TOKEN_EXPIRE_MINUTES

# Initialize Database tables
try:
    Base.metadata.create_all(bind=engine)
except Exception as e:
    logging.error(f"Failed to initialize database: {str(e)}")

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
    try:
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
            raise HTTPException(status_code=401, detail="User not found in database")
            
        user.role = role 
        return user
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Authentication error: {str(e)}")

@app.post("/login", response_model=schemas.Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    try:
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
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Login error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error during login")

@app.get("/users/me", response_model=schemas.UserResponse)
def get_current_user_profile(current_user = Depends(get_current_user)):
    return current_user

# ==========================================
# 🏠 REGISTRATION
# ==========================================
def validate_image_file(file: UploadFile):
    if file and not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File uploaded is not a valid image format (JPEG/PNG required).")

@app.post("/register/customer", response_model=schemas.UserResponse)
def register_customer(
    full_name: str = Form(...),
    email: str = Form(...),
    phone: str = Form(...),
    password: str = Form(...),
    city: str = Form(None),
    company_name: str = Form(None),
    profile_image: UploadFile = File(None),
    db: Session = Depends(get_db)
):
    try:
        if db.query(models.Customer).filter(models.Customer.email == email).first():
            raise HTTPException(status_code=400, detail="Email already registered")
        if db.query(models.Customer).filter(models.Customer.phone == phone).first():
            raise HTTPException(status_code=400, detail="Phone already registered")

        validate_image_file(profile_image)

        image_url = None
        if profile_image:
            image_url = upload_file_to_s3(profile_image, db, folder="profiles")

        user_data = schemas.CustomerCreate(
            full_name=full_name, email=email, phone=phone, password=password, city=city, role="customer",company_name=company_name,
        )
        customer = registrationcrud.create_customer(db, user_data, profile_image_url=image_url)
        customer.role="customer"
        return customer
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="Database transaction failed")

@app.post("/register/agent", response_model=schemas.UserResponse)
def register_agent(
    full_name: str = Form(...),
    email: str = Form(...),
    phone: str = Form(...),
    password: str = Form(...),
    rera_number: str = Form(None),
    agency_name: str = Form(None),
    city: str = Form(None),
    profile_image: UploadFile = File(None),
    db: Session = Depends(get_db)
):
    try:
        if db.query(models.Agent).filter(models.Agent.email == email).first():
            raise HTTPException(status_code=400, detail="Email already registered")
        if db.query(models.Agent).filter(models.Agent.phone == phone).first():
            raise HTTPException(status_code=400, detail="Phone already registered")

        validate_image_file(profile_image)

        image_url = None
        if profile_image:
            image_url = upload_file_to_s3(profile_image, db, folder="profiles")

        user_data = schemas.AgentCreate(
            full_name=full_name, email=email, phone=phone, password=password, 
            rera_number=rera_number, agency_name=agency_name, city=city, role="agent"
        )
        agent = registrationcrud.create_agent(db, user_data, profile_image_url=image_url)
        agent.role = "agent" 
        return agent 
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="Database transaction failed")

@app.post("/register/builder", response_model=schemas.UserResponse)
def register_builder(
    company_name: str = Form(...),
    contact_person: str = Form(None),
    email: str = Form(...),
    phone: str = Form(...),
    password: str = Form(...),
    rera_number: str = Form(None),
    city: str = Form(None),
    profile_image: UploadFile = File(None),
    db: Session = Depends(get_db)
):
    try:
        if db.query(models.Builder).filter(models.Builder.email == email).first():
            raise HTTPException(status_code=400, detail="Email already registered")
        if db.query(models.Builder).filter(models.Builder.phone == phone).first():
            raise HTTPException(status_code=400, detail="Phone already registered")

        validate_image_file(profile_image)

        image_url = None
        if profile_image:
            image_url = upload_file_to_s3(profile_image, db, folder="profiles")

        user_data = schemas.BuilderCreate(
            company_name=company_name, contact_person=contact_person, email=email, 
            phone=phone, password=password, rera_number=rera_number, city=city, role="builder"
        )
        builder = registrationcrud.create_builder(db, user_data, profile_image_url=image_url)
        builder.role = "builder"
        return builder
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="Database transaction failed")

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
        auto_approve = current_user.role in ["agent", "builder"]    
        new_property = crud.create_property(db=db, property_data=request, is_approved=auto_approve)
        
        prop_dict = schemas.PropertyResponse.model_validate(new_property).model_dump()
        prop_dict["image_ids"] = request.image_ids
        return prop_dict

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logging.error(f"Error creating property: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal Server Error during property creation")

@app.get("/properties", response_model=list[schemas.PropertyResponse])
def get_properties(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    try:
        return crud.get_all_properties(db, skip, limit)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch properties: {str(e)}")

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
    try:
        return crud.search_properties(
            db=db, search_query=search_query, property_type=property_type, 
            min_price=min_price, max_price=max_price, bedrooms=bedrooms, 
            status=status, skip=skip, limit=limit
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")

@app.get("/properties/pending", response_model=list[schemas.PropertyResponse])
def get_pending_properties_api(
    skip: int = 0, 
    limit: int = 10, 
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    if current_user.role != "agent":
        raise HTTPException(status_code=403, detail="Only agents can view the pending approval queue.")
    
    try:
        return crud.get_pending_properties(db=db, skip=skip, limit=limit)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch pending properties: {str(e)}")

# ==========================================
# 📊 MASTER SHEET IMPORT / EXPORT
# ==========================================
@app.post("/properties/import")
async def import_properties_from_csv(
    file: UploadFile = File(...), 
    db: Session = Depends(get_db),
):
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Only CSV files are allowed.")

    try:
        contents = await file.read()
        if not contents:
            raise HTTPException(status_code=400, detail="The uploaded file is empty.")
            
        decoded = contents.decode('utf-8')
        reader = csv.DictReader(io.StringIO(decoded))

        # Wipe old data
        db.query(models.Property).delete()
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to process file or clear old database: {str(e)}")

    imported_count = 0
    try:
        for row in reader:
            def parse_int(val):
                if val and str(val).strip():
                    try: return int(float(str(val).replace(',', '').strip()))
                    except ValueError: return None
                return None
                
            def parse_float(val):
                if val and str(val).strip():
                    try: return float(str(val).replace(',', '').strip())
                    except ValueError: return None
                return None

            new_property = models.Property(
                title=row.get("Title", "Untitled"),
                bedrooms=parse_int(row.get("Bedrooms")),
                map_location=row.get("Map Location"),
                agent_email=row.get("Agent Email"),
                property_type=row.get("Property Type"),
                image=row.get("new image") or row.get("Image"), 
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
                owner=row.get("Owner"),
                is_approved=True 
            )
            db.add(new_property)
            imported_count += 1

        db.commit()
        return {"message": f"Successfully imported {imported_count} properties from the Master Sheet."}
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error during row insertion: {str(e)}")

@app.get("/properties/export")
def export_properties_to_csv(db: Session = Depends(get_db)):
    try:
        properties = db.query(models.Property).all()
        if not properties:
            raise HTTPException(status_code=404, detail="No properties found to export.")

        output = io.StringIO()
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
                "Title": prop.title, "Bedrooms": prop.bedrooms, "Map Location": prop.map_location,
                "Agent Email": prop.agent_email, "Property Type": prop.property_type, "Image": prop.image,
                "Description": prop.description, "Price": prop.price, "Gallery": prop.gallery,
                "Year Built": prop.year_built, "Status": prop.status, "Agent Name": prop.agent_name,
                "Bathrooms": prop.bathrooms, "Agent Phone": prop.agent_phone, "Size": prop.size,
                "Floors": prop.floors, "ID": prop.id, "Owner": prop.owner,
                "Created Date": prop.created_date.strftime("%Y-%m-%d %H:%M:%S") if prop.created_date else "",
                "Updated Date": prop.updated_date.strftime("%Y-%m-%d %H:%M:%S") if prop.updated_date else ""
            })

        output.seek(0)
        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=updated_master_sheet.csv"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")

@app.get("/properties/{property_id}", response_model=schemas.PropertyResponse)
def get_property_by_id(property_id: int, db: Session = Depends(get_db)):
    property_obj = db.query(models.Property).filter(models.Property.id == property_id).first()
    if not property_obj:
        raise HTTPException(status_code=404, detail="Property not found")
        
    try:
        images = db.query(models.PropertyImage).filter(models.PropertyImage.property_id == property_id).all()
        image_ids = [img.id for img in images]
        
        response_dict = schemas.PropertyResponse.model_validate(property_obj).model_dump()
        response_dict["image_ids"] = image_ids
        return response_dict
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving property: {str(e)}")

@app.put("/properties/{property_id}/approve")
def approve_property(
    property_id: int, 
    db: Session = Depends(get_db), 
    current_user = Depends(get_current_user)
):
    if current_user.role != "agent":
        raise HTTPException(status_code=403, detail="Only agents can approve properties.")
    
    try:
        prop = db.query(models.Property).filter(models.Property.id == property_id).first()
        if not prop:
            raise HTTPException(status_code=404, detail="Property not found")
            
        prop.is_approved = True
        db.commit()
        return {"message": f"Property '{prop.title}' has been approved and is now live!"}
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="Database update failed")

# ==========================================
# 🖼️ IMAGES
# ==========================================
@app.post("/upload-image")
async def upload_image(
    image: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    validate_image_file(image)
    try:
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
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to upload image: {str(e)}")

@app.post("/property-images/download")
def download_property_images(
    request: schemas.ImageDownloadRequest,
    db: Session = Depends(get_db),
):
    if not request.image_ids:
        raise HTTPException(status_code=400, detail="image_ids required")

    try:
        zip_bytes = crud.get_images_as_zip(db, request.image_ids)
        if not zip_bytes:
            raise HTTPException(status_code=404, detail="Images not found or are empty")

        return StreamingResponse(
            io.BytesIO(zip_bytes),
            media_type="application/zip",
            headers={"Content-Disposition": "attachment; filename=property_images.zip"},
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate zip: {str(e)}")

# ==========================================
# 👤 USER & CUSTOMER API ROUTES
# ==========================================
def get_current_customer(current_user = Depends(get_current_user)):
    if getattr(current_user, "role", None) != "customer":
        raise HTTPException(status_code=403, detail="Customer access only")
    return current_user

@app.get("/my-properties", response_model=List[schemas.PropertyResponse])
def get_my_properties(
    skip: int = 0, 
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: schemas.UserResponse = Depends(get_current_user) 
):
    try:
        my_properties = db.query(models.Property).filter(
            models.Property.posted_by_id == current_user.id,
            models.Property.posted_by_role == current_user.role
        ).offset(skip).limit(limit).all()
        
        return my_properties
        
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to fetch your properties: {str(e)}"
        )

@app.get("/api/customer/profile", response_model=schemas.UserResponse)
def get_profile(user = Depends(get_current_customer)):
    return user

@app.put("/api/customer/profile")
def update_profile(data: schemas.ProfileUpdate, db: Session = Depends(get_db), user = Depends(get_current_user)):
    try:
        updated_user = crud.update_user_profile(db, user.id, user.role, data)
        if not updated_user:
            raise HTTPException(status_code=404, detail="User not found")
        updated_user.role = user.role
        return {"message": "Profile updated", "data": updated_user}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update profile: {str(e)}")

@app.post("/users/me/image")
async def upload_profile_image(
    image: UploadFile = File(...),
    db: Session = Depends(get_db),
    user = Depends(get_current_user) 
):
    validate_image_file(image)
    try:
        image_url = upload_file_to_s3(image, db, folder="profiles")
        
        # Determine the correct model based on role
        if user.role == "customer":
            db_user = db.query(models.Customer).filter(models.Customer.id == user.id).first()
        elif user.role == "agent":
            db_user = db.query(models.Agent).filter(models.Agent.id == user.id).first()
        elif user.role == "builder":
            db_user = db.query(models.Builder).filter(models.Builder.id == user.id).first()
            
        if not db_user:
            raise HTTPException(status_code=404, detail="User not found in database")
            
        db_user.profile_image_url = image_url
        db.commit()
        db.refresh(db_user)

        return {
            "message": "Profile photo uploaded successfully",
            "profile_image_url": image_url
        }
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="Database error saving profile image")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to upload profile image: {str(e)}")

@app.post("/api/customer/buy-requirements", response_model=schemas.BuyRequirementResponse)
def post_requirement(data: schemas.BuyRequirementCreate, db: Session = Depends(get_db), user = Depends(get_current_customer)):
    try:
        return crud.create_buy_requirement(db, data, user.id)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to create buy requirement")

@app.get("/api/customer/buy-requirements", response_model=list[schemas.BuyRequirementResponse])
def get_my_requirements(db: Session = Depends(get_db), user = Depends(get_current_customer)):
    try:
        return crud.get_customer_requirements(db, user.id)
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to retrieve requirements")

@app.delete("/api/customer/buy-requirements/{req_id}")
def delete_requirement(req_id: int, db: Session = Depends(get_db), user = Depends(get_current_customer)):
    try:
        success = crud.delete_buy_requirement(db, req_id, user.id)
        if not success:
            raise HTTPException(status_code=404, detail="Requirement not found or not owned by you")
        return {"message": "Requirement deleted"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to delete requirement")
    
# In main.py (Customer API Routes section)

@app.get("/api/customer/buy-requirements/{req_id}/matches", response_model=list[schemas.PropertyResponse])
def get_requirement_matches(req_id: int, db: Session = Depends(get_db), user = Depends(get_current_customer)):
    try:
        matches = crud.get_matching_properties_for_requirement(db, req_id, user.id)
        if matches is None:
            raise HTTPException(status_code=404, detail="Buy requirement not found or not owned by you")
        return matches
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to find matched properties: {str(e)}")

@app.post("/api/customer/favourites/{property_id}")
def add_favourite(property_id: int, db: Session = Depends(get_db), user = Depends(get_current_customer)):
    try:
        # Validate property actually exists!
        prop = db.query(models.Property).filter(models.Property.id == property_id).first()
        if not prop:
            raise HTTPException(status_code=404, detail="Property not found")
            
        crud.add_favourite(db, property_id, user.id)
        return {"message": "Property added to favourites"}
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to add favourite")

@app.get("/api/customer/favourites", response_model=list[schemas.PropertyResponse])
def get_favourites(db: Session = Depends(get_db), user = Depends(get_current_customer)):
    try:
        return crud.get_customer_favourites(db, user.id)
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to retrieve favourites")

@app.post("/api/customer/contact-owner")
def contact_owner(data: schemas.ContactOwner, db: Session = Depends(get_db), user = Depends(get_current_customer)):
    try:
        prop = db.query(models.Property).filter(models.Property.id == data.property_id).first()
        if not prop:
            raise HTTPException(status_code=404, detail="Cannot contact owner: Property not found")

        crud.create_enquiry(db, data, user.id)
        return {
            "message": "Enquiry sent successfully",
            "property_id": data.property_id,
            "customer_id": user.id
        }
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to save enquiry")