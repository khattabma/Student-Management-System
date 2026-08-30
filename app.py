from flask import Flask, render_template, request, redirect, url_for, flash, session, Response
from dotenv import load_dotenv
import sqlite3
import csv
import re
import os
from io import StringIO
from sqlite3 import IntegrityError
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
load_dotenv()

app = Flask(__name__)

# ==========================================================
# SECURITY CONFIGURATION
# ==========================================================

# Use an environment variable in production.
# A temporary random key is generated if none is provided.
app.secret_key = os.environ.get("SECRET_KEY") or os.urandom(32).hex()

# Admin code must never be hard-coded in the source code.
ADMIN_CODE = os.environ.get("ADMIN_CODE")


# ==========================================================
# PATHS
# ==========================================================

DATABASE_PATH = os.path.join(app.root_path, "students.db")

UPLOAD_FOLDER = os.path.join(
    app.root_path,
    "static",
    "uploads"
)

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

os.makedirs(UPLOAD_FOLDER, exist_ok=True)


# ==========================================================
# DATABASE
# ==========================================================

def init_db():

    connection = sqlite3.connect(DATABASE_PATH)
    cursor = connection.cursor()

    # Students table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            age INTEGER NOT NULL,
            major TEXT NOT NULL,
            email TEXT UNIQUE,
            photo TEXT
        )
    """)

    # Users table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL,
            gender TEXT DEFAULT 'male',
            avatar TEXT DEFAULT 'male-avatar.png'
        )
    """)

    # Add role column if it does not exist
    cursor.execute("PRAGMA table_info(users)")
    columns = [column[1] for column in cursor.fetchall()]

    if "role" not in columns:
        cursor.execute(
            "ALTER TABLE users ADD COLUMN role TEXT DEFAULT 'viewer'"
        )

    connection.commit()
    connection.close()


init_db()


# ==========================================================
# HOME / DASHBOARD
# ==========================================================

