"""
database.py - Database operations and setup for CampusFix.
Uses Python's built-in sqlite3 module to manage SQLite tables and queries.
"""

import sqlite3
import os
from werkzeug.security import generate_password_hash

# Path to the SQLite database file
DB_NAME = "campusfix.db"

def get_db_connection():
    """
    Establishes and returns a connection to the SQLite database.
    Configures row_factory so query results can be accessed like dictionaries.
    """
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    # Enable foreign key constraints in SQLite
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def init_db():
    """
    Initializes the database by creating necessary tables if they do not exist,
    and seeds demo users and realistic complaints if the database is empty.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    # 1. Users Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        role TEXT NOT NULL CHECK(role IN ('student', 'staff', 'admin')),
        department TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # 2. Complaints Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS complaints (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        complaint_id TEXT UNIQUE NOT NULL,
        student_id INTEGER NOT NULL,
        title TEXT NOT NULL,
        description TEXT NOT NULL,
        category TEXT NOT NULL,
        subcategory TEXT NOT NULL,
        location TEXT NOT NULL,
        priority TEXT NOT NULL CHECK(priority IN ('Low', 'Medium', 'High', 'Critical')),
        status TEXT NOT NULL CHECK(status IN ('Submitted', 'Under Review', 'Assigned', 'In Progress', 'Resolved', 'Closed', 'Reopened')),
        assigned_staff_id INTEGER,
        image_filename TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (student_id) REFERENCES users (id),
        FOREIGN KEY (assigned_staff_id) REFERENCES users (id)
    )
    """)

    # 3. Comments / Timeline Updates Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS comments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        complaint_id INTEGER NOT NULL,
        user_id INTEGER NOT NULL,
        comment TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (complaint_id) REFERENCES complaints (id) ON DELETE CASCADE,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )
    """)

    # 4. Notifications Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS notifications (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        message TEXT NOT NULL,
        complaint_id INTEGER,
        is_read INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id),
        FOREIGN KEY (complaint_id) REFERENCES complaints (id) ON DELETE SET NULL
    )
    """)

    conn.commit()

    # Seed initial demo data if users table is empty
    cursor.execute("SELECT COUNT(*) FROM users")
    user_count = cursor.fetchone()[0]

    if user_count == 0:
        seed_demo_data(cursor, conn)

    conn.close()

