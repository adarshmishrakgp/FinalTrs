======================================================
🏠 REAL ESTATE API DOCUMENTATION FOR FRONTEND
======================================================
Base URL: http://localhost:8000  (Update for production)

GLOBAL HEADERS:
- For protected routes, include: 
  Authorization: Bearer <your_access_token>

------------------------------------------------------
1. 🔐 AUTHENTICATION & REGISTRATION
------------------------------------------------------

A. Register Customer
- Endpoint: POST /register/customer
- Auth Required: No
- Body (JSON): 
  {
    "full_name": "John Doe",
    "email": "john@example.com",
    "phone": "1234567890",
    "password": "password123",
    "city": "New York"
  }

B. Register Agent
- Endpoint: POST /register/agent
- Auth Required: No
- Body (JSON): Same as above, but add "rera_number" and "agency_name"

C. Register Builder
- Endpoint: POST /register/builder
- Auth Required: No
- Body (JSON): Uses "company_name", "contact_person", "email", "phone", "password", "rera_number", "city"

D. Login (Get Token)
- Endpoint: POST /login
- Auth Required: No
- Content-Type: application/x-www-form-urlencoded (Form Data)
- Body (Form Data):
  - username: <user_email>
  - password: <user_password>
- Response: 
  {
    "access_token": "eyJhbGci...",
    "token_type": "bearer",
    "role": "customer|agent|builder"
  }

------------------------------------------------------
2. 🏢 PROPERTIES (Standard API)
------------------------------------------------------

A. Get All Properties (Paginated)
- Endpoint: GET /properties
- Auth Required: No
- Query Params:
  - skip (int, default: 0)
  - limit (int, default: 10)
- Response: Array of property objects with attached `image_ids`.

B. Search & Filter Properties
- Endpoint: GET /properties/search
- Auth Required: No
- Query Params (All Optional):
  - city (string)
  - property_type (string - e.g., "APARTMENT", "VILLA")
  - min_price (float)
  - max_price (float)
  - bedrooms (int)
  - skip (int), limit (int)
- Response: Array of filtered property objects.

C. Get Single Property Details
- Endpoint: GET /properties/{property_id}
- Auth Required: No
- Path Param: property_id (int)
- Response: Single property object.

D. Create Property
- Endpoint: POST /createproperty
- Auth Required: YES (Role: Agent or Builder only)
- Body (JSON): 
  {
    "title": "Luxury Villa",
    "property_type": "VILLA",
    "city": "Los Angeles",
    "expected_price": 500000,
    ... (other fields based on PropertyCreate schema),
    "image_ids": [1, 2, 3]  // IDs returned from the image upload endpoint
  }
- Response: {"property_id": 1, "message": "Property created successfully..."}

------------------------------------------------------
3. 🖼️ IMAGES & MEDIA
------------------------------------------------------

A. Upload Single Image to S3
- Endpoint: POST /upload-image
- Auth Required: No (or Yes, if you choose to secure it)
- Content-Type: multipart/form-data
- Body (Form Data):
  - image: <File object>
- Response:
  {
    "message": "Image uploaded successfully",
    "image_url": "https://bucket.s3.amazonaws.com/..."
  }

B. Download Multiple Images as ZIP
- Endpoint: POST /property-images/download
- Auth Required: No
- Body (JSON):
  {
    "image_ids": [1, 2, 3]
  }
- Response: File download (application/zip)

------------------------------------------------------
4. 📋 LEGACY / CURRENT PROPERTIES (If still in use)
------------------------------------------------------

A. Get Current Properties
- Endpoint: GET /current-properties
- Query Params: skip, limit

B. Create Current Property
- Endpoint: POST /current-properties/create
- Body (JSON): Matches CurrentPropertyCreate schema.