@app.route("/", methods=["GET", "POST"])
def home():

    if "user" not in session:
        return redirect(url_for("login"))

    # ------------------------------------------------------
    # ADD STUDENT
    # ------------------------------------------------------

    if request.method == "POST":

        if session.get("role") != "admin":
            flash(
                "Only administrators can add students.",
                "error"
            )
            return redirect(url_for("home"))

        name = request.form.get("name", "").strip()
        age = request.form.get("age", "").strip()
        major = request.form.get("major", "").strip()
        email = request.form.get("email", "").strip()
        photo = request.files.get("photo")

        # Name validation
        if len(name) < 3:
            flash(
                "Student name must be at least 3 characters.",
                "error"
            )
            return redirect(url_for("home"))

        # Age validation
        if not age.isdigit():
            flash(
                "Age must be a number.",
                "error"
            )
            return redirect(url_for("home"))

        age = int(age)

        if age < 16 or age > 100:
            flash(
                "Age must be between 16 and 100.",
                "error"
            )
            return redirect(url_for("home"))

        # Major validation
        if not major:
            flash(
                "Major is required.",
                "error"
            )
            return redirect(url_for("home"))

        # Email validation
        email_pattern = (
            r"^[A-Za-z0-9._%+-]+"
            r"@[A-Za-z0-9.-]+\."
            r"[A-Za-z]{2,}$"
        )

        if not re.match(email_pattern, email):
            flash(
                "Please enter a valid email address.",
                "error"
            )
            return redirect(url_for("home"))

        # --------------------------------------------------
        # STUDENT PHOTO
        # --------------------------------------------------

        filename = ""

        if photo and photo.filename:

            filename = secure_filename(photo.filename)

            photo.save(
                os.path.join(
                    app.config["UPLOAD_FOLDER"],
                    filename
                )
            )

        # --------------------------------------------------
        # DATABASE INSERT
        # --------------------------------------------------

        connection = sqlite3.connect(DATABASE_PATH)
        cursor = connection.cursor()

        try:

            cursor.execute(
                """
                INSERT INTO students
                (name, age, major, email, photo)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    name,
                    age,
                    major,
                    email,
                    filename
                )
            )

            connection.commit()
            connection.close()

            flash(
                "Student added successfully!",
                "success"
            )

            return redirect(url_for("home"))

        except IntegrityError:

            connection.close()

            flash(
                "This email already exists!",
                "error"
            )

            return redirect(url_for("home"))

    # ------------------------------------------------------
    # SEARCH / SORT
    # ------------------------------------------------------

    search = request.args.get("search", "").strip()
    sort = request.args.get("sort", "asc")

    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row

    cursor = connection.cursor()

    if search:

        cursor.execute(
            """
            SELECT *
            FROM students
            WHERE name LIKE ?
               OR email LIKE ?
            """,
            (
                "%" + search + "%",
                "%" + search + "%"
            )
        )

    else:

        if sort == "desc":

            cursor.execute(
                """
                SELECT *
                FROM students
                ORDER BY name DESC
                """
            )

        else:

            cursor.execute(
                """
                SELECT *
                FROM students
                ORDER BY name ASC
                """
            )

    students = cursor.fetchall()

    # ------------------------------------------------------
    # DASHBOARD STATISTICS
    # ------------------------------------------------------

    major_counts = {}

    for student in students:

        major = student["major"]

        if major and major.strip():

            major_counts[major] = (
                major_counts.get(major, 0) + 1
            )

    majors_count = len(
        set(
            student["major"]
            for student in students
            if student["major"]
        )
    )

    ages = [
        student["age"]
        for student in students
        if student["age"]
    ]

    average_age = (
        round(sum(ages) / len(ages), 1)
        if ages
        else 0
    )

    total_students = len(students)

    connection.close()

    return render_template(
        "index.html",
        students=students,
        search=search,
        total_students=total_students,
        majors_count=majors_count,
        average_age=average_age,
        major_counts=major_counts
    )


# ==========================================================
# DELETE STUDENT
# ==========================================================

@app.route("/delete/<int:id>")
def delete_student(id):

    if "user" not in session:
        return redirect(url_for("login"))

    if session.get("role") != "admin":

        flash(
            "Only administrators can delete students.",
            "error"
        )

        return redirect(url_for("home"))

    connection = sqlite3.connect(DATABASE_PATH)
    cursor = connection.cursor()

    cursor.execute(
        "DELETE FROM students WHERE id = ?",
        (id,)
    )

    connection.commit()
    connection.close()

    flash(
        "Student deleted successfully!",
        "success"
    )

    return redirect(url_for("home"))


# ==========================================================
# EDIT STUDENT
# ==========================================================

@app.route("/edit/<int:id>", methods=["GET", "POST"])
def edit_student(id):

    if "user" not in session:
        return redirect(url_for("login"))

    if session.get("role") != "admin":

        flash(
            "Only administrators can edit students.",
            "error"
        )

        return redirect(url_for("home"))

    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row

    cursor = connection.cursor()

    if request.method == "POST":

        name = request.form.get("name", "").strip()
        age = request.form.get("age", "").strip()
        major = request.form.get("major", "").strip()
        email = request.form.get("email", "").strip()

        # Validation
        if len(name) < 3:

            connection.close()

            flash(
                "Student name must be at least 3 characters.",
                "error"
            )

            return redirect(
                url_for("edit_student", id=id)
            )

        if not age.isdigit():

            connection.close()

            flash(
                "Age must be a number.",
                "error"
            )

            return redirect(
                url_for("edit_student", id=id)
            )

        age = int(age)

        if age < 16 or age > 100:

            connection.close()

            flash(
                "Age must be between 16 and 100.",
                "error"
            )

            return redirect(
                url_for("edit_student", id=id)
            )

        if not major:

            connection.close()

            flash(
                "Major is required.",
                "error"
            )

            return redirect(
                url_for("edit_student", id=id)
            )

        email_pattern = (
            r"^[A-Za-z0-9._%+-]+"
            r"@[A-Za-z0-9.-]+\."
            r"[A-Za-z]{2,}$"
        )

        if not re.match(email_pattern, email):

            connection.close()

            flash(
                "Please enter a valid email address.",
                "error"
            )

            return redirect(
                url_for("edit_student", id=id)
            )

        try:

            cursor.execute(
                """
                UPDATE students
                SET name = ?,
                    age = ?,
                    major = ?,
                    email = ?
                WHERE id = ?
                """,
                (
                    name,
                    age,
                    major,
                    email,
                    id
                )
            )

            connection.commit()
            connection.close()

            flash(
                "Student updated successfully!",
                "success"
            )

            return redirect(url_for("home"))

        except IntegrityError:

            connection.close()

            flash(
                "This email already exists!",
                "error"
            )

            return redirect(
                url_for("edit_student", id=id)
            )

    cursor.execute(
        """
        SELECT *
        FROM students
        WHERE id = ?
        """,
        (id,)
    )

    student = cursor.fetchone()

    connection.close()

    if student is None:
        return redirect(url_for("home"))

    return render_template(
        "edit.html",
        student=student
    )


# ==========================================================
# REGISTER
# ==========================================================

@app.route("/register", methods=["GET", "POST"])
def register():

    if "user" in session:
        return redirect(url_for("home"))

    if request.method == "POST":

        username = request.form.get(
            "username",
            ""
        ).strip()

        email = request.form.get(
            "email",
            ""
        ).strip()

        password = request.form.get(
            "password",
            ""
        )

        gender = request.form.get(
            "gender",
            "male"
        )

        admin_code = request.form.get(
            "admin_code",
            ""
        ).strip()

        # --------------------------------------------------
        # VALIDATION
        # --------------------------------------------------

        if len(username) < 3:

            flash(
                "Username must be at least 3 characters.",
                "error"
            )

            return redirect(url_for("register"))

        email_pattern = (
            r"^[A-Za-z0-9._%+-]+"
            r"@[A-Za-z0-9.-]+\."
            r"[A-Za-z]{2,}$"
        )

        if not re.match(email_pattern, email):

            flash(
                "Please enter a valid email address.",
                "error"
            )

            return redirect(url_for("register"))

        if len(password) < 8:

            flash(
                "Password must be at least 8 characters long.",
                "error"
            )

            return redirect(url_for("register"))

        # --------------------------------------------------
        # DETERMINE ROLE
        # --------------------------------------------------

        if admin_code:

            if ADMIN_CODE and admin_code == ADMIN_CODE:

                role = "admin"

            else:

                flash(
                    "Invalid Admin Code.",
                    "error"
                )

                return redirect(
                    url_for("register")
                )

        else:

            role = "viewer"

        # --------------------------------------------------
        # AVATAR
        # --------------------------------------------------

        if gender == "female":

            avatar = "female-avatar.png"

        else:

            avatar = "male-avatar.png"

        # --------------------------------------------------
        # HASH PASSWORD
        # --------------------------------------------------

        hashed_password = generate_password_hash(
            password
        )

        # --------------------------------------------------
        # CREATE USER
        # --------------------------------------------------

        connection = sqlite3.connect(DATABASE_PATH)
        cursor = connection.cursor()

        try:

            cursor.execute(
                """
                INSERT INTO users
                (
                    username,
                    email,
                    password,
                    gender,
                    avatar,
                    role
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    username,
                    email,
                    hashed_password,
                    gender,
                    avatar,
                    role
                )
            )

            connection.commit()
            connection.close()

            flash(
                "Account created successfully! Please login.",
                "success"
            )

            return redirect(url_for("login"))

        except sqlite3.IntegrityError:

            connection.close()

            flash(
                "Email already exists!",
                "error"
            )

            return redirect(
                url_for("register")
            )

    return render_template("register.html")


