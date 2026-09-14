"""
app.py - Main Flask application entry point for CampusFix.
A clean, straightforward Python Flask application using SQLite.
"""

import os
from datetime import datetime
from functools import wraps
from flask import (
    Flask, render_template, request, redirect, url_for,
    session, flash, send_from_directory, abort, g
)
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import database

# Initialize Flask app
app = Flask(__name__)
# Secret key for session signing
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "campusfix-super-secret-key-2026")

# Configure upload directory
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "uploads")
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp"}
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 8 * 1024 * 1024  # Max 8MB uploads

# Ensure uploads folder exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Define official Categories and Subcategories
CATEGORIES = {
    "Infrastructure & Facilities": [
        "Classrooms", "Furniture", "Washrooms", "Buildings", "Campus Facilities"
    ],
    "Utilities & Maintenance": [
        "Electricity", "Water", "Cleaning", "Plumbing", "General Maintenance"
    ],
    "Technology & Digital Services": [
        "Wi-Fi", "Computers", "Projectors", "College Portal", "Digital Services"
    ],
    "Student Services & Transport": [
        "Transport", "Library", "Canteen", "Student Services"
    ],
    "Safety & Security": [
        "Campus Safety", "Security", "Emergency Campus Issue"
    ]
}

PRIORITY_LEVELS = ["Low", "Medium", "High", "Critical"]
STATUS_ORDER = ["Submitted", "Under Review", "Assigned", "In Progress", "Resolved", "Closed"]


def allowed_file(filename):
    """Check if uploaded file extension is allowed."""
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


# ==========================================================
# ACCESS CONTROL DECORATORS & HELPERS
# ==========================================================

def login_required(f):
    """Restricts route to logged-in users."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in to access this page.", "warning")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated_function

def role_required(allowed_roles):
    """Restricts route to users with specified role(s)."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if "user_id" not in session:
                flash("Please log in to access this page.", "warning")
                return redirect(url_for("login"))
            user_role = session.get("user_role")
            if user_role not in allowed_roles:
                abort(403)
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def student_required(f):
    return role_required(["student"])(f)

def staff_required(f):
    return role_required(["staff"])(f)

def admin_required(f):
    return role_required(["admin"])(f)


# ==========================================================
# CONTEXT PROCESSOR FOR GLOBAL TEMPLATE VARIABLES
# ==========================================================

@app.context_processor
def inject_global_data():
    """Injects notifications count and user details into all Jinja templates."""
    unread_count = 0
    if "user_id" in session:
        unread_count = database.get_unread_notification_count(session["user_id"])
    return {
        "current_user_name": session.get("user_name"),
        "current_user_email": session.get("user_email"),
        "current_user_role": session.get("user_role"),
        "unread_notifications_count": unread_count,
        "categories_dict": CATEGORIES,
        "priority_levels": PRIORITY_LEVELS
    }


# ==========================================================
# AUTHENTICATION ROUTES
# ==========================================================

@app.route("/")
def index():
    """Landing page introducing CampusFix."""
    if "user_id" in session:
        # If already logged in, redirect to respective dashboard
        role = session.get("user_role")
        if role == "admin":
            return redirect(url_for("admin_dashboard"))
        elif role == "staff":
            return redirect(url_for("staff_dashboard"))
        else:
            return redirect(url_for("dashboard"))
    return render_template("index.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    """Student registration route."""
    if "user_id" in session:
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")
        department = request.form.get("department", "").strip()

        # Simple validation
        if not name or not email or not password:
            flash("Please fill in all required fields.", "error")
            return render_template("register.html", name=name, email=email, department=department)

        if password != confirm_password:
            flash("Passwords do not match. Please try again.", "error")
            return render_template("register.html", name=name, email=email, department=department)

        if len(password) < 6:
            flash("Password must be at least 6 characters long.", "error")
            return render_template("register.html", name=name, email=email, department=department)

        # Check existing user
        existing_user = database.get_user_by_email(email)
        if existing_user:
            flash("An account with this email already exists. Please log in.", "error")
            return render_template("register.html", name=name, email=email, department=department)

        # Hash password using Werkzeug
        hashed_password = generate_password_hash(password)

        # Always assign role 'student' for public self-registration
        user_id = database.create_user(
            name=name,
            email=email,
            password_hash=hashed_password,
            role="student",
            department=department or "Undergraduate Student"
        )

        if user_id:
            # Set session
            session["user_id"] = user_id
            session["user_name"] = name
            session["user_email"] = email
            session["user_role"] = "student"
            flash(f"Welcome to CampusFix, {name}! Your account has been created.", "success")
            return redirect(url_for("dashboard"))
        else:
            flash("Registration failed. Please try again.", "error")

    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    """User login route."""
    if "user_id" in session:
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        if not email or not password:
            flash("Please enter both email and password.", "error")
            return render_template("login.html", email=email)

        user = database.get_user_by_email(email)

        if user and check_password_hash(user["password"], password):
            # Password matches, store in session
            session["user_id"] = user["id"]
            session["user_name"] = user["name"]
            session["user_email"] = user["email"]
            session["user_role"] = user["role"]
            flash(f"Signed in successfully as {user['name']}.", "success")

            # Redirect based on user role
            if user["role"] == "admin":
                return redirect(url_for("admin_dashboard"))
            elif user["role"] == "staff":
                return redirect(url_for("staff_dashboard"))
            else:
                return redirect(url_for("dashboard"))
        else:
            flash("Invalid email or password. Please try again.", "error")
            return render_template("login.html", email=email)

    return render_template("login.html")

@app.route("/logout")
def logout():
    """Clears user session and logs out."""
    session.clear()
    flash("You have been signed out.", "info")
    return redirect(url_for("login"))


# ==========================================================
# STUDENT ROUTES
# ==========================================================

@app.route("/dashboard")
@login_required
def dashboard():
    """Role-aware dashboard."""
    role = session.get("user_role")
    if role == "admin":
        return redirect(url_for("admin_dashboard"))
    elif role == "staff":
        return redirect(url_for("staff_dashboard"))

    student_id = session["user_id"]
    stats = database.get_student_dashboard_stats(student_id)
    # Get latest complaints
    recent_complaints = database.get_student_complaints(student_id)[:5]

    return render_template("dashboard.html", stats=stats, complaints=recent_complaints)

@app.route("/report", methods=["GET", "POST"])
@login_required
@student_required
def report():
    """Report a new campus problem."""
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        description = request.form.get("description", "").strip()
        category = request.form.get("category", "").strip()
        subcategory = request.form.get("subcategory", "").strip()
        location = request.form.get("location", "").strip()
        priority = request.form.get("priority", "Medium").strip()

        # Validation
        if not title or not description or not category or not location:
            flash("Please fill in all required fields (Title, Category, Location, Description).", "error")
            return render_template("report.html",
                title=title, description=description, category=category,
                subcategory=subcategory, location=location, priority=priority
            )

        # Handle optional image upload
        image_filename = None
        if "image" in request.files:
            file = request.files["image"]
            if file and file.filename != "":
                if allowed_file(file.filename):
                    # Make filename safe and unique
                    original_name = secure_filename(file.filename)
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    image_filename = f"{timestamp}_{original_name}"
                    file.save(os.path.join(app.config["UPLOAD_FOLDER"], image_filename))
                else:
                    flash("Invalid image format. Allowed formats: PNG, JPG, JPEG, WEBP.", "error")
                    return render_template("report.html",
                        title=title, description=description, category=category,
                        subcategory=subcategory, location=location, priority=priority
                    )

        # Create complaint in database
        complaint_code = database.create_complaint(
            student_id=session["user_id"],
            title=title,
            description=description,
            category=category,
            subcategory=subcategory or "General",
            location=location,
            priority=priority,
            image_filename=image_filename
        )

        flash(f"Complaint {complaint_code} submitted successfully! Our campus team has been notified.", "success")
        return redirect(url_for("complaint_detail", complaint_id=complaint_code))

    return render_template("report.html")

@app.route("/complaints")
@login_required
@student_required
def complaints():
    """View and filter student's own complaints."""
    student_id = session["user_id"]
    search = request.args.get("search", "").strip()
    category = request.args.get("category", "").strip()
    status = request.args.get("status", "").strip()
    priority = request.args.get("priority", "").strip()

    student_complaints = database.get_student_complaints(
        student_id=student_id,
        search_query=search,
        category_filter=category,
        status_filter=status,
        priority_filter=priority
    )

    return render_template(
        "complaints.html",
        complaints=student_complaints,
        search=search,
        selected_category=category,
        selected_status=status,
        selected_priority=priority
    )


# ==========================================================
# COMPLAINT DETAILS & SHARED ACTIONS
# ==========================================================

@app.route("/complaint/<complaint_id>")
@login_required
def complaint_detail(complaint_id):
    """View detailed information, status lifecycle, updates, and actions for a complaint."""
    complaint = database.get_complaint_by_code(complaint_id)
    if not complaint:
        abort(404)

    # Access control:
    # Students can only view their own complaints
    current_user_id = session["user_id"]
    current_role = session["user_role"]

    if current_role == "student" and complaint["student_id"] != current_user_id:
        abort(403)

    comments = database.get_complaint_comments(complaint["id"])
    staff_list = []
    if current_role == "admin":
        staff_list = database.get_staff_members()

    return render_template(
        "complaint_detail.html",
        complaint=complaint,
        comments=comments,
        staff_list=staff_list,
        status_order=STATUS_ORDER
    )

@app.route("/complaint/<int:complaint_db_id>/comment", methods=["POST"])
@login_required
def add_comment(complaint_db_id):
    """Add a new comment or progress update to a complaint."""
    comment_text = request.form.get("comment", "").strip()
    complaint_code = request.form.get("complaint_code")

    if not comment_text:
        flash("Comment cannot be blank.", "error")
        return redirect(url_for("complaint_detail", complaint_id=complaint_code))

    database.add_complaint_comment(
        complaint_db_id=complaint_db_id,
        user_id=session["user_id"],
        comment_text=comment_text
    )
    flash("Update added successfully.", "success")
    return redirect(url_for("complaint_detail", complaint_id=complaint_code))

@app.route("/complaint/<int:complaint_db_id>/reopen", methods=["POST"])
@login_required
@student_required
def reopen_complaint(complaint_db_id):
    """Allows student to reopen a resolved complaint with an explanation."""
    reason = request.form.get("reason", "").strip()
    complaint_code = request.form.get("complaint_code")

    if not reason:
        reason = "Student indicated the issue is still unresolved and reopened the ticket."
    else:
        reason = f"Reopened by student with reason: {reason}"

    database.update_complaint_status(
        complaint_db_id=complaint_db_id,
        new_status="Reopened",
        user_id=session["user_id"],
        comment_text=reason
    )
    flash(f"Complaint {complaint_code} has been reopened.", "info")
    return redirect(url_for("complaint_detail", complaint_id=complaint_code))

@app.route("/complaint/<int:complaint_db_id>/close", methods=["POST"])
@login_required
@student_required
def close_complaint(complaint_db_id):
    """Allows student to confirm resolution and close their complaint."""
    complaint_code = request.form.get("complaint_code")
    database.update_complaint_status(
        complaint_db_id=complaint_db_id,
        new_status="Closed",
        user_id=session["user_id"],
        comment_text="Issue confirmed resolved and closed by student."
    )
    flash(f"Complaint {complaint_code} has been closed. Thank you for using CampusFix!", "success")
    return redirect(url_for("complaint_detail", complaint_id=complaint_code))


# ==========================================================
# STAFF ROUTES
# ==========================================================

@app.route("/staff/dashboard")
@login_required
@staff_required
def staff_dashboard():
    """Staff dashboard showing assigned complaints and status summary."""
    staff_id = session["user_id"]
    stats = database.get_staff_dashboard_stats(staff_id)

    search = request.args.get("search", "").strip()
    status = request.args.get("status", "").strip()
    priority = request.args.get("priority", "").strip()

    assigned_complaints = database.get_staff_complaints(
        staff_id=staff_id,
        search_query=search,
        status_filter=status,
        priority_filter=priority
    )

    return render_template(
        "staff_dashboard.html",
        stats=stats,
        complaints=assigned_complaints,
        search=search,
        selected_status=status,
        selected_priority=priority
    )

@app.route("/staff/complaint/<int:complaint_db_id>/status", methods=["POST"])
@login_required
@staff_required
def staff_update_status(complaint_db_id):
    """Allows assigned staff member to update complaint status."""
    new_status = request.form.get("status", "").strip()
    complaint_code = request.form.get("complaint_code")
    comment_text = request.form.get("comment", "").strip()

    allowed_staff_statuses = ["Under Review", "In Progress", "Resolved"]
    if new_status not in allowed_staff_statuses:
        flash("Invalid status selected.", "error")
        return redirect(url_for("complaint_detail", complaint_id=complaint_code))

    note = f"Staff marked status as '{new_status}'."
    if comment_text:
        note += f" Note: {comment_text}"

    database.update_complaint_status(
        complaint_db_id=complaint_db_id,
        new_status=new_status,
        user_id=session["user_id"],
        comment_text=note
    )
    flash(f"Complaint {complaint_code} status updated to {new_status}.", "success")
    return redirect(url_for("complaint_detail", complaint_id=complaint_code))


# ==========================================================
# ADMIN ROUTES
# ==========================================================

@app.route("/admin/dashboard")
@login_required
@admin_required
def admin_dashboard():
    """Administrator dashboard with complete campus metrics."""
    stats = database.get_admin_dashboard_stats()
    # Recent complaints across all students
    recent_complaints = database.get_all_complaints()[:8]
    staff_members = database.get_staff_members()

    return render_template(
        "admin_dashboard.html",
        stats=stats,
        complaints=recent_complaints,
        staff_members=staff_members
    )

@app.route("/admin/complaints")
@login_required
@admin_required
def admin_complaints():
    """Complete list of campus complaints for administrative management."""
    search = request.args.get("search", "").strip()
    category = request.args.get("category", "").strip()
    status = request.args.get("status", "").strip()
    priority = request.args.get("priority", "").strip()

    all_complaints = database.get_all_complaints(
        search_query=search,
        category_filter=category,
        status_filter=status,
        priority_filter=priority
    )
    staff_members = database.get_staff_members()

    return render_template(
        "admin_complaints.html",
        complaints=all_complaints,
        staff_members=staff_members,
        search=search,
        selected_category=category,
        selected_status=status,
        selected_priority=priority
    )

@app.route("/admin/complaint/<int:complaint_db_id>/assign", methods=["POST"])
@login_required
@admin_required
def admin_assign_staff(complaint_db_id):
    """Assigns complaint to a staff member."""
    staff_id = request.form.get("staff_id", type=int)
    complaint_code = request.form.get("complaint_code")

    if not staff_id:
        flash("Please select a valid staff member.", "error")
        return redirect(url_for("complaint_detail", complaint_id=complaint_code))

    database.assign_complaint(complaint_db_id, staff_id, session["user_id"])
    flash(f"Complaint {complaint_code} has been assigned to staff member.", "success")
    return redirect(url_for("complaint_detail", complaint_id=complaint_code))

@app.route("/admin/complaint/<int:complaint_db_id>/priority", methods=["POST"])
@login_required
@admin_required
def admin_update_priority(complaint_db_id):
    """Changes priority of a complaint."""
    new_priority = request.form.get("priority", "").strip()
    complaint_code = request.form.get("complaint_code")

    if new_priority in PRIORITY_LEVELS:
        database.update_complaint_priority(complaint_db_id, new_priority, session["user_id"])
        flash(f"Complaint {complaint_code} priority changed to {new_priority}.", "success")
    return redirect(url_for("complaint_detail", complaint_id=complaint_code))

@app.route("/admin/complaint/<int:complaint_db_id>/status", methods=["POST"])
@login_required
@admin_required
def admin_update_status(complaint_db_id):
    """Admin overrides complaint status."""
    new_status = request.form.get("status", "").strip()
    complaint_code = request.form.get("complaint_code")
    comment_text = request.form.get("comment", "").strip()

    note = f"Administrator changed status to '{new_status}'."
    if comment_text:
        note += f" Note: {comment_text}"

    database.update_complaint_status(
        complaint_db_id=complaint_db_id,
        new_status=new_status,
        user_id=session["user_id"],
        comment_text=note
    )
    flash(f"Complaint {complaint_code} status updated to {new_status}.", "success")
    return redirect(url_for("complaint_detail", complaint_id=complaint_code))

@app.route("/admin/users")
@login_required
@admin_required
def admin_users():
    """List of all registered campus users (students, staff, admins)."""
    users = database.get_all_users()
    return render_template("admin_users.html", users=users)


# ==========================================================
# NOTIFICATIONS & PROFILE
# ==========================================================

@app.route("/notifications")
@login_required
def notifications():
    """View in-app notifications for logged-in user."""
    user_id = session["user_id"]
    notifs = database.get_user_notifications(user_id)
    return render_template("notifications.html", notifications=notifs)

@app.route("/notifications/read/<int:notification_id>", methods=["POST"])
@login_required
def mark_notification_read(notification_id):
    """Mark single notification as read."""
    database.mark_notification_as_read(notification_id, session["user_id"])
    return redirect(request.referrer or url_for("notifications"))

@app.route("/notifications/read-all", methods=["POST"])
@login_required
def mark_all_notifications_read():
    """Mark all notifications as read for current user."""
    database.mark_all_notifications_as_read(session["user_id"])
    flash("All notifications marked as read.", "info")
    return redirect(url_for("notifications"))

@app.route("/profile")
@login_required
def profile():
    """Display user profile information."""
    user = database.get_user_by_id(session["user_id"])
    if not user:
        abort(404)
    return render_template("profile.html", user=user)

@app.route("/uploads/<filename>")
def uploaded_file(filename):
    """Securely serve uploaded images."""
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)


# ==========================================================
# ERROR HANDLERS
# ==========================================================

@app.errorhandler(404)
def page_not_found(e):
    return render_template("404.html"), 404

@app.errorhandler(403)
def access_forbidden(e):
    return render_template("403.html"), 403


# ==========================================================
# MAIN EXECUTION
# ==========================================================

if __name__ == "__main__":
    # Ensure database is initialized before starting server
    database.init_db()
    # Bind to 0.0.0.0 and port 3000 as required by environment
    port = int(os.environ.get("PORT", 3000))
    print(f"Starting CampusFix Flask Application on http://0.0.0.0:{port}...")
    app.run(host="0.0.0.0", port=port, debug=True)