def seed_demo_data(cursor, conn):
    """
    Populates default demo users, staff, admin, and realistic sample complaints.
    """
    default_password = generate_password_hash("password123")

    # Insert Users
    users_data = [
        ("Alex Johnson (Student)", "student@campusfix.com", default_password, "student", "Computer Science"),
        ("Sarah Williams (Student)", "sarah@campusfix.com", default_password, "student", "Electrical Engineering"),
        ("John Davis (Staff - Facilities)", "staff@campusfix.com", default_password, "staff", "Campus Facilities"),
        ("Marcus Vance (Staff - IT & AV)", "marcus@campusfix.com", default_password, "staff", "IT & Digital Services"),
        ("Elena Rostova (Staff - Maintenance)", "elena@campusfix.com", default_password, "staff", "Utilities & Maintenance"),
        ("Dr. Arthur Pendelton (Admin)", "admin@campusfix.com", default_password, "admin", "Campus Administration")
    ]

    cursor.executemany("""
        INSERT INTO users (name, email, password, role, department)
        VALUES (?, ?, ?, ?, ?)
    """, users_data)

    conn.commit()

    # Retrieve inserted IDs
    cursor.execute("SELECT id, email FROM users")
    user_map = {row["email"]: row["id"] for row in cursor.fetchall()}

    student1_id = user_map["student@campusfix.com"]
    student2_id = user_map["sarah@campusfix.com"]
    staff_facilities_id = user_map["staff@campusfix.com"]
    staff_it_id = user_map["marcus@campusfix.com"]
    staff_maint_id = user_map["elena@campusfix.com"]
    admin_id = user_map["admin@campusfix.com"]

    # Sample realistic complaints
    complaints_data = [
        (
            "CMP-1001", student1_id,
            "Broken overhead projector in Lecture Hall B",
            "The projector blinks magenta continuously and shuts off after 5 minutes of use during morning lectures.",
            "Technology & Digital Services", "Projectors",
            "Science Block, Room 204 (Lecture Hall B)",
            "High", "In Progress", staff_it_id, None,
            "2026-09-10 09:30:00", "2026-09-11 14:15:00"
        ),
        (
            "CMP-1002", student1_id,
            "Water leakage near 2nd floor washroom",
            "Persistent pipe leakage under the main washroom basin causing slippery tiles and safety hazard for students.",
            "Utilities & Maintenance", "Plumbing",
            "Engineering Wing B, 2nd Floor Corridor",
            "Critical", "Assigned", staff_maint_id, None,
            "2026-09-11 11:00:00", "2026-09-12 08:30:00"
        ),
        (
            "CMP-1003", student2_id,
            "Wi-Fi connection drops repeatedly in Central Library",
            "Campus-Student Wi-Fi network constantly disconnects every 2 minutes on the 3rd floor study section.",
            "Technology & Digital Services", "Wi-Fi",
            "Central Library, 3rd Floor Quiet Study Area",
            "Medium", "Under Review", None, None,
            "2026-09-12 10:15:00", "2026-09-12 10:15:00"
        ),
        (
            "CMP-1004", student1_id,
            "Damaged wooden desk and loose chairs in Seminar Hall",
            "Row 3 desk has broken splintered wooden edge and three attached chairs are rocking dangerously.",
            "Infrastructure & Facilities", "Furniture",
            "Academic Complex 1, Seminar Hall A",
            "Low", "Resolved", staff_facilities_id, None,
            "2026-09-08 14:00:00", "2026-09-10 16:00:00"
        ),
        (
            "CMP-1005", student2_id,
            "Main pathway streetlight malfunctioning near North Gate",
            "Three streetlights along the student hostel pathway are completely dead, making walking at night hazardous.",
            "Utilities & Maintenance", "Electricity",
            "North Gate Pathway between Hostel 4 and Library",
            "High", "Submitted", None, None,
            "2026-09-13 18:45:00", "2026-09-13 18:45:00"
        ),
        (
            "CMP-1006", student1_id,
            "Canteen water dispenser filter replacement needed",
            "Water dispenser in the main cafeteria has a red 'Replace Filter' indicator light and water tastes metallic.",
            "Student Services & Transport", "Canteen",
            "Campus Student Center, Main Cafeteria",
            "Medium", "Closed", staff_facilities_id, None,
            "2026-09-05 12:00:00", "2026-09-09 11:30:00"
        ),
        (
            "CMP-1007", student2_id,
            "Course registration portal throws 500 error on elective select",
            "Students attempting to submit minor degree electives on the portal receive Internal Server Error.",
            "Technology & Digital Services", "College Portal",
            "Online Student Portal System",
            "Critical", "In Progress", staff_it_id, None,
            "2026-09-12 16:30:00", "2026-09-13 09:00:00"
        ),
        (
            "CMP-1008", student1_id,
            "Emergency exit door latch jammed on ground floor",
            "Fire exit push-bar door in Building 4 ground floor is stuck shut and does not push open smoothly.",
            "Safety & Security", "Emergency Campus Issue",
            "Arts & Humanities Building, South Fire Exit",
            "Critical", "Assigned", staff_facilities_id, None,
            "2026-09-13 13:20:00", "2026-09-13 14:00:00"
        ),
        (
            "CMP-1009", student2_id,
            "Air conditioning unit making loud buzzing noise in Room 108",
            "Split AC unit in computer lab 2 rattles violently, disrupting classes.",
            "Utilities & Maintenance", "General Maintenance",
            "Tech Block, Room 108 (Lab 2)",
            "Low", "Submitted", None, None,
            "2026-09-13 17:10:00", "2026-09-13 17:10:00"
        )
    ]

    for comp in complaints_data:
        cursor.execute("""
            INSERT INTO complaints (
                complaint_id, student_id, title, description, category, subcategory,
                location, priority, status, assigned_staff_id, image_filename,
                created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, comp)

    conn.commit()

    # Add realistic comments and updates
    # CMP-1001 comments
    cursor.execute("SELECT id FROM complaints WHERE complaint_id = 'CMP-1001'")
    c1_id = cursor.fetchone()[0]
    cursor.executemany("""
        INSERT INTO comments (complaint_id, user_id, comment, created_at)
        VALUES (?, ?, ?, ?)
    """, [
        (c1_id, student1_id, "Reported issue: projector shut off during Prof. Chen's lecture today.", "2026-09-10 09:30:00"),
        (c1_id, admin_id, "Complaint reviewed and assigned to IT & AV support team (Marcus Vance).", "2026-09-10 11:00:00"),
        (c1_id, staff_it_id, "Technician visited Room 204. Found faulty cooling fan causing thermal safety shutdown. Replacement fan ordered.", "2026-09-11 14:15:00")
    ])

    # CMP-1002 comments
    cursor.execute("SELECT id FROM complaints WHERE complaint_id = 'CMP-1002'")
    c2_id = cursor.fetchone()[0]
    cursor.executemany("""
        INSERT INTO comments (complaint_id, user_id, comment, created_at)
        VALUES (?, ?, ?, ?)
    """, [
        (c2_id, student1_id, "Water pooling in hallway, caution tape needed immediately.", "2026-09-11 11:00:00"),
        (c2_id, admin_id, "Assigned to Elena Rostova (Utilities & Maintenance). High priority dispatch.", "2026-09-12 08:30:00")
    ])

    # CMP-1004 comments
    cursor.execute("SELECT id FROM complaints WHERE complaint_id = 'CMP-1004'")
    c4_id = cursor.fetchone()[0]
    cursor.executemany("""
        INSERT INTO comments (complaint_id, user_id, comment, created_at)
        VALUES (?, ?, ?, ?)
    """, [
        (c4_id, student1_id, "Desks need sanding and screws tightened before upcoming seminar.", "2026-09-08 14:00:00"),
        (c4_id, staff_facilities_id, "Carpentry team completed repairs on row 3 desk and replaced loose bolts.", "2026-09-10 16:00:00")
    ])

    # Add sample notifications
    notifications_data = [
        (student1_id, "Your complaint CMP-1001 has been assigned to Marcus Vance.", c1_id, 0, "2026-09-10 11:00:00"),
        (student1_id, "Marcus Vance added an update to CMP-1001: Replacement fan ordered.", c1_id, 0, "2026-09-11 14:15:00"),
        (student1_id, "Your complaint CMP-1004 has been marked as Resolved by John Davis.", c4_id, 1, "2026-09-10 16:00:00"),
        (staff_it_id, "You have been assigned a new complaint: CMP-1001 (Broken overhead projector).", c1_id, 1, "2026-09-10 11:00:00"),
        (staff_maint_id, "You have been assigned a new complaint: CMP-1002 (Water leakage near washroom).", c2_id, 0, "2026-09-12 08:30:00")
    ]

    cursor.executemany("""
        INSERT INTO notifications (user_id, message, complaint_id, is_read, created_at)
        VALUES (?, ?, ?, ?, ?)
    """, notifications_data)

    conn.commit()


# ==========================================================
# USER OPERATIONS
# ==========================================================

def create_user(name, email, password_hash, role="student", department=None):
    """Inserts a new user into the database."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO users (name, email, password, role, department)
            VALUES (?, ?, ?, ?, ?)
        """, (name, email.lower().strip(), password_hash, role, department))
        conn.commit()
        user_id = cursor.lastrowid
        return user_id
    except sqlite3.IntegrityError:
        return None
    finally:
        conn.close()

def get_user_by_email(email):
    """Fetches a user record by email address."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE LOWER(email) = LOWER(?)", (email.strip(),))
    user = cursor.fetchone()
    conn.close()
    return user

def get_user_by_id(user_id):
    """Fetches a user record by primary key id."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    user = cursor.fetchone()
    conn.close()
    return user

def get_all_users():
    """Retrieves all registered users ordered by creation date."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, email, role, department, created_at FROM users ORDER BY created_at DESC")
    users = cursor.fetchall()
    conn.close()
    return users

def get_staff_members():
    """Retrieves list of all staff members available for assignment."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, email, department FROM users WHERE role = 'staff' ORDER BY name ASC")
    staff = cursor.fetchall()
    conn.close()
    return staff


# ==========================================================
# COMPLAINT OPERATIONS
# ==========================================================

def generate_complaint_id(cursor):
    """Generates next readable complaint ID, e.g., CMP-1010."""
    cursor.execute("SELECT id FROM complaints ORDER BY id DESC LIMIT 1")
    last_row = cursor.fetchone()
    next_num = 1001 if not last_row else (1000 + last_row["id"] + 1)
    return f"CMP-{next_num}"

def create_complaint(student_id, title, description, category, subcategory, location, priority, image_filename=None):
    """Creates a new complaint submitted by a student."""
    conn = get_db_connection()
    cursor = conn.cursor()
    complaint_code = generate_complaint_id(cursor)

    cursor.execute("""
        INSERT INTO complaints (
            complaint_id, student_id, title, description, category, subcategory,
            location, priority, status, image_filename
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'Submitted', ?)
    """, (complaint_code, student_id, title, description, category, subcategory, location, priority, image_filename))

    complaint_db_id = cursor.lastrowid

    # Add initial creation comment
    cursor.execute("""
        INSERT INTO comments (complaint_id, user_id, comment)
        VALUES (?, ?, ?)
    """, (complaint_db_id, student_id, "Complaint submitted by student."))

    # Add confirmation notification for student
    cursor.execute("""
        INSERT INTO notifications (user_id, message, complaint_id)
        VALUES (?, ?, ?)
    """, (student_id, f"Your complaint {complaint_code} was successfully submitted.", complaint_db_id))

    conn.commit()
    conn.close()
    return complaint_code

def get_complaint_by_code(complaint_id_code):
    """Fetches a complaint by its readable code (e.g. 'CMP-1001') with student & staff details."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT c.*,
               s.name AS student_name, s.email AS student_email,
               st.name AS staff_name, st.email AS staff_email, st.department AS staff_department
        FROM complaints c
        JOIN users s ON c.student_id = s.id
        LEFT JOIN users st ON c.assigned_staff_id = st.id
        WHERE c.complaint_id = ?
    """, (complaint_id_code,))
    complaint = cursor.fetchone()
    conn.close()
    return complaint

def get_student_complaints(student_id, search_query="", category_filter="", status_filter="", priority_filter=""):
    """Fetches complaints filed by a specific student with optional filters."""
    conn = get_db_connection()
    cursor = conn.cursor()

    query = """
        SELECT c.*, st.name AS staff_name
        FROM complaints c
        LEFT JOIN users st ON c.assigned_staff_id = st.id
        WHERE c.student_id = ?
    """
    params = [student_id]

    if search_query:
        query += " AND (c.complaint_id LIKE ? OR c.title LIKE ? OR c.location LIKE ? OR c.description LIKE ?)"
        term = f"%{search_query}%"
        params.extend([term, term, term, term])

    if category_filter:
        query += " AND c.category = ?"
        params.append(category_filter)

    if status_filter:
        query += " AND c.status = ?"
        params.append(status_filter)

    if priority_filter:
        query += " AND c.priority = ?"
        params.append(priority_filter)

    query += " ORDER BY c.created_at DESC"

    cursor.execute(query, params)
    complaints = cursor.fetchall()
    conn.close()
    return complaints

def get_staff_complaints(staff_id, search_query="", status_filter="", priority_filter=""):
    """Fetches complaints assigned to a particular staff member."""
    conn = get_db_connection()
    cursor = conn.cursor()

    query = """
        SELECT c.*, s.name AS student_name
        FROM complaints c
        JOIN users s ON c.student_id = s.id
        WHERE c.assigned_staff_id = ?
    """
    params = [staff_id]

    if search_query:
        query += " AND (c.complaint_id LIKE ? OR c.title LIKE ? OR c.location LIKE ?)"
        term = f"%{search_query}%"
        params.extend([term, term, term])

    if status_filter:
        query += " AND c.status = ?"
        params.append(status_filter)

    if priority_filter:
        query += " AND c.priority = ?"
        params.append(priority_filter)

    query += " ORDER BY c.created_at DESC"

    cursor.execute(query, params)
    complaints = cursor.fetchall()
    conn.close()
    return complaints

def get_all_complaints(search_query="", category_filter="", status_filter="", priority_filter=""):
    """Fetches all complaints for administrators with search and filtering."""
    conn = get_db_connection()
    cursor = conn.cursor()

    query = """
        SELECT c.*, s.name AS student_name, st.name AS staff_name
        FROM complaints c
        JOIN users s ON c.student_id = s.id
        LEFT JOIN users st ON c.assigned_staff_id = st.id
        WHERE 1=1
    """
    params = []

    if search_query:
        query += " AND (c.complaint_id LIKE ? OR c.title LIKE ? OR c.location LIKE ? OR s.name LIKE ?)"
        term = f"%{search_query}%"
        params.extend([term, term, term, term])

    if category_filter:
        query += " AND c.category = ?"
        params.append(category_filter)

    if status_filter:
        query += " AND c.status = ?"
        params.append(status_filter)

    if priority_filter:
        query += " AND c.priority = ?"
        params.append(priority_filter)

    query += " ORDER BY c.created_at DESC"

    cursor.execute(query, params)
    complaints = cursor.fetchall()
    conn.close()
    return complaints

def update_complaint_status(complaint_db_id, new_status, user_id, comment_text=None):
    """
    Updates the status of a complaint, creates a timeline comment,
    and dispatches a notification to the student.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    # Get complaint details
    cursor.execute("SELECT complaint_id, student_id, assigned_staff_id, status FROM complaints WHERE id = ?", (complaint_db_id,))
    comp = cursor.fetchone()
    if not comp:
        conn.close()
        return False

    complaint_code = comp["complaint_id"]
    student_id = comp["student_id"]
    old_status = comp["status"]

    # Update complaint
    cursor.execute("""
        UPDATE complaints
        SET status = ?, updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
    """, (new_status, complaint_db_id))

    # Add timeline comment
    if not comment_text:
        comment_text = f"Status changed from '{old_status}' to '{new_status}'."

    cursor.execute("""
        INSERT INTO comments (complaint_id, user_id, comment)
        VALUES (?, ?, ?)
    """, (complaint_db_id, user_id, comment_text))

    # Notify student
    cursor.execute("""
        INSERT INTO notifications (user_id, message, complaint_id)
        VALUES (?, ?, ?)
    """, (student_id, f"Your complaint {complaint_code} status updated to: {new_status}.", complaint_db_id))

    conn.commit()
    conn.close()
    return True

