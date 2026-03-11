=========================================================
PROPERTY PORTAL API DOCUMENTATION

    AUTHENTICATION & USERS

POST /login

    Purpose: Logs in a user (Customer, Agent, or Builder) and returns a JWT access token.

    Input: Form-Data (username/email, password)

    Access: Public

GET /users/me

    Purpose: Returns the profile information of the currently logged-in user.

    Access: Requires valid JWT Token (Any role)

POST /users/me/image

    Purpose: Uploads and sets the profile picture for the logged-in user via AWS S3.

    Input: Image File (multipart/form-data)

    Access: Requires valid JWT Token (Customer, Agent, or Builder)

    REGISTRATION

POST /register/customer

    Purpose: Creates a new Customer account.

    Input: Form-Data (full_name, email, phone, password, city, company_name, optional profile_image file)

    Access: Public

POST /register/agent

    Purpose: Creates a new Agent account.

    Input: Form-Data (full_name, email, phone, password, rera_number, agency_name, city, optional profile_image file)

    Access: Public

POST /register/builder

    Purpose: Creates a new Builder account.

    Input: Form-Data (company_name, contact_person, email, phone, password, rera_number, city, optional profile_image file)

    Access: Public

    PROPERTIES (CORE FEATURES)

POST /createproperty

    Purpose: Creates a new highly-detailed property listing. Automatically links the property to the logged-in user via posted_by_id.

    Access: Requires valid JWT Token (Any role. Agents/Builders auto-approve; Customers go to pending).

GET /properties

    Purpose: Fetches a list of all APPROVED properties for the public feed, complete with image arrays.

    Access: Public

GET /my-properties

    Purpose: Fetches all properties specifically posted by the currently logged-in user.

    Access: Requires valid JWT Token (Any role)

GET /properties/search

    Purpose: Searches approved properties using updated filters (title/city/address, property_type, min/max expected_price, bedrooms, possession_status).

    Access: Public

GET /properties/pending

    Purpose: Fetches a list of UNAPPROVED properties waiting for review.

    Access: Agent Only

POST /properties/import

    Purpose: Uploads a Master Sheet (CSV) and imports properties directly into the new database schema.

    Input: CSV File

    Access: Public

GET /properties/export

    Purpose: Downloads the entire property database as a Master Sheet (CSV).

    Access: Public

GET /properties/{property_id}

    Purpose: Fetches the full details and images of a single specific property.

    Access: Public

PUT /properties/{property_id}/approve

    Purpose: Approves a pending property, making it visible on the public feed.

    Access: Agent Only

    IMAGES & MEDIA

POST /upload-image

    Purpose: Uploads a property image to AWS S3 and saves the URL to the database.

    Input: Image File

    Access: Public / Authenticated Users

POST /property-images/download

    Purpose: Downloads requested property images bundled as a ZIP file.

    Access: Public

    CUSTOMER DASHBOARD & ACTIONS

GET /api/customer/profile

    Purpose: Fetches the logged-in customer's profile details.

    Access: Customer Only

PUT /api/customer/profile

    Purpose: Updates the customer's profile text data (name, phone, city, company_name).

    Access: Customer Only

POST /api/customer/buy-requirements

    Purpose: Submits a new property buying requirement for the customer (using expected_price and carpet_area).

    Access: Customer Only

GET /api/customer/buy-requirements

    Purpose: Fetches all buying requirements posted by the logged-in customer.

    Access: Customer Only

DELETE /api/customer/buy-requirements/{req_id}

    Purpose: Deletes a specific buying requirement.

    Access: Customer Only

GET /api/customer/buy-requirements/{req_id}/matches

    Purpose: Cross-references a specific buy requirement with all approved properties and returns a list of perfect matches based on price, area, city, and type.

    Access: Customer Only

POST /api/customer/favourites/{property_id}

    Purpose: Adds a specific property to the customer's favourites list.

    Access: Customer Only

GET /api/customer/favourites

    Purpose: Fetches all properties the customer has favorited.

    Access: Customer Only

POST /api/customer/contact-owner

    Purpose: Sends a message/inquiry about a specific property to the system.

    Access: Customer Only

=========================================================