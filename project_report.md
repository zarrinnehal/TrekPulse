# PROJECT REPORT: TREKSYNC (Trekking Management Application)

## 1. Student Details
* **Student Name**: Zarrin Nehal
* **Roll Number**: 22f2000003
* **Course/Department**: DS Study, IITM
* **Email Address**: 22f2000003@ds.study.iitm.ac.in
* **Submission Date**: July 13, 2026

---

## 2. Project Details & Approach

### Question Statement
Develop a multi-role Trekking Management Application featuring distinct functionalities for **Administrators**, **Trek Staff Guides**, and **Trekkers (Users)**. The system must support secure authentication, slot tracking, status changes (Pending, Approved, Open, Started, Closed, Completed), historical booking logs, data searches/filters, and data visualization.

### Approach & Architecture
We built the application on the **Flask Web Framework** adhering to professional engineering patterns:
1. **Application Factory Pattern (`app/__init__.py`)**: Decouples configuration, database bindings, and extension registrations, facilitating clean testing environments.
2. **Role-Based Controller Routing (Blueprints)**: Separate blueprints isolate concerns for `/auth`, `/admin`, `/staff`, `/trekker`, `/api`, and `/` (main index).
3. **Preventing Overbooking (Transaction Isolation & Mutex Checks)**:
   - Bookings are guarded by database transactions. Before a booking record is written, the controller queries the exact trek record using `db.session.get()`.
   - Checks if `available_slots > 0` and `status == 'Open'`.
   - Adjusts slots and commits atomically. Any failure triggers a database rollback and flashes an warning, preventing race conditions.
4. **Premium Light UI Layout**: Styled using a crisp **Light Theme** built with Bootstrap 5. Main content renders on a clean white/off-white canvas (`#f8fafc` and `#ffffff`) accented with a beautiful emerald green (`#059669`) primary color scheme.

---

## 3. AI / LLM Declaration
This application and its automated verification suites were pair programmed using **Google Antigravity**, an agentic AI coding assistant. The AI assisted with structuring the modular blueprint components, configuring the SQLAlchemy ORM models, styling the custom CSS attributes, and setting up the 21 pytest automated cases.

---

## 4. Frameworks & Libraries Used
* **Core Language**: Python 3.12
* **Backend Framework**: Flask (Jinja2 templating, WSGI server)
* **Authentication**: Flask-Login (session-based cookies, role decorators)
* **Database & ORM**: SQLite & Flask-SQLAlchemy
* **Form Verification**: Flask-WTF & WTForms (CSRF protection, email validation)
* **Visuals & Charts**: Chart.js (interactive frontend canvas charts configured for light-theme backgrounds)
* **CSS Framework**: Bootstrap 5 (Responsive custom light-mode layouts)
* **Testing Library**: pytest (with StaticPool configuration for memory testing)

---

## 5. Entity-Relationship (ER) Diagram
The diagram below details the relational schema, cardinalities, and constraints of our SQLite database:

```mermaid
erDiagram
    USER {
        int id PK
        string username UNIQUE
        string email UNIQUE
        string password_hash
        string role "admin | staff | trekker"
        string status "pending | approved | blacklisted"
        datetime created_at
    }
    
    STAFF_PROFILE {
        int id PK
        int user_id FK
        string name
        string contact_details
    }

    TREK {
        int id PK
        string name UNIQUE
        string location
        string difficulty "Easy | Moderate | Hard"
        int duration
        int total_slots
        int available_slots
        string status "Pending | Approved | Open | Started | Closed | Completed"
        date start_date
        date end_date
        int assigned_staff_id FK
    }

    BOOKING {
        int id PK
        int user_id FK
        int trek_id FK
        datetime booking_date
        string status "Booked | Cancelled | Completed"
    }

    USER ||--o| STAFF_PROFILE : "has profile (if staff)"
    USER ||--o{ BOOKING : "places bookings (if trekker)"
    USER ||--o{ TREK : "assigned to treks (if staff)"
    TREK ||--o{ BOOKING : "associated with"
```

---

## 6. API Resource Endpoints
The platform exposes RESTful read-only JSON endpoints under the `/api` prefix:

### 1. Retrieve All Treks
* **Route**: `GET /api/treks`
* **Access**: Public
* **Output Format (JSON)**:
```json
[
  {
    "id": 1,
    "name": "Everest Base Camp",
    "location": "Nepal",
    "difficulty": "Hard",
    "duration": 12,
    "total_slots": 20,
    "available_slots": 18,
    "status": "Open",
    "start_date": "2026-07-20",
    "end_date": "2026-08-01",
    "assigned_staff_id": 2
  }
]
```

### 2. Retrieve All Bookings
* **Route**: `GET /api/bookings`
* **Access**: Logged-in Admin Users Only (returns `403` if non-admin)
* **Output Format (JSON)**:
```json
[
  {
    "id": 1,
    "user_id": 3,
    "trek_id": 1,
    "booking_date": "2026-07-12 18:22:15",
    "status": "Booked"
  }
]
```

### 3. Retrieve Registered Users
* **Route**: `GET /api/users`
* **Access**: Logged-in Admin Users Only (returns `403` if non-admin)
* **Output Format (JSON)**:
```json
[
  {
    "id": 3,
    "username": "Amit Sharma",
    "email": "amit@mail.com",
    "role": "trekker",
    "status": "approved",
    "created_at": "2026-07-12 18:02:51"
  }
]
```

---

## 7. Presentation Video
* **Video Link**: [Your Google Drive Presentation Video Link Here]
