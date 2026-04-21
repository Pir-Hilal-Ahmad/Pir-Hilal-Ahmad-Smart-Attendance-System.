🎓 Smart Attendance System (Flask + SQLite)

A web-based Smart Attendance System built using Flask (Python) and SQLite, designed for managing student attendance efficiently with role-based access for Admin, Teacher, and Students.

---

🚀 Features

- 🔐 User Authentication (Admin / Teacher / Student)
- 📝 Student Registration & Approval System
- 📊 Attendance Marking by Teachers
- 🧾 Subject & Department Management
- 🔄 Profile Update Approval Workflow
- 📋 View Attendance Records
- 🎯 Clean UI with responsive design
- ⚠️ Notification banner for system updates

---

🛠️ Tech Stack

- Backend: Flask (Python)
- Database: SQLite
- Frontend: HTML, CSS, Bootstrap
- Deployment: Render (Gunicorn)

---

📂 Project Structure

attendance_web/
│── app.py
│── database.db
│── requirements.txt
│
├── templates/
│   ├── index.html
│   ├── login.html
│   ├── admin.html
│   ├── teacher.html
│   └── student.html
│
├── static/
│   ├── css/
│   └── js/

---

⚙️ Installation & Setup

🔹 1. Clone Repository

git clone https://github.com/your-username/attendance-system.git
cd attendance-system

---

🔹 2. Create Virtual Environment

python -m venv venv
source venv/bin/activate   # Linux/Mac
venv\Scripts\activate      # Windows

---

🔹 3. Install Dependencies

pip install -r requirements.txt

---

🔹 4. Run Application

python app.py

Then open:

http://127.0.0.1:5000/

---

🌐 Deployment (Render)

1. Push code to GitHub
2. Connect repository to Render
3. Set build command:

pip install -r requirements.txt

4. Set start command:

gunicorn app:app

---

⚠️ Notes

- Forgot Password feature is under development
- Ensure correct credentials while logging in
- SQLite is used (not recommended for large-scale production)

---

🔮 Future Improvements

- 🔐 Password Reset via Email
- 📱 Mobile Responsive UI Enhancements
- 🗄️ Migration to PostgreSQL
- 📊 Attendance Analytics Dashboard
- 🔔 Real-time Notifications

---

👨‍💻 Author

Pir Hilal Ahmad
📍 Jammu & Kashmir, India

---

📜 License

This project is for educational purposes.

---

⭐ Support

If you like this project, give it a ⭐ on GitHub!