# ==========================================================
# LOGIN
# ==========================================================

@app.route("/login", methods=["GET", "POST"])
def login():

    if "user" in session:
        return redirect(url_for("home"))

    if request.method == "POST":

        email = request.form.get(
            "email",
            ""
        ).strip()

        password = request.form.get(
            "password",
            ""
        )

        connection = sqlite3.connect(
            DATABASE_PATH
        )

        connection.row_factory = sqlite3.Row

        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT *
            FROM users
            WHERE email = ?
            """,
            (email,)
        )

        user = cursor.fetchone()

        connection.close()

        if user and check_password_hash(
            user["password"],
            password
        ):

            session["user"] = user["username"]
            session["avatar"] = user["avatar"]
            session["gender"] = user["gender"]
            session["role"] = user["role"]

            flash(
                "Login successful!",
                "success"
            )

            return redirect(
                url_for("home")
            )

        flash(
            "Invalid email or password!",
            "error"
        )

        return redirect(
            url_for("login")
        )

    return render_template("login.html")


# ==========================================================
# LOGOUT
# ==========================================================

@app.route("/logout")
def logout():

    session.clear()

    flash(
        "Logged out successfully!",
        "success"
    )

    return redirect(
        url_for("login")
    )


# ==========================================================
# ABOUT
# ==========================================================

@app.route("/about")
def about():

    if "user" not in session:
        return redirect(url_for("login"))

    return render_template(
        "about.html"
    )


# ==========================================================
# CONTACT
# ==========================================================

@app.route("/contact")
def contact():

    if "user" not in session:
        return redirect(url_for("login"))

    return render_template(
        "contact.html"
    )


# ==========================================================
# EXPORT CSV
# ==========================================================

@app.route("/export")
def export_students():

    if "user" not in session:
        return redirect(url_for("login"))

    connection = sqlite3.connect(
        DATABASE_PATH
    )

    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT name, age, major, email
        FROM students
        """
    )

    students = cursor.fetchall()

    connection.close()

    output = StringIO()

    writer = csv.writer(output)

    writer.writerow(
        [
            "Name",
            "Age",
            "Major",
            "Email"
        ]
    )

    for student in students:
        writer.writerow(student)

    response = Response(
        output.getvalue(),
        mimetype="text/csv"
    )

    response.headers[
        "Content-Disposition"
    ] = (
        "attachment; "
        "filename=students.csv"
    )

    return response


