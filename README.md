# 🎓 Student Management System

A full-stack web-based Student Management System built with Python and Flask.

The application provides a modern interface for managing student records, user accounts, authentication, role-based access control, dashboard analytics, and account settings.

## 🚀 Live Demo

Coming soon.

## ✨ Features

### 🔐 Authentication & Authorization

- User registration
- Secure login and logout
- Password hashing
- Session-based authentication
- Admin and Viewer roles
- Protected administrative actions
- Administrator registration code

### 👨‍🎓 Student Management

- Add new students
- View student records
- Edit student information
- Delete students
- Upload student photos
- Search students by name or email
- Sort students A–Z / Z–A
- Prevent duplicate student emails
- Input validation

### 📊 Dashboard & Analytics

- Total students
- Total majors
- Average student age
- Students by major
- Interactive charts using Chart.js
- Responsive dashboard

### 👤 Account Management

- Profile avatar
- Upload custom avatar
- Change email address
- Change password
- Gender-based default avatars

### ⚙️ User Experience

- Light and Dark Mode
- English / Arabic interface
- Notification preferences
- Smooth animations
- Page transitions
- Responsive design
- Modern glassmorphism-inspired UI

### 📄 Data Management

- Export student records to CSV
- SQLite database

## 🛠️ Technologies Used

### Backend

- Python
- Flask
- SQLite
- Werkzeug

### Frontend

- HTML5
- CSS3
- JavaScript
- Bootstrap 5
- Font Awesome
- Chart.js

### Tools

- Git
- GitHub

## 📂 Project Structure

```text
Student-Management-System/
│
├── app.py
├── main.py
├── requirements.txt
├── .gitignore
├── .env.example
├── README.md
├── students.json
│
├── templates/
│   ├── base.html
│   ├── index.html
│   ├── login.html
│   ├── register.html
│   ├── edit.html
│   ├── settings.html
│   ├── change_email.html
│   ├── change_password.html
│   ├── about.html
│   └── contact.html
│
└── static/
    ├── style.css
    └── uploads/
        ├── male-avatar.png
        └── female-avatar.png