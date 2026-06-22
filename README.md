# TrekSync: Trekking Management Application

TrekSync is a professional web application built on Flask, SQLite, and Bootstrap 5 designed to streamline trek operations. It features three distinct user portals: **Administrators**, **Trek Staff Guides**, and **Trekkers (Users)**.

The system incorporates robust transaction isolation to prevent overbooking, interactive Chart.js visualization panels, role-based access configurations, and RESTful API endpoints.

---

## 🚀 Key Features

* **Multi-Role Portals**: Distinct dashboards and left-sidebar menus matching the project wireframes.
* **Overbooking Protection**: Transactions are atomic and guarded against race conditions at the database layer.
* **Light Theme Design**: Styled using a clean Light Mode color scheme accented with nature-inspired emerald green.
* **Interactive Statistics Charts**: Renders booking distribution and route difficulty charts using Chart.js.
* **REST API Endpoints**: Read-only JSON resources (`GET /api/treks`, `GET /api/bookings`, `GET /api/users`) protected by role checks.
* **Seeded Mock Data**: Default CLI seeding provides mock data for guides, trekkers, and routes, allowing immediate testing.

---

## 🛠️ Tech Stack

* **Backend Framework**: Flask 3.x
* **Database & ORM**: SQLite & Flask-SQLAlchemy 3.x
* **Session Management**: Flask-Login (session cookies)
* **Form Validation**: Flask-WTF & WTForms (CSRF validation)
* **Visuals & Charts**: Chart.js
* **CSS Framework**: Bootstrap 5 (Custom biophilic layouts)
* **Testing Suite**: pytest (21 test cases passing)

---

## 📂 Project Structure

```
├── app/
│   ├── commands.py         # CLI seed commands (flask seed-db)
│   ├── forms.py            # Flask-WTF validation forms
│   ├── models.py           # SQLAlchemy database schemas
│   ├── routes/             # Blueprints (auth, admin, staff, trekker, api, main)
│   ├── static/             # CSS (custom light stylesheet)
│   └── templates/          # Jinja2 layouts and sidebar portals
├── tests/                  # Automated unit and integration test suite
├── config.py               # Database and security credentials
├── run.py                  # Entrypoint to start WSGI server
├── requirements.txt        # Package dependencies
└── README.md               # Documentation
```

---

## ⚙️ Getting Started

### 1. Set Up Environment & Install Dependencies
Clone the repository, create a virtual environment, and install packages:
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install requirements
pip install -r requirements.txt
```

### 2. Initialize and Seed the Database
Initialize tables and populate mock data matching the wireframe schemas:
```bash
# Configure application context
# Windows (PowerShell):
$env:FLASK_APP="run.py"
# macOS/Linux:
export FLASK_APP=run.py

# Run seed command
flask seed-db
```

### 3. Run the Development Server
Start the local server:
```bash
python run.py
```
Open your browser and navigate to: **`http://localhost:5000`**

### 4. Run the Automated Tests
Execute the pytest suite:
```bash
python -m pytest
```

---

## 🔐 Credentials for Seeding Verification

Use the following seeded accounts to verify the respective role workflows:

| Role | Username | Email | Password | Status |
| :--- | :--- | :--- | :--- | :--- |
| **Admin** | `admin` | `admin@trekking.com` | `AdminPassword123!` | Approved |
| **Staff Guide** | `vikas_guide` | `vikas@mail.com` | `Password123!` | Approved |
| **Staff Guide** | `neha_guide` | `neha@mail.com` | `Password123!` | Pending Approval |
| **Trekker** | `Amit Sharma` | `amit@mail.com` | `Password123!` | Approved |

---

## 📡 API Documentation

REST endpoints return JSON formatting:

* `GET /api/treks`: Public endpoint listing all treks.
* `GET /api/bookings`: Admin-only endpoint listing all bookings (requires admin cookie).
* `GET /api/users`: Admin-only endpoint listing registered users.

---

## 👤 Author
* **Name**: Zarrin Nehal
* **Roll Number**: 22f2000003
* **Email**: 22f2000003@ds.study.iitm.ac.in