# ==========================================================
# SETTINGS
# ==========================================================

@app.route("/settings")
def settings():

    if "user" not in session:
        return redirect(url_for("login"))

    return render_template(
        "settings.html"
    )


# ==========================================================
# CHANGE AVATAR
# ==========================================================

@app.route(
    "/change_avatar",
    methods=["POST"]
)
def change_avatar():

    if "user" not in session:
        return redirect(url_for("login"))

    file = request.files.get("avatar")

    if not file or file.filename == "":

        flash(
            "Please select an image.",
            "warning"
        )

        return redirect(
            url_for("settings")
        )

    filename = secure_filename(
        file.filename
    )

    file.save(
        os.path.join(
            app.config["UPLOAD_FOLDER"],
            filename
        )
    )

    connection = sqlite3.connect(
        DATABASE_PATH
    )

    cursor = connection.cursor()

    cursor.execute(
        """
        UPDATE users
        SET avatar = ?
        WHERE username = ?
        """,
        (
            filename,
            session["user"]
        )
    )

    connection.commit()
    connection.close()

    session["avatar"] = filename

    flash(
        "Avatar updated successfully!",
        "success"
    )

    return redirect(
        url_for("settings")
    )


# ==========================================================
# CHANGE EMAIL
# ==========================================================

@app.route(
    "/change_email",
    methods=["GET", "POST"]
)
def change_email():

    if "user" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":

        new_email = request.form.get(
            "email",
            ""
        ).strip()

        email_pattern = (
            r"^[A-Za-z0-9._%+-]+"
            r"@[A-Za-z0-9.-]+\."
            r"[A-Za-z]{2,}$"
        )

        if not re.match(
            email_pattern,
            new_email
        ):

            flash(
                "Please enter a valid email address.",
                "error"
            )

            return redirect(
                url_for("change_email")
            )

        connection = sqlite3.connect(
            DATABASE_PATH
        )

        cursor = connection.cursor()

        try:

            cursor.execute(
                """
                UPDATE users
                SET email = ?
                WHERE username = ?
                """,
                (
                    new_email,
                    session["user"]
                )
            )

            connection.commit()
            connection.close()

            flash(
                "Email updated successfully!",
                "success"
            )

            return redirect(
                url_for("settings")
            )

        except sqlite3.IntegrityError:

            connection.close()

            flash(
                "This email is already in use.",
                "error"
            )

            return redirect(
                url_for("change_email")
            )

    return render_template(
        "change_email.html"
    )


# ==========================================================
# CHANGE PASSWORD
# ==========================================================

@app.route(
    "/change_password",
    methods=["GET", "POST"]
)
def change_password():

    if "user" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":

        current_password = request.form.get(
            "current_password",
            ""
        )

        new_password = request.form.get(
            "new_password",
            ""
        )

        if len(new_password) < 8:

            flash(
                "New password must be at least 8 characters long.",
                "error"
            )

            return redirect(
                url_for("change_password")
            )

        connection = sqlite3.connect(
            DATABASE_PATH
        )

        connection.row_factory = sqlite3.Row

        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT password
            FROM users
            WHERE username = ?
            """,
            (session["user"],)
        )

        user = cursor.fetchone()

        if not user:

            connection.close()

            session.clear()

            return redirect(
                url_for("login")
            )

        if not check_password_hash(
            user["password"],
            current_password
        ):

            connection.close()

            flash(
                "Current password is incorrect!",
                "error"
            )

            return redirect(
                url_for("change_password")
            )

        hashed_password = generate_password_hash(
            new_password
        )

        cursor.execute(
            """
            UPDATE users
            SET password = ?
            WHERE username = ?
            """,
            (
                hashed_password,
                session["user"]
            )
        )

        connection.commit()
        connection.close()

        flash(
            "Password updated successfully!",
            "success"
        )

        return redirect(
            url_for("settings")
        )

    return render_template(
        "change_password.html"
    )


# ==========================================================
# RUN APPLICATION
# ==========================================================

if __name__ == "__main__":

    app.run(
        debug=True
    )