from flask import Flask, render_template, request, redirect, url_for, flash, session
import sqlite3
from sqlite3 import IntegrityError
from werkzeug.security import generate_password_hash, check_password_hash
app = Flask(__name__)
app.secret_key = "student_management_secret_key"
def init_db():
    connection = sqlite3.connect("students.db")
    cursor = connection.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            age INTEGER NOT NULL,
            major TEXT NOT NULL,
            email text unique
        )
    """)
    cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    password TEXT NOT NULL
)
""")
    connection.commit()
    connection.close()

init_db()

@app.route("/", methods=["GET", "POST"])
def home():
    if "user" not in session:
        return redirect(url_for("login"))
    if request.method == "POST":
        name = request.form["name"]
        age = request.form["age"]
        major = request.form["major"]
        email = request.form["email"]
        connection = sqlite3.connect("students.db")
        cursor = connection.cursor()

        try:
         cursor.execute(
        "INSERT INTO students (name, age, major, email) VALUES (?, ?, ?, ?)",
        (name, age, major, email)
    )

         connection.commit()
         connection.close()
         flash("Student added successfully!", "success")
         return redirect(url_for("home"))

        except IntegrityError:
         connection.close()
         flash("This email already exists!", "error")
         return redirect(url_for("home"))

    search = request.args.get("search", "")

    connection = sqlite3.connect("students.db")
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()

    if search:
        cursor.execute(
            "SELECT * FROM students WHERE name LIKE ? OR email LIKE ?",
("%" + search + "%", "%" + search + "%")
        )
    else:
        cursor.execute("SELECT * FROM students")

    students = cursor.fetchall()
    total_students = len(students)
    connection.close()
    return render_template(
        "index.html",
        students=students,
        search=search,
        total_students=total_students
    )
@app.route("/delete/<int:id>")
def delete_student(id):

    connection = sqlite3.connect("students.db")
    cursor = connection.cursor()

    cursor.execute(
        "DELETE FROM students WHERE id = ?",
        (id,)
    )

    connection.commit()
    connection.close()
    flash("Student deleted successfully!", "success")
    return redirect(url_for("home"))


@app.route("/edit/<int:id>", methods=["GET", "POST"])
def edit_student(id):
    if "user" not in session:
     return redirect(url_for("login"))
    connection = sqlite3.connect("students.db")
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()

    if request.method == "POST":

        name = request.form["name"]
        age = request.form["age"]
        major = request.form["major"]
        email = request.form["email"]

        try:
         cursor.execute(
        """
         UPDATE students
         SET name = ?, age = ?, major = ?, email = ?
         WHERE id = ?
        """,
         (name, age, major, email, id)
    )

         connection.commit()
         connection.close()
         flash("Student updated successfully!", "success")
         return redirect(url_for("home"))

        except IntegrityError:
         connection.close()
        flash("This email already exists!", "error")
        return redirect(url_for("home"))

    cursor.execute(
        "SELECT * FROM students WHERE id = ?",
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

@app.route("/register", methods=["GET", "POST"])
def register():
    if "user" in session:
        return redirect(url_for("home"))
    if request.method == "POST":
        username = request.form["username"]
        email = request.form["email"]
        password = request.form["password"]
        password = generate_password_hash(password)
        connection = sqlite3.connect("students.db")
        cursor = connection.cursor()

        try:
            cursor.execute(
                "INSERT INTO users (username, email, password) VALUES (?, ?, ?)",
                (username, email, password)
            )

            connection.commit()
            connection.close()

            flash("Registration successful!", "success")
            return redirect(url_for("register"))

        except IntegrityError:
            connection.close()
            flash("Email already exists!", "error")
            return redirect(url_for("register"))

    return render_template("register.html")
@app.route("/login", methods=["GET", "POST"])
def login():
    if "user" in session:
        return redirect(url_for("home"))

    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        connection = sqlite3.connect("students.db")
        connection.row_factory = sqlite3.Row
        cursor = connection.cursor()

        cursor.execute(
            "SELECT * FROM users WHERE email = ?",
            (email,)
        )

        user = cursor.fetchone()
        connection.close()

        if user and check_password_hash(user["password"], password):
            session["user"] = user["username"]
            flash("Login successful!", "success")
            return redirect(url_for("home"))
        else:
            flash("Invalid email or password!", "error")
            return redirect(url_for("login"))

    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    flash("Logged out successfully!", "success")
    return redirect(url_for("login"))

@app.route("/about")
def about():
    if "user" not in session:
        return redirect(url_for("login"))

    return render_template("about.html")

@app.route("/contact")
def contact():
    if "user" not in session:
        return redirect(url_for("login"))

    return render_template("contact.html")
if __name__ == "__main__":
    app.run(debug=True)