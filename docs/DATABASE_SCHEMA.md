# Database Schema

Voice2Justice utilizes **SQLite3** for its relational database. The schema is auto-migrated on startup via `models/db.py`, utilizing parameterized queries to prevent SQL injection.

## Entity Relationship Diagram

```mermaid
erDiagram
    USERS ||--o{ COMPLAINTS : submits
    ADMINS
    
    USERS {
        int id PK
        string full_name
        string email UK
        string phone
        string password_hash
        string auth_provider "local/google"
        string google_id
        string profile_picture
        timestamp created_at
    }
    
    ADMINS {
        int id PK
        string username UK
        string password_hash
        string role
        timestamp created_at
    }
    
    COMPLAINTS {
        int id PK
        string complaint_number UK "VJ-YYYY-NNNN"
        string tracking_id UK "UUIDv4 (IDOR protection)"
        int user_id FK "nullable (for guests)"
        string user_type "Registered/Guest"
        string guest_name
        string guest_email
        string guest_phone
        string text
        string type "crpc_crime/civic_issue"
        string category
        float confidence_score
        string location
        string status "Received/Investigating/Closed"
        string priority "High/Medium/Low"
        string department
        string sla
        string summary
        string sections
        string submitted_to
        float fraud_score
        string fraud_status
        string review_status "Pending/Genuine/Fake"
        string verification_status "Verified/Unverified"
        string submitted_ip
        timestamp created_at
        timestamp updated_at
    }
```

## Tables & Indexing

### 1. `complaints`
The core table storing all grievance data.
- **Indexes**: `idx_complaint_number` (UNIQUE), `idx_tracking_id` (UNIQUE), `idx_status`, `idx_category`, `idx_created_at`, `idx_user_id`.
- **Fraud Tracking**: Stores `submitted_ip`, `fraud_score`, `fraud_status`, and admin `review_status` without actively blocking the user (to avoid rejecting legitimate urgent grievances).
- **Timestamps**: Uses `updated_at` for caching logic in PDF generation.

### 2. `users`
Stores citizen credentials and OAuth linkage.
- **OAuth Linkage**: `auth_provider` defaults to `local`. If authenticated via Google, stores `google_id` and `profile_picture`.
- **Constraint**: `email` is UNIQUE.

### 3. `admins`
Stores backend dashboard users.
- **Default Seeding**: `models/db.py` automatically injects a `super_admin` (`admin` / `admin123`) if the table is empty upon initialization.

## Auto-Migration Strategy

Instead of using heavy tools like Alembic, the system uses a robust, lightweight try/except migration script for SQLite.

```python
migrations = [
    "ALTER TABLE complaints ADD COLUMN user_id INTEGER",
    "ALTER TABLE complaints ADD COLUMN fraud_score REAL DEFAULT 0.0"
]
for migration in migrations:
    try:
        cursor.execute(migration)
    except sqlite3.OperationalError:
        pass  # Column already exists
```
This ensures zero-downtime schema evolution when deploying to ephemeral or new environments.