def assign_complaint(complaint_db_id, staff_id, admin_user_id):
    """Assigns complaint to a staff member and sets status to Assigned."""
    conn = get_db_connection()
    cursor = conn.cursor()

    # Fetch staff and complaint details
    cursor.execute("SELECT name FROM users WHERE id = ?", (staff_id,))
    staff = cursor.fetchone()
    if not staff:
        conn.close()
        return False

    cursor.execute("SELECT complaint_id, student_id FROM complaints WHERE id = ?", (complaint_db_id,))
    comp = cursor.fetchone()
    if not comp:
        conn.close()
        return False

    staff_name = staff["name"]
    complaint_code = comp["complaint_id"]
    student_id = comp["student_id"]

    cursor.execute("""
        UPDATE complaints
        SET assigned_staff_id = ?, status = 'Assigned', updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
    """, (staff_id, complaint_db_id))

    # Add timeline comment
    cursor.execute("""
        INSERT INTO comments (complaint_id, user_id, comment)
        VALUES (?, ?, ?)
    """, (complaint_db_id, admin_user_id, f"Assigned to {staff_name}. Status changed to Assigned."))

    # Notify Student
    cursor.execute("""
        INSERT INTO notifications (user_id, message, complaint_id)
        VALUES (?, ?, ?)
    """, (student_id, f"Your complaint {complaint_code} has been assigned to staff member {staff_name}.", complaint_db_id))

    # Notify Staff
    cursor.execute("""
        INSERT INTO notifications (user_id, message, complaint_id)
        VALUES (?, ?, ?)
    """, (staff_id, f"New complaint assigned to you: {complaint_code}.", complaint_db_id))

    conn.commit()
    conn.close()
    return True

