# API Documentation

## Authentication Protocols
Voice2Justice uses dual authentication mechanisms:
1. **Admin APIs**: Secured via standard session cookies (`session['admin_id']`). Endpoints return `401 Unauthorized` if unauthenticated.
2. **Citizen APIs**: Secured via standard session cookies (`session['user_id']`). Endpoints return `401 Unauthorized` if unauthenticated.
3. **Public APIs**: Endpoints like `/api/process` do not strictly require authentication but track IP addresses for rate limiting and fraud scoring.

## Rate Limiting
Global Limits: `200 per day`, `50 per hour` per IP.
*Specific endpoints have stricter limits noted below.*

---

## 1. Complaint Processing (`routes/complaints.py`)

### `POST /api/process`
Submits a complaint text to the ML classifier and stores it.
- **Auth Required**: No
- **Rate Limit**: 5 per minute
- **Body**:
```json
{
  "text": "Someone stole my bike from the park.",
  "location": "Central Park",
  "guest_name": "John Doe",  // Required if not logged in
  "guest_email": "john@example.com", // Required if not logged in
  "guest_phone": "1234567890" // Required if not logged in
}
```
- **Success Response (200)**:
```json
{
  "status": "success",
  "type": "crpc_crime",
  "complaint_id": 12,
  "tracking_id": "550e8400-e29b-41d4-a716-446655440000",
  "complaint_number": "VJ-2026-0012",
  "steps": ["Initializing...", "Parsing..."],
  "html": "<div class='result-card'>...</div>"
}
```

### `GET /api/track/<tracking_id>`
Fetches the current status and metadata of a complaint using its secure UUIDv4.
- **Auth Required**: No
- **Success Response (200)**: Returns full complaint dict.

### `GET /api/complaints`
Lists all complaints in the system.
- **Auth Required**: Admin

---

## 2. Dashboard Analytics (`routes/dashboard.py`)
*All endpoints in this section require Admin Auth.*

### `GET /api/dashboard/stats`
Returns top-level aggregates.
```json
{ "status": "success", "data": { "total": 150, "open": 45, "closed": 105 } }
```

### `GET /api/dashboard/trends`
Returns monthly volume trends and status distributions for Chart.js.

### `GET /api/dashboard/recent`
Returns the 20 most recent complaints including joined user data.

### `POST /api/admin/review`
Updates the admin review status of a flagged complaint.
- **Body**: `{"complaint_id": 12, "review_status": "Genuine"}`
- **Success Response (200)**: `{"status": "success"}`

---

## 3. Reports & Exports (`routes/reports.py`)

### `GET /report/<tracking_id>`
Renders the printable HTML version of the official report (FIR/Civic Ticket).

### `GET /report/<tracking_id>/pdf`
Triggers server-side ReportLab PDF generation and forces a file download. Cached automatically based on `updated_at`.

---

## 4. Authentication (`routes/auth.py`, `routes/user_auth.py`)

### `POST /login` (Admin)
- **Body** (Form Data): `username`, `password`
- **Response**: `302 Redirect` to dashboard on success.

### `POST /user/register` (Citizen)
- **Rate Limit**: 5 per minute
- **Body** (Form Data): `full_name`, `email`, `phone`, `password`

### `GET /user/login/google` (Citizen)
Initiates OAuth 2.0 flow with Google.

### `POST /api/update-status` (Admin)
- **Body**: `{"complaint_id": 12, "status": "Investigating"}`
- **Valid Statuses**: `Received`, `Under Review`, `Investigating`, `In Progress`, `Resolved`, `Closed`, `Rejected`
