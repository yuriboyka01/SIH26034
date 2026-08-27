# API Reference

Base URL: `http://localhost:8000`

Interactive docs: `http://localhost:8000/docs`

## Authentication

### POST /api/auth/register

Create a new user account.

**Request:**
```json
{
  "name": "John Doe",
  "email": "john@example.com",
  "password": "securepassword"
}
```

**Response (201):**
```json
{
  "access_token": "eyJhbG...",
  "token_type": "bearer",
  "user": {
    "id": "uuid",
    "name": "John Doe",
    "email": "john@example.com",
    "role": "INSPECTOR",
    "created_at": "2026-08-26T12:00:00Z"
  }
}
```

### POST /api/auth/login

Authenticate and receive JWT token.

**Request:**
```json
{
  "email": "john@example.com",
  "password": "securepassword"
}
```

**Response (200):** Same as register response.

### GET /api/auth/me

Get current user profile. Requires Bearer token.

**Response (200):**
```json
{
  "id": "uuid",
  "name": "John Doe",
  "email": "john@example.com",
  "role": "INSPECTOR",
  "created_at": "2026-08-26T12:00:00Z"
}
```

---

## Inspections

All inspection endpoints require Bearer token authentication.

### POST /api/inspections

Create a new inspection.

**Request:**
```json
{
  "product_name": "Example Rice",
  "brand": "Example Brand"
}
```

**Response (201):**
```json
{
  "id": "uuid",
  "inspection_number": "INS-20260826-A1B2",
  "product_name": "Example Rice",
  "brand": "Example Brand",
  "status": "CREATED",
  "created_by": "user-uuid",
  "created_at": "2026-08-26T12:00:00Z",
  "updated_at": "2026-08-26T12:00:00Z",
  "images": []
}
```

### GET /api/inspections

List all inspections for the current user.

**Response (200):**
```json
[
  {
    "id": "uuid",
    "inspection_number": "INS-20260826-A1B2",
    "product_name": "Example Rice",
    "brand": "Example Brand",
    "status": "CREATED",
    "created_at": "2026-08-26T12:00:00Z",
    "image_count": 0
  }
]
```

### GET /api/inspections/{inspection_id}

Get inspection details with images.

**Response (200):** Same as create response, with populated `images` array.

---

## Images

### POST /api/inspections/{inspection_id}/images

Upload an image to an inspection. Uses multipart/form-data.

**Form fields:**
- `file` (required): Image file (JPG, PNG, WEBP, max 10MB)
- `image_type` (optional): FRONT, BACK, SIDE, OTHER (default: OTHER)

**Response (201):**
```json
{
  "id": "uuid",
  "original_filename": "packet.jpg",
  "stored_filename": "abc123.jpg",
  "mime_type": "image/jpeg",
  "file_size": 123456,
  "image_type": "FRONT",
  "url": "/api/images/abc123.jpg",
  "created_at": "2026-08-26T12:00:00Z"
}
```

### DELETE /api/inspections/{inspection_id}/images/{image_id}

Delete an image. Returns 204 No Content.

### GET /api/images/{stored_filename}

Serve the stored image file. No authentication required.

---

## Dashboard

### GET /api/dashboard/stats

Get inspection count statistics.

**Response (200):**
```json
{
  "total": 10,
  "created": 3,
  "images_uploaded": 4,
  "processing": 1,
  "completed": 2,
  "needs_review": 0
}
```

---

## System

### GET /api/health

Health check endpoint (no auth required).

**Response (200):**
```json
{
  "status": "healthy",
  "version": "1.0.0-phase1"
}
```

---

## Error Format

All errors follow this format:

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable message."
  }
}
```

### Common Error Codes

| Code | HTTP | Description |
|------|------|-------------|
| INVALID_CREDENTIALS | 401 | Wrong email or password |
| INVALID_TOKEN | 401 | Expired or malformed JWT |
| EMAIL_ALREADY_EXISTS | 400 | Duplicate registration |
| INSPECTION_NOT_FOUND | 404 | Inspection doesn't exist |
| IMAGE_NOT_FOUND | 404 | Image doesn't exist |
| IMAGE_TYPE_NOT_SUPPORTED | 400 | Invalid file format |
| IMAGE_TOO_LARGE | 400 | File exceeds size limit |
| INTERNAL_ERROR | 500 | Server error (no details exposed) |
