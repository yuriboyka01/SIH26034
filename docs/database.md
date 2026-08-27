# Database Schema

## Entity Relationship

```
┌─────────┐     ┌──────────────┐     ┌──────────────────┐
│  users  │ 1─N │ inspections  │ 1─N │ inspection_images │
└─────────┘     └──────────────┘     └──────────────────┘
```

## Tables

### users

| Column | Type | Constraints | Description |
|--------|------|------------|-------------|
| id | UUID | PK | User identifier |
| name | VARCHAR(255) | NOT NULL | Full name |
| email | VARCHAR(255) | UNIQUE, NOT NULL | Email address |
| password_hash | VARCHAR(255) | NOT NULL | bcrypt hash |
| role | ENUM(UserRole) | NOT NULL, DEFAULT 'INSPECTOR' | User role |
| created_at | TIMESTAMPTZ | DEFAULT now() | Creation timestamp |
| updated_at | TIMESTAMPTZ | DEFAULT now() | Last update timestamp |

**Indexes:** `ix_users_email` on `email`

### inspections

| Column | Type | Constraints | Description |
|--------|------|------------|-------------|
| id | UUID | PK | Inspection identifier |
| inspection_number | VARCHAR(50) | UNIQUE, NOT NULL | Auto-generated (INS-YYYYMMDD-XXXX) |
| created_by | UUID | FK → users.id, CASCADE, NOT NULL | Creator |
| product_name | VARCHAR(500) | NOT NULL | Product name |
| brand | VARCHAR(255) | NOT NULL | Brand name |
| status | ENUM(InspectionStatus) | NOT NULL, DEFAULT 'CREATED' | Lifecycle status |
| created_at | TIMESTAMPTZ | DEFAULT now() | Creation timestamp |
| updated_at | TIMESTAMPTZ | DEFAULT now() | Last update timestamp |

**Indexes:** `ix_inspections_inspection_number` on `inspection_number`

### inspection_images

| Column | Type | Constraints | Description |
|--------|------|------------|-------------|
| id | UUID | PK | Image identifier |
| inspection_id | UUID | FK → inspections.id, CASCADE, NOT NULL | Parent inspection |
| original_filename | VARCHAR(500) | NOT NULL | User's original filename |
| stored_filename | VARCHAR(255) | UNIQUE, NOT NULL | Generated storage filename |
| file_path | VARCHAR(1000) | NOT NULL | Storage path/key |
| mime_type | VARCHAR(100) | NOT NULL | MIME type (image/jpeg, etc.) |
| file_size | INTEGER | NOT NULL | File size in bytes |
| image_type | ENUM(ImageType) | NOT NULL, DEFAULT 'OTHER' | Image category |
| created_at | TIMESTAMPTZ | DEFAULT now() | Upload timestamp |

**Indexes:** `ix_inspection_images_inspection_id` on `inspection_id`

## Enums

### UserRole
- `ADMIN`
- `INSPECTOR`

### InspectionStatus
- `CREATED` — Initial state
- `IMAGES_UPLOADED` — At least one image attached
- `PROCESSING` — AI analysis in progress (future)
- `COMPLETED` — Analysis complete (future)
- `NEEDS_REVIEW` — Issues found, needs manual review (future)

### ImageType
- `FRONT` — Front label
- `BACK` — Back label
- `SIDE` — Side label
- `OTHER` — Other view

## Cascade Behavior

- Deleting a **user** cascades to all their inspections and images
- Deleting an **inspection** cascades to all its images
