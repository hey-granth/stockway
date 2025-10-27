# Accounts API Documentation

## Authentication Endpoints

All authentication is handled through Supabase using phone number and OTP (One-Time Password).

### Base URL
```
/api/accounts/
```

---

## 1. Send OTP

Send an OTP to a phone number for authentication.

**Endpoint:** `POST /auth/send-otp/`

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

**Endpoint:** `POST /auth/verify-otp/`

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

**Endpoint:** `POST /auth/logout/`

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

## 4. Refresh Token

Get new access and refresh tokens using a refresh token.

**Endpoint:** `POST /auth/refresh/`

**Authentication:** None required

**Request Body:**
```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Response (200 OK):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "expires_in": 3600,
  "expires_at": 1698432000,
  "token_type": "bearer"
}
```

**Error Response (401 Unauthorized):**
```json
{
  "error": "Failed to refresh session: Invalid refresh token"
}
```

---

## 5. Get Current User

Get the currently authenticated user's details.

**Endpoint:** `GET /auth/me/`

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
2. Call `POST /auth/send-otp/` with phone number
3. User receives OTP via SMS
4. Call `POST /auth/verify-otp/` with phone number and OTP
5. Store `access_token` and `refresh_token` on client

### Authenticated Requests
Include the access token in the Authorization header:
```
Authorization: Bearer <access_token>
```

### Token Refresh
When the access token expires:
1. Call `POST /auth/refresh/` with the refresh token
2. Store new `access_token` and `refresh_token`

### Logout
Call `POST /auth/logout/` with the access token in the Authorization header

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

