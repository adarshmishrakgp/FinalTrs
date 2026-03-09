=========================================================
          PROPERTY PORTAL API DOCUMENTATION
=========================================================

---------------------------------------------------------
1. AUTHENTICATION & USERS
---------------------------------------------------------
POST /login
- Purpose: Logs in a user (Customer, Agent, or Builder) and returns a JWT access token.
- Input: Form-Data (username/email, password)
- Access: Public

GET /users/me
- Purpose: Returns the profile information of the currently logged-in user.
- Access: Requires valid JWT Token (Any role)

---------------------------------------------------------
2. REGISTRATION
---------------------------------------------------------
POST /register/customer
- Purpose: Creates a new Customer account.
- Input: Form-Data (full_name, email, phone, password, city, optional profile_image file)
- Access: Public

POST /register/agent
- Purpose: Creates a new Agent account.
- Input: Form-Data (full_name, email, phone, password, rera_number, agency_name, city, optional profile_image file)
- Access: Public

POST /register/builder
- Purpose: Creates a new Builder account.
- Input: Form-Data (company_name, contact_person, email, phone, password, rera_number, city, optional profile_image file)
- Access: Public

---------------------------------------------------------
3. PROPERTIES (CORE FEATURES)
---------------------------------------------------------
POST /createproperty
- Purpose: Creates a new property listing. If created by Agent/Builder, it is automatically approved. If created by a Customer, it goes into the pending queue.
- Access: Requires valid JWT Token (Any role)

GET /properties
- Purpose: Fetches a list of all APPROVED properties for the public feed.
- Access: Public

GET /properties/search
- Purpose: Searches approved properties using filters (title, type, min/max price, bedrooms, status).
- Access: Public

GET /properties/pending
- Purpose: Fetches a list of UNAPPROVED properties waiting for review.
- Access: Agent Only

POST /properties/import
- Purpose: Uploads a Master Sheet (CSV) and imports properties directly into the database.
- Input: CSV File
- Access: Public (Consider restricting to Admin/Agent in the future)

GET /properties/export
- Purpose: Downloads the entire property database as a Master Sheet (CSV).
- Access: Public (Consider restricting to Admin/Agent in the future)

GET /properties/{property_id}
- Purpose: Fetches the full details and images of a single specific property.
- Access: Public

PUT /properties/{property_id}/approve
- Purpose: Approves a pending property, making it visible on the public feed.
- Access: Agent Only

---------------------------------------------------------
4. IMAGES & MEDIA
---------------------------------------------------------
POST /upload-image
- Purpose: Uploads a property image to AWS S3 and saves the URL to the database.
- Input: Image File
- Access: Public / Authenticated Users

POST /property-images/download
- Purpose: Downloads property images as a ZIP file. (Note: Recommend removing this if using S3 public URLs).
- Access: Public

---------------------------------------------------------
5. CUSTOMER DASHBOARD & ACTIONS
---------------------------------------------------------
GET /api/customer/profile
- Purpose: Fetches the logged-in customer's profile details.
- Access: Customer Only

PUT /api/customer/profile
- Purpose: Updates the customer's profile text data (name, phone, city).
- Access: Customer Only

POST /api/customer/profile/image
- Purpose: Uploads and sets the customer's profile picture via AWS S3.
- Input: Image File
- Access: Customer Only

POST /api/customer/buy-requirements
- Purpose: Submits a new property buying requirement for the customer.
- Access: Customer Only

GET /api/customer/buy-requirements
- Purpose: Fetches all buying requirements posted by the logged-in customer.
- Access: Customer Only

DELETE /api/customer/buy-requirements/{req_id}
- Purpose: Deletes a specific buying requirement.
- Access: Customer Only

POST /api/customer/favourites/{property_id}
- Purpose: Adds a specific property to the customer's favourites list.
- Access: Customer Only

GET /api/customer/favourites
- Purpose: Fetches all properties the customer has favorited.
- Access: Customer Only

POST /api/customer/contact-owner
- Purpose: Sends a message/inquiry about a specific property to the system.
- Access: Customer Only

=========================================================