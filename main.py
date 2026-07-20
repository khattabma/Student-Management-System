from flask import Flask, render_template
import json
students = []
next_student_id = 1
FILE_NAME = "students.json"
def save_students():    
    with open(FILE_NAME, "w") as file:
        json.dump(students, file, indent=4)
def load_students():
    global students, next_student_id
    try:
        with open(FILE_NAME, "r") as file:
            students = json.load(file)

        if students:
            next_student_id = max(student["id"] for student in students) + 1

    except FileNotFoundError:
        students = []
def show_menu():
    print("=" * 40)
    print(" Student Management System ")
    print("=" * 40)
    print("1. Add Student")
    print("2. View Students")
    print("3. Search Student")
    print("4. Delete Student")
    print("5. Edit Student")
    print("6. Exit")
#load_students()
# while True:
#     show_menu()

#     choice = input("Choose an option: ")
#     if choice == "1":
#      name = input("Enter student name: ")
#      age = input("Enter student age: ")
#      major = input("Enter student major: ")

#      student = {
#         "id": next_student_id,
#         "name": name,
#         "age": age,
#         "major": major
#      }

#      students.append(student)
#      save_students()
#      next_student_id += 1

#      print("Student added successfully!")
#     elif choice == "2":
#         print("\nStudents List:")
#         if len(students) == 0:
#             print("No students found.")
#         else:
#             print("=" * 40)
#             for student in students:
#                 print(f"ID    : {student['id']}")
#                 print(f"Name  : {student['name']}")
#                 print(f"Age   : {student['age']}")
#                 print(f"Major : {student['major']}")
#                 print("-" * 40)
#     elif choice == "3":
#         name = input("Enter student name to search: ")
#         found = False

#         for student in students:
#             if student["name"] == name:
#                 print("Student found!")
#                 print(student)
#                 found = True
#                 break

#         if not found:
#             print("Student not found.")

#     elif choice == "4":
#         name = input("Enter student name to delete: ")

#         found = False

#         for student in students:
#             if student["name"] == name:
#                 students.remove(student)
#                 save_students()
#                 print("Student deleted successfully!")
#                 found = True
#                 break

#         if not found:
#             print("Student not found.")
#     elif choice == "5":
#      name = input("Enter student name to edit: ")

#      found = False
#      for student in students:
#       if student["name"] == name:
#         found = True
#         student["name"] = input("Enter new name: ")
#         student["age"] = input("Enter new age: ")
#         student["major"] = input("Enter new major: ")
#         save_students()
#         print("Student updated successfully!")
#         break
#      if not found:
#       print("Student not found.")
#     elif choice == "6":
#          print("Goodbye!")
#          break

#     else:
#         print("Invalid option.")

#     print()
    app = Flask(__name__)

@app.route("/")
def home():
    return render_template("index.html")

if __name__ == "__main__":
    app.run(debug=True)