# Accounts App API Documentation

Purpose
- Phone OTP authentication and Shopkeeper (Customer) profile management.

Base URL
- /auth/

Authentication
- OTP endpoints: no auth required
- Profile endpoints: Token auth required
  - Header: Authorization: Token <token>

Endpoints

1) Request OTP
- POST /auth/request-otp/
- Body:
  {
    "phone_number": "+919876543210"
  }
- 200 OK:
  { "message": "OTP sent successfully" }
- 400/500: { "error": "..." }

2) Verify OTP (Login)
- POST /auth/verify-otp/
- Body:
  {
    "phone_number": "+919876543210",
    "otp": "123456"
  }
- 200 OK:
  {
    "message": "OTP verified successfully",
    "token": "<drf_token>",
    "user": {
      "id": 1,
      "phone_number": "+919876543210",
      "role": "SHOPKEEPER",
      "is_verified": true,
      "first_name": "",
      "last_name": ""
    }
  }
- Notes: Save token and send with Authorization header for subsequent calls.

3) Shopkeeper Profile (simple)
- URL: /auth/shopkeeper/profile/
- Methods: GET, POST, PUT
- Auth: Token, role SHOPKEEPER
- GET 200:
  {
    "id": 10,
    "user_phone": "+919876543210",
    "user_email": null,
    "shop_name": "ABC Kirana",
    "address": "12 Market Rd",
    "latitude": 28.61,
    "longitude": 77.21,
    "gst_number": "",
    "license_number": "",
    "onboarding_completed": false,
    "created_at": "2025-10-23T10:00:00Z",
    "updated_at": "2025-10-23T10:00:00Z"
  }
- POST 201: same shape as GET (creates profile for current user)
- PUT 200: full update
- 404 when profile not created yet (for GET/PUT)

4) Customer Profile (full onboarding helper)
- URL: /auth/customers/profile/
- Methods: GET, POST, PATCH, PUT
- Auth: Token, role SHOPKEEPER
- GET 200: same schema as ShopkeeperProfile above
- POST 201: create if none exists; 409 if already exists
- PATCH 200: partial update; automatically sets onboarding_completed=true when
  shop_name, address, latitude, longitude, and at least one of gst_number or license_number are present
- PUT 200: full replace
- Common 404:
  {
    "error": "Profile not found. Please create your profile first.",
    "detail": "Use POST method to create a new profile."
  }

Error Responses
- 401 Unauthorized: { "detail": "Authentication credentials were not provided." }
- 403 Forbidden: { "detail": "You do not have permission to perform this action." }
- 400 Bad Request: { "error": "..." } or serializer field errors

Notes
- All datetimes are ISO 8601 UTC strings.
- Latitude ∈ [-90, 90], Longitude ∈ [-180, 180].
- Use /api/warehouses/nearby/ and /shopkeeper/warehouses/nearby/ for proximity queries after setting profile location.
