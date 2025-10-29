# Accounts API Documentation

## Authentication Endpoints

All authentication is handled through Supabase using phone number and OTP (One-Time Password).

### Base URL
```
/api/accounts/
```

### Notes
- Authentication tokens are managed by Supabase client SDK
- Token refresh is handled automatically by the Supabase client on the frontend
- No JWT verification is needed on the backend - Supabase handles all token validation

---

## 1. Send OTP

Send an OTP to a phone number for authentication.

**Endpoint:** `POST /api/accounts/send-otp/`

**Authentication:** None required

**Request Body:**
```json
{
  "phone_number": "+1234567890"
}
```

**Response (200 OK):**
```json
{
  "success": true,
  "message": "OTP sent successfully to your phone",
  "phone_number": "+1234567890"
}
```

**Error Response (400 Bad Request):**
```json
{
  "error": {
    "phone_number": ["Phone number must be in E.164 format (e.g., +1234567890)"]
  }
}
```

---

## 2. Verify OTP

Verify the OTP and get authentication tokens.

**Endpoint:** `POST /api/accounts/verify-otp/`

**Authentication:** None required

**Request Body:**
```json
{
  "phone_number": "+1234567890",
  "otp": "123456"
}
```

**Response (200 OK):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "expires_in": 3600,
  "expires_at": 1698432000,
  "token_type": "bearer",
  "user": {
    "id": 1,
    "phone_number": "+1234567890",
    "email": null,
    "full_name": "",
    "role": "SHOPKEEPER",
    "is_active": true,
    "date_joined": "2025-10-27T10:30:00Z",
    "last_login": null
  }
}
```

**Error Response (401 Unauthorized):**
```json
{
  "error": "Invalid or expired OTP"
}
```

---

## 3. Logout

Invalidate the current session.

**Endpoint:** `POST /api/accounts/logout/`

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

**Endpoint:** `GET /api/accounts/me/`

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
1. User provides phone number
2. Call `POST /api/accounts/send-otp/` with phone number
3. User receives OTP via SMS
4. Call `POST /api/accounts/verify-otp/` with phone number and OTP
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
Call `POST /api/accounts/logout/` with the access token in the Authorization header

---

## Phone Number Format

All phone numbers must be in **E.164 format**:
- Start with `+`
- Country code + number
- No spaces or special characters

Examples:
- US: `+12025551234`
- India: `+919876543210`
- UK: `+447700900123`

---

## User Roles

- `SHOPKEEPER` - Shop owner (default)
- `RIDER` - Delivery rider
- `WAREHOUSE_MANAGER` - Warehouse manager
- `ADMIN` - System administrator