def update_complaint_priority(complaint_db_id, new_priority, admin_user_id):
    """Allows an administrator to change complaint priority level."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT complaint_id, priority FROM complaints WHERE id = ?", (complaint_db_id,))
    comp = cursor.fetchone()
    if not comp:
        conn.close()
        return False

    old_priority = comp["priority"]
    cursor.execute("""
        UPDATE complaints
        SET priority = ?, updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
    """, (new_priority, complaint_db_id))

    cursor.execute("""
        INSERT INTO comments (complaint_id, user_id, comment)
        VALUES (?, ?, ?)
    """, (complaint_db_id, admin_user_id, f"Priority adjusted from {old_priority} to {new_priority}."))

    conn.commit()
    conn.close()
    return True

def add_complaint_comment(complaint_db_id, user_id, comment_text):
    """Appends an update/comment to a complaint timeline."""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO comments (complaint_id, user_id, comment)
        VALUES (?, ?, ?)
    """, (complaint_db_id, user_id, comment_text))

    # Update timestamp
    cursor.execute("UPDATE complaints SET updated_at = CURRENT_TIMESTAMP WHERE id = ?", (complaint_db_id,))

    # Determine who to notify
    cursor.execute("SELECT complaint_id, student_id, assigned_staff_id FROM complaints WHERE id = ?", (complaint_db_id,))
    comp = cursor.fetchone()
    cursor.execute("SELECT name, role FROM users WHERE id = ?", (user_id,))
    author = cursor.fetchone()

    if comp and author:
        complaint_code = comp["complaint_id"]
        # If staff or admin posted, notify student
        if author["role"] in ('staff', 'admin') and comp["student_id"] != user_id:
            cursor.execute("""
                INSERT INTO notifications (user_id, message, complaint_id)
                VALUES (?, ?, ?)
            """, (comp["student_id"], f"New update from {author['name']} on {complaint_code}.", complaint_db_id))

        # If student posted, notify assigned staff if any
        if author["role"] == 'student' and comp["assigned_staff_id"]:
            cursor.execute("""
                INSERT INTO notifications (user_id, message, complaint_id)
                VALUES (?, ?, ?)
            """, (comp["assigned_staff_id"], f"Student {author['name']} commented on {complaint_code}.", complaint_db_id))

    conn.commit()
    conn.close()
    return True

def get_complaint_comments(complaint_db_id):
    """Retrieves all comments/updates for a complaint along with author information."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT c.*, u.name AS author_name, u.role AS author_role, u.department AS author_department
        FROM comments c
        JOIN users u ON c.user_id = u.id
        WHERE c.complaint_id = ?
        ORDER BY c.created_at ASC
    """, (complaint_db_id,))
    comments = cursor.fetchall()
    conn.close()
    return comments


# ==========================================================
# NOTIFICATIONS OPERATIONS
# ==========================================================

def get_user_notifications(user_id):
    """Returns all notifications for a given user, newest first."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT n.*, c.complaint_id AS complaint_code
        FROM notifications n
        LEFT JOIN complaints c ON n.complaint_id = c.id
        WHERE n.user_id = ?
        ORDER BY n.created_at DESC
    """, (user_id,))
    notifs = cursor.fetchall()
    conn.close()
    return notifs

def get_unread_notification_count(user_id):
    """Counts unread notifications for navigation badge display."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM notifications WHERE user_id = ? AND is_read = 0", (user_id,))
    count = cursor.fetchone()[0]
    conn.close()
    return count

def mark_notification_as_read(notification_id, user_id):
    """Marks a specific notification as read."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE notifications SET is_read = 1 WHERE id = ? AND user_id = ?", (notification_id, user_id))
    conn.commit()
    conn.close()

