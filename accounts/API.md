# Accounts API Documentation

## Authentication Endpoints

All authentication is handled through Supabase using email and OTP (One-Time Password).

### Base URL
```
/api/auth/
```

### Notes
- Authentication tokens are managed by Supabase client SDK
- Token refresh is handled automatically by the Supabase client on the frontend
- No JWT verification is needed on the backend - Supabase handles all token validation

---

## 1. Send OTP

Send an OTP to an email address for authentication.

**Endpoint:** `POST /api/auth/send-otp/`

**Authentication:** None required

**Headers:**
```
Content-Type: application/json
```

**Request Body:**
```json
{
  "email": "user@example.com"
}
```

**Response (200 OK):**
```json
{
  "success": true,
  "message": "OTP sent successfully to your email",
  "email": "user@example.com"
}
```

**Error Response (400 Bad Request):**
```json
{
  "error": {
    "email": ["Enter a valid email address."]
  }
}
```

---

## 2. Verify OTP

Verify the OTP and get authentication tokens.
**Headers:**
```
Content-Type: application/json
```


**Endpoint:** `POST /api/auth/verify-otp/`

**Authentication:** None required

**Request Body:**
```json
{
  "email": "user@example.com",
  "otp": "123456"
}
```

**Response (200 OK):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "expires_in": 36000,
  "expires_at": 1698432000,
  "token_type": "bearer",
  "user": {
    "id": 1,
    "phone_number": null,
**Error Response (400 Bad Request):**
```json
{
  "error": {
    "otp": ["OTP must contain only digits"]
  }
}
```

    "email": "user@example.com",
    "full_name": "",
    "role": "SHOPKEEPER",
    "is_active": true,
    "date_joined": "2025-10-30T10:30:00Z",
    "last_login": null
  }
**Error Response (415 Unsupported Media Type):**
```json
{
  "detail": "Unsupported media type \"text/plain\" in request."
}
```
*Note: This error occurs when the `Content-Type: application/json` header is missing from the request.*

}
```

**Error Response (401 Unauthorized):**
```json
{
  "error": "Invalid or expired OTP"
}
```

---

Content-Type: application/json
## 3. Logout

Invalidate the current session.

**Endpoint:** `POST /api/auth/logout/`

**Authentication:** Required (Bearer token)

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response (200 OK):**
```json
{
  "success": true,
  "message": "Logged out successfully"
}
```

---

## 4. Get Current User

Get the currently authenticated user's details.

**Endpoint:** `GET /api/auth/me/`

**Authentication:** Required (Bearer token)

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response (200 OK):**
```json
{
  "id": 1,
  "phone_number": "+1234567890",
  "email": null,
  "full_name": "",
  "role": "SHOPKEEPER",
  "is_active": true,
  "date_joined": "2025-10-27T10:30:00Z",
  "last_login": "2025-10-27T11:00:00Z"
}
```

---

## Authentication Flow

### Initial Login
1. User provides email address
2. Call `POST /api/auth/send-otp/` with email
3. User receives OTP via email
4. Call `POST /api/auth/verify-otp/` with email and OTP
5. Store `access_token` and `refresh_token` on client (managed by Supabase SDK)

### Authenticated Requests
Include the access token in the Authorization header:
```
Authorization: Bearer <access_token>
```

### Token Refresh
- Token refresh is handled automatically by the Supabase client SDK
- The SDK will automatically refresh expired tokens before making requests
- No manual token refresh endpoint is needed on the backend

### Logout
Call `POST /api/auth/logout/` with the access token in the Authorization header

---

## Email Format

All emails must be valid email addresses in standard format.

Examples:
- `user@example.com`
- `john.doe@company.co.uk`
- `contact+test@domain.org`

---

## User Roles

- `SHOPKEEPER` - Shop owner (default)
- `RIDER` - Delivery rider
- `WAREHOUSE_MANAGER` - Warehouse manager
- `ADMIN` - System administrator

---

## Technical Implementation

### User Model Structure
- **USERNAME_FIELD**: `phone_number` (not `username`)
- **Primary Identifier**: Phone number in E.164 format
- **No Username Field**: The custom User model does not have a `username` field
- **Authentication Method**: Phone-based OTP via Supabase
- **User String Representation**: Returns `phone_number`
- **Available Methods**:
  - `get_full_name()` - Returns `full_name` or `phone_number` if name not set
  - `get_short_name()` - Returns `phone_number`

### ShopkeeperProfile Model
- **Relationship**: OneToOne with User model
- **Location Field**: PostGIS PointField for geographic coordinates
- **Key Fields**: `shop_name`, `shop_address`, `location`, `gst_number`, `is_verified`
- **Table Name**: `shopkeeper_profiles`

### Database Schema
- **Users Table**: `users` (custom table name, not `auth_user`)
- **Location Fields**: Use PostGIS geography type (SRID 4326)
- **Indexes**: Created on `phone_number` and `supabase_uid` for performance


