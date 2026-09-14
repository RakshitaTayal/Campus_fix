# CampusFix — College Problem Reporting & Resolution Platform

**CampusFix** is a straightforward, beginner-friendly web application designed for colleges and universities. It allows students to report problems across campus facilities, track ticket resolution in real-time, and receive updates when issues are fixed. Campus staff can manage work orders assigned to them, while college administrators supervise campus-wide metrics, dispatch staff, and adjust ticket priorities.

The project is structured specifically as a clean learning and practice codebase built entirely around **Python, Flask, SQLite, and Jinja2**, demonstrating core web development concepts like CRUD operations, authentication, session management, relational SQLite database modeling, form handling, and secure file uploads.

---

## 🌟 Key Features

### 🎓 Student Role
- **Account Registration & Authentication:** Secure registration and session-based login using Werkzeug password hashing.
- **Problem Reporting:** Submit issues with title, location, category, subcategory, urgency priority (Low, Medium, High, Critical), and optional photo upload.
- **Ticket Tracking & Search:** View all filed complaints, filter by status, priority, and category, and search by keywords.
- **Visual Progress Lifecycle:** Track the lifecycle from `Submitted` &rarr; `Under Review` &rarr; `Assigned` &rarr; `In Progress` &rarr; `Resolved` &rarr; `Closed`.
- **Confirmation & Reopen:** Students can confirm resolution by closing the complaint, or reopen it with an explanation if the issue persists.
- **In-App Notifications:** Real-time notifications for status transitions, assignments, and technician notes.

### 🔧 Staff Role
- **Assigned Maintenance Dashboard:** View complaints directly assigned by administrators.
- **Status & Timeline Updates:** Add progress comments (e.g. "Parts ordered", "Technician dispatched") and transition statuses between `Under Review`, `In Progress`, and `Resolved`.
- **Urgency Filtering:** Quick views for Critical and In-Progress work orders.

### 🏛️ Administrator Role
- **College-Wide Metrics:** Live counts for Total, Submitted, Under Review, Assigned, In Progress, Resolved, Closed, and Critical tickets.
- **Staff Dispatching:** Assign incoming complaints to relevant maintenance and IT personnel.
- **Ticket Management:** Override priorities, adjust statuses, and review full student and staff timelines.
- **User Directory:** Inspect registered students, maintenance teams, and administrators.

---

## 🛠️ Technology Stack

- **Backend:** Python 3, Flask, Jinja2
- **Database:** Python's built-in `sqlite3` (no heavy ORM)
- **Security:** Werkzeug (`generate_password_hash`, `check_password_hash`, `secure_filename`)
- **Frontend:** Semantic HTML5, clean custom CSS, and minimal vanilla JavaScript
- **File Storage:** Local secure `uploads/` directory for complaint photos

---

## 📁 Project Directory Structure

```text
CampusFix/
│
├── app.py                  # Main Flask routes, access control & application logic
├── database.py             # SQLite helper functions, schema definition & seed data
├── requirements.txt        # Python dependencies (Flask, Werkzeug)
├── README.md               # Project documentation & setup guide
├── .gitignore              # Git ignore rules for virtualenvs, caches & secrets
├── campusfix.db            # SQLite database file (auto-created on first run)
│
├── templates/              # Jinja2 HTML templates
│   ├── base.html           # Base layout with navbar, alerts & footer
│   ├── index.html          # Public landing page with demo account shortcuts
│   ├── login.html          # Authentication login page with quick autofill
│   ├── register.html       # Student registration page
│   ├── dashboard.html      # Student dashboard with summary cards & recent tickets
│   ├── report.html         # Issue reporting form with dynamic subcategories & photo upload
│   ├── complaints.html     # Student's "My Complaints" list with search & filters
│   ├── complaint_detail.html # Full complaint details, lifecycle tracker & comment timeline
│   ├── staff_dashboard.html# Staff view for assigned tickets & status changes
│   ├── admin_dashboard.html# Admin overview with campus-wide statistics
│   ├── admin_complaints.html# Admin master complaints directory with staff assignment
│   ├── admin_users.html    # Campus users directory (students and staff)
│   ├── notifications.html  # In-app notification center
│   ├── profile.html        # User account profile
│   ├── 404.html            # Friendly Not Found error page
│   └── 403.html            # Access Denied error page
│
├── static/                 # Static assets
│   ├── style.css           # Clean, responsive CSS styling
│   └── script.js           # Minimal vanilla JavaScript for UI interactions
│
└── uploads/                # Directory for user-uploaded complaint photos
```

---

## 🚀 Quick Setup & Installation

### 1. Clone the Repository
```bash
git clone https://github.com/your-username/CampusFix.git
cd CampusFix
```

### 2. Create and Activate Virtual Environment
On macOS / Linux:
```bash
python3 -m venv venv
source venv/bin/activate
```

On Windows (Command Prompt / PowerShell):
```cmd
python -m venv venv
venv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Run the Application
```bash
python app.py
```

Open your browser and navigate to:
```text
http://127.0.0.1:3000   (or http://localhost:3000)
```

---

## 🔑 Demo Test Accounts

The application automatically seeds realistic sample accounts and complaints upon first startup:

| Role | Email | Password | Purpose |
| :--- | :--- | :--- | :--- |
| **Student** | `student@campusfix.com` | `password123` | File problems, track tickets, close/reopen issues |
| **Staff (Facilities)** | `staff@campusfix.com` | `password123` | Manage carpentry, classroom furniture & facility jobs |
| **Staff (IT & AV)** | `marcus@campusfix.com` | `password123` | Manage projector, Wi-Fi & student portal tickets |
| **Administrator** | `admin@campusfix.com` | `password123` | Review statistics, assign staff, oversee all tickets |

*(The login page also includes 1-click credential buttons for rapid testing).*

---

## 🔄 Complete Resolution Workflow Tested

```text
       STUDENT
          │
          ▼
       Register / Login
          │
          ▼
   Submit Complaint (e.g. CMP-1001)
   Status: "Submitted"
          │
          ▼
       ADMIN
          │
          ▼
   Reviews ticket & assigns to Staff
   Status: "Assigned"
          │
          ▼
       STAFF
          │
          ▼
   Investigates & updates status
   Status: "In Progress"
          │
          ▼
   Completes fix
   Status: "Resolved"
          │
          ▼
       STUDENT
     ┌────┴───────────────┐
     ▼                    ▼
[Confirm & Close]    [Reopen Ticket]
 Status: "Closed"     Status: "Reopened"
```