def mark_all_notifications_as_read(user_id):
    """Marks all notifications for a user as read."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE notifications SET is_read = 1 WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()


# ==========================================================
# STATISTICS / DASHBOARD METRICS
# ==========================================================

def get_student_dashboard_stats(student_id):
    """Calculates summary cards metrics for student dashboard."""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM complaints WHERE student_id = ?", (student_id,))
    total = cursor.fetchone()[0]

    cursor.execute("""
        SELECT COUNT(*) FROM complaints
        WHERE student_id = ? AND status IN ('Submitted', 'Under Review', 'Assigned')
    """, (student_id,))
    pending = cursor.fetchone()[0]

    cursor.execute("""
        SELECT COUNT(*) FROM complaints
        WHERE student_id = ? AND status = 'In Progress'
    """, (student_id,))
    in_progress = cursor.fetchone()[0]

    cursor.execute("""
        SELECT COUNT(*) FROM complaints
        WHERE student_id = ? AND status IN ('Resolved', 'Closed')
    """, (student_id,))
    resolved = cursor.fetchone()[0]

    conn.close()
    return {
        "total": total,
        "pending": pending,
        "in_progress": in_progress,
        "resolved": resolved
    }

def get_staff_dashboard_stats(staff_id):
    """Calculates summary cards metrics for staff dashboard."""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM complaints WHERE assigned_staff_id = ?", (staff_id,))
    assigned = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM complaints WHERE assigned_staff_id = ? AND status = 'In Progress'", (staff_id,))
    in_progress = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM complaints WHERE assigned_staff_id = ? AND status IN ('Resolved', 'Closed')", (staff_id,))
    resolved = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM complaints WHERE assigned_staff_id = ? AND priority = 'Critical'", (staff_id,))
    critical = cursor.fetchone()[0]

    conn.close()
    return {
        "assigned": assigned,
        "in_progress": in_progress,
        "resolved": resolved,
        "critical": critical
    }

def get_admin_dashboard_stats():
    """Calculates complete system-wide statistics for administrator dashboard."""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM complaints")
    total = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM complaints WHERE status = 'Submitted'")
    submitted = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM complaints WHERE status = 'Under Review'")
    under_review = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM complaints WHERE status = 'Assigned'")
    assigned = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM complaints WHERE status = 'In Progress'")
    in_progress = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM complaints WHERE status = 'Resolved'")
    resolved = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM complaints WHERE status = 'Closed'")
    closed = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM complaints WHERE priority = 'Critical'")
    critical = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM users WHERE role = 'student'")
    student_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM users WHERE role = 'staff'")
    staff_count = cursor.fetchone()[0]

    conn.close()
    return {
        "total": total,
        "submitted": submitted,
        "under_review": under_review,
        "assigned": assigned,
        "in_progress": in_progress,
        "resolved": resolved,
        "closed": closed,
        "critical": critical,
        "student_count": student_count,
        "staff_count": staff_count
    }
