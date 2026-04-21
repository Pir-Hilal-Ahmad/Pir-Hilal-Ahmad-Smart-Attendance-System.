from flask import Flask, render_template, request, redirect, session, jsonify, flash
import sqlite3, os
from werkzeug.utils import secure_filename
from functools import wraps
from datetime import datetime, date
from flask_mail import Mail, Message
from itsdangerous import URLSafeTimedSerializer
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash, check_password_hash
from flask import session, request, redirect, render_template

# ---------------- ENV ----------------
load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY") or "fallback_secret_key"

# ---------------- MAIL ----------------
app.config.update(
    MAIL_SERVER='smtp.gmail.com',
    MAIL_PORT=587,
    MAIL_USE_TLS=True,
    MAIL_USERNAME=os.environ.get("MAIL_USERNAME"),
    MAIL_PASSWORD=os.environ.get("MAIL_PASSWORD")
)

mail = Mail(app)

# ---------------- TOKEN ----------------
serializer = URLSafeTimedSerializer(str(app.secret_key))

# ---------------- PATHS ----------------
DB = "attendance.db"
UPLOAD_FOLDER = "static/uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER


# ---------------- DB ----------------
def init_db():
    conn = sqlite3.connect(DB)
    cur = conn.cursor()

    cur.execute("CREATE TABLE IF NOT EXISTS users (username TEXT, password TEXT, role TEXT, email TEXT)")
    cur.execute("CREATE TABLE IF NOT EXISTS user_permissions (username TEXT, permission TEXT)")

    cur.execute("""
    CREATE TABLE IF NOT EXISTS students (
        id TEXT, name TEXT, semester TEXT,
        subjects TEXT, photo TEXT,
        department TEXT, reg_no TEXT
    )""")

    cur.execute("""
    CREATE TABLE IF NOT EXISTS pending_students (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT, parentage TEXT, semester TEXT,
        subjects TEXT, department TEXT,
        phone TEXT, email TEXT,
        username TEXT, password TEXT, photo TEXT
    )""")

    cur.execute("""
    CREATE TABLE IF NOT EXISTS pending_updates (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id TEXT, name TEXT, department TEXT,
        phone TEXT, email TEXT, username TEXT,
        password TEXT, reg_no TEXT
    )""")

    cur.execute("""
    CREATE TABLE IF NOT EXISTS attendance (
        student_id TEXT, subject TEXT,
        semester TEXT, date TEXT, status TEXT
    )""")

    cur.execute("""
    CREATE TABLE IF NOT EXISTS notifications (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        message TEXT, media TEXT,
        category TEXT, downloads INTEGER DEFAULT 0,
        created_at TEXT
    )""")
    cur.execute("""
CREATE TABLE IF NOT EXISTS subjects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    department TEXT,
    semester TEXT
)
""")
    


    # default users
    cur.execute("INSERT OR IGNORE INTO users VALUES (?,?,?,?)",
                ("admin", generate_password_hash("123"), "admin", "admin@gmail.com"))

    cur.execute("INSERT OR IGNORE INTO users VALUES (?,?,?,?)",
                ("teacher", generate_password_hash("123"), "teacher", "teacher@gmail.com"))
    

    try:
        cur.execute("ALTER TABLE subjects ADD COLUMN department TEXT")
    except:
        pass

    try:
        cur.execute("ALTER TABLE subjects ADD COLUMN semester TEXT")
    except:
        pass

    try:
        cur.execute("ALTER TABLE pending_updates ADD COLUMN subjects TEXT")
    except:
        pass

    try:
        from flask_mail import Mail, Message
    except:
        Mail= None
        Message= None

    conn.commit()
    conn.close()


# ---------------- PERMISSION ----------------
def permission_required(permission):
    def wrapper(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if permission not in session.get("permissions", []):
                return "❌ Access Denied"
            return f(*args, **kwargs)
        return decorated
    return wrapper


# ---------------- HOME ----------------
@app.route("/")
def home():
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    notes = cur.execute("""
        SELECT message, created_at
        FROM notifications
        ORDER BY id DESC
    """).fetchall()

    conn.close()

    return render_template("home.html", notes=notes)


# ---------------- LOGIN ----------------
@app.route("/login/<role>", methods=["GET","POST"])
def login_role(role):

    if request.method == "POST":
        u = request.form.get("username")
        p = request.form.get("password")

        conn = sqlite3.connect(DB)
        cur = conn.cursor()

        cur.execute("""
        SELECT username, password, role 
        FROM users 
        WHERE username=?
        """, (u,))

        res = cur.fetchone()

        if res and check_password_hash(res[1], p) and res[2] == role:

            perms = cur.execute("""
            SELECT permission FROM user_permissions WHERE username=?
            """, (u,)).fetchall()

            session["permissions"] = [x[0] for x in perms]
            session["user"] = u
            session["role"] = role

            conn.close()
            return redirect(f"/{role}")

        else:
            conn.close()
            flash("Invalid username, password or role")

    return render_template("login_role.html", role=role)
# ---------------- FORGOT PASSWORD ----------------
@app.route("/forgot", methods=["GET","POST"])
def forgot():
    if request.method == "POST":
        username = request.form.get("username")
        email = request.form.get("email")

        conn = sqlite3.connect(DB)
        cur = conn.cursor()

        user = cur.execute("SELECT * FROM users WHERE username=? AND email=?", (username, email)).fetchone()
        conn.close()

        if user:
            token = serializer.dumps(email, salt="reset-password")
            link = f"http://127.0.0.1:5000/reset/{token}"

            msg = Message("Password Reset",
                          sender=app.config['MAIL_USERNAME'],
                          recipients=[email])

            msg.body = f"Click to reset password:\n{link}"
            mail.send(msg)

            flash("Reset link sent")
        else:
            flash("Invalid details")

    return render_template("forgot.html")


# ---------------- RESET PASSWORD ----------------
@app.route("/reset/<token>", methods=["GET", "POST"])
def reset_token(token):
    try:
        email = serializer.loads(token, salt="reset-password", max_age=3600)
    except:
        return "Invalid or expired link"

    if request.method == "POST":
        new_password = request.form.get("password")

        if not new_password or len(new_password) < 6:
            flash("Password must be 6+ chars")
            return redirect(request.url)

        hashed = generate_password_hash(new_password)

        conn = sqlite3.connect(DB)
        cur = conn.cursor()
        cur.execute("UPDATE users SET password=? WHERE email=?", (hashed, email))
        conn.commit()
        conn.close()

        flash("Password updated")
        return redirect("/")

    return render_template("reset_password.html")


# ---------------- ADMIN ----------------
# @app.route("/admin", methods=["GET","POST"])
# def admin():
#     conn = sqlite3.connect(DB)
#     cur = conn.cursor()



#     if request.method == "POST":

#         msg = request.form.get("message")
#         cur.execute("INSERT INTO notifications (message, created_at) VALUES (?,?)",
#                     (msg, str(datetime.now())))
#         conn.commit()

#     pending = cur.execute("SELECT * FROM pending_students").fetchall()
#     students = cur.execute("SELECT * FROM students").fetchall()

#     conn.close()


#     action = request.form.get("action")

#     if action == "add_subject":
#         name = request.form.get("subject_name")
#         dept = request.form.get("department")
#         sem = request.form.get("semester")

#         cur.execute("""
#             INSERT INTO subjects (name, department, semester)
#             VALUES (?,?,?)
#         """, (name, dept, sem))

#     conn.commit()

#     return render_template("admin.html", pending=pending, students=students)


@app.route("/admin", methods=["GET", "POST"])
def admin():
    conn = sqlite3.connect(DB)
    cur = conn.cursor()

    if request.method == "POST":
        action = request.form.get("action")

        if action == "add_notification":
            msg = request.form.get("message")

            cur.execute("""
                INSERT INTO notifications (message, created_at)
                VALUES (?,?)
            """, (msg, str(datetime.now())))

            conn.commit()

        if action == "add_subject":
            name = request.form.get("subject_name")
            dept = request.form.get("department")
            sem = request.form.get("semester")

            cur.execute("""
                INSERT INTO subjects (name, department, semester)
                VALUES (?,?,?)
            """, (name, dept, sem))

            conn.commit()

    # ✅ FETCH DATA BEFORE CLOSING
    pending = cur.execute("SELECT * FROM pending_students").fetchall()
    students = cur.execute("SELECT * FROM students").fetchall()
    updates = cur.execute("SELECT * FROM pending_updates").fetchall()
    notifications = cur.execute("SELECT * FROM notifications").fetchall()

    conn.close()  # ✅ CLOSE AT END ONLY

    return render_template(
        "admin.html",
        pending=pending,
        students=students,
        updates=updates,
        notifications=notifications
    )

# @app.route("/approve/<int:id>")
# def approve(id):
#     conn = sqlite3.connect(DB)
#     cur = conn.cursor()

#     student = cur.execute(
#         "SELECT * FROM pending_students WHERE id=?", (id,)
#     ).fetchone()

#     if student:
#         # insert into students table
#         cur.execute("""
#         INSERT INTO students (id, name, semester, subjects, photo, department, reg_no)
#         VALUES (?,?,?,?,?,?,?)
#         """, (
#             student[8],  # username as ID
#             student[1],
#             student[3],
#             student[4],
#             student[10],
#             student[5],
#             student[6]
#         ))

#         # insert into users
#         cur.execute("""
#         INSERT INTO users (username, password, role, email)
#         VALUES (?,?,?,?)
#         """, (
#             student[8],
#             student[9],
#             "student",
#             student[7]
#         ))

#         # delete from pending
#         cur.execute("DELETE FROM pending_students WHERE id=?", (id,))

#         conn.commit()

#     conn.close()
#     return redirect("/admin")


# ---------------- REGISTER ----------------
@app.route("/register", methods=["GET","POST"])
def register():

    conn = sqlite3.connect(DB)
    cur = conn.cursor()

    subjects = []

    if request.method == "POST":

        file = request.files.get("photo")
        filename = "default.png"

        if file and file.filename:
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))

        subjects_str = ",".join(request.form.getlist("subjects"))

        data = (
            request.form.get("name"),
            request.form.get("parentage"),
            request.form.get("semester"),
            subjects_str,
            request.form.get("department"),
            request.form.get("phone"),
            request.form.get("email"),
            request.form.get("username"),
            generate_password_hash(request.form.get("password")),
            filename
        )

        cur.execute("""
        INSERT INTO pending_students
        (name,parentage,semester,subjects,department,phone,email,username,password,photo)
        VALUES (?,?,?,?,?,?,?,?,?,?)
        """, data)

        conn.commit()
        conn.close()

        flash("Registered successfully")
        return redirect("/register")

    conn.close()
    return render_template("register.html", subjects=subjects)


@app.route("/get_subjects_register")
def get_subjects_register():
    dept = request.args.get("department")
    sem = request.args.get("semester")

    conn = sqlite3.connect(DB)
    cur = conn.cursor()

    rows = cur.execute("""
        SELECT name FROM subjects
        WHERE department=? AND semester=?
    """, (dept, sem)).fetchall()

    conn.close()

    return jsonify([r[0] for r in rows])


# ---------------- STUDENT ----------------
@app.route("/student")
def student():
    if "user" not in session:
        return redirect("/")

    sid = session.get("user")

    conn = sqlite3.connect(DB)
    cur = conn.cursor()

    # ---------------- ATTENDANCE ----------------
    records = cur.execute("""
        SELECT date, subject, status
        FROM attendance
        WHERE student_id=?
        ORDER BY date DESC
    """, (sid,)).fetchall()

    # ---------------- SUBJECT LIST ----------------
    subjects_raw = cur.execute("""
        SELECT DISTINCT subject FROM attendance
        WHERE student_id=?
    """, (sid,)).fetchall()

    subjects_list = [s[0] for s in subjects_raw]

    # ---------------- SUBJECT ANALYTICS ----------------
    subject_data = {}

    for sub in subjects_list:
        total = cur.execute("""
            SELECT COUNT(*) FROM attendance
            WHERE student_id=? AND subject=?
        """, (sid, sub)).fetchone()[0]

        present = cur.execute("""
            SELECT COUNT(*) FROM attendance
            WHERE student_id=? AND subject=? AND status='P'
        """, (sid, sub)).fetchone()[0]

        subject_data[sub] = {
            "total": total,
            "present": present
        }

    # ---------------- PHOTO ----------------
    student_row = cur.execute("""
        SELECT photo FROM students WHERE id=?
    """, (sid,)).fetchone()

    photo = student_row[0] if student_row else None

    conn.close()

    return render_template(
        "student.html",
        records=records,
        subjects=subjects_list,
        subject_data=subject_data,
        photo=photo
    )

@app.route("/approve/<int:id>")
def approve(id):
    conn = sqlite3.connect(DB)
    cur = conn.cursor()

    student = cur.execute(
        "SELECT * FROM pending_students WHERE id=?", (id,)
    ).fetchone()

    if student:
        cur.execute("""
        INSERT INTO students (id, name, semester, subjects, photo, department, reg_no)
        VALUES (?,?,?,?,?,?,?)
        """, (
            student[8],
            student[1],
            student[3],
            student[4],
            student[10],
            student[5],
            student[6]
        ))

        cur.execute("""
        INSERT INTO users (username, password, role, email)
        VALUES (?,?,?,?)
        """, (
            student[8],
            student[9],
            "student",
            student[7]
        ))

        cur.execute("DELETE FROM pending_students WHERE id=?", (id,))
        conn.commit()

    conn.close()
    return redirect("/admin")

@app.route("/approve_update/<int:id>")
def approve_update(id):
    conn = sqlite3.connect(DB)
    cur = conn.cursor()

    # get update request
    u = cur.execute("SELECT * FROM pending_updates WHERE id=?", (id,)).fetchone()

    if u:
        # ✅ update student data
        cur.execute("""
        UPDATE students SET
            name=?,
            department=?,
            reg_no=?,
            subjects=?
        WHERE id=?
        """, (u[2], u[3], u[8], u[9], u[1]))

        # ✅ update user data
        cur.execute("""
        UPDATE users SET
            username=?,
            password=?,
            email=?
        WHERE username=?
        """, (u[6], u[7], u[5], u[0]))

        # ✅ remove request
        cur.execute("DELETE FROM pending_updates WHERE id=?", (id,))

        conn.commit()

    conn.close()
    return redirect("/admin")


@app.route("/reject_update/<int:id>")
def reject_update(id):
    conn = sqlite3.connect(DB)
    cur = conn.cursor()

    cur.execute("DELETE FROM pending_updates WHERE id=?", (id,))
    conn.commit()
    conn.close()

    return redirect("/admin")



@app.route("/update_profile", methods=["GET", "POST"])
def update_profile():

    subjects_list = request.form.getlist("subjects")
    subjects = ",".join(subjects_list)

    if "user" not in session:
        return redirect("/")

    sid = session.get("user")

    conn = sqlite3.connect(DB)
    cur = conn.cursor()

    if request.method == "POST":
        cur.execute("""
INSERT INTO pending_updates
(student_id,name,department,phone,email,username,password,reg_no,subjects)
VALUES (?,?,?,?,?,?,?,?,?)
""", (
    sid,
    request.form.get("name"),
    request.form.get("department"),
    request.form.get("phone"),
    request.form.get("email"),
    request.form.get("username"),
    request.form.get("password"),
    request.form.get("reg_no"),
    subjects   # ✅ from checkbox
))

        conn.commit()
        flash("Update request sent")

    student = cur.execute(
        "SELECT * FROM students WHERE id=?", (sid,)
    ).fetchone()

    conn.close()

    return render_template("update_profile.html", student=student)

# ---------------- TEACHER ----------------
@app.route("/teacher")
def teacher():
    return render_template("teacher.html")


@app.route("/get_students_smart")
def get_students_smart():
    dept = request.args.get("department")
    sem = request.args.get("semester")
    subject = request.args.get("subject")

    conn = sqlite3.connect(DB)
    cur = conn.cursor()

    rows = cur.execute("""
        SELECT id, name, reg_no, subjects 
        FROM students 
        WHERE department=? AND semester=?
    """, (dept, sem)).fetchall()

    filtered = []

    for sid, name, reg, subs in rows:
        if subs and subject.lower() in subs.lower():
            filtered.append((sid, name, reg))

    conn.close()

    return jsonify(filtered)




@app.route("/get_departments")
def get_departments():
    conn = sqlite3.connect(DB)
    cur = conn.cursor()

    rows = cur.execute("SELECT DISTINCT department FROM students").fetchall()

    conn.close()

    return jsonify([r[0] for r in rows if r[0]])


@app.route("/get_semesters")
def get_semesters():
    dept = request.args.get("department")

    conn = sqlite3.connect(DB)
    cur = conn.cursor()

    rows = cur.execute("""
        SELECT DISTINCT semester 
        FROM students 
        WHERE department=?
    """, (dept,)).fetchall()

    conn.close()

    return jsonify([r[0] for r in rows if r[0]])


@app.route("/submit_attendance", methods=["POST"])
def submit_attendance():
    subject = request.form.get("subject")
    semester = request.form.get("semester")

    conn = sqlite3.connect(DB)
    cur = conn.cursor()

    student_ids = request.form.getlist("student_ids")

    for sid in student_ids:
        status = request.form.get(f"status_{sid}")

        cur.execute("""
        INSERT INTO attendance (student_id, subject, semester, date, status)
        VALUES (?,?,?,?,?)
        """, (
            sid,
            subject,
            semester,
            str(date.today()),
            status
        ))

    conn.commit()
    conn.close()

    flash("✅ Attendance submitted successfully")
    return redirect("/teacher")



@app.route("/get_subjects")
def get_subjects():
    dept = request.args.get("department")
    sem = request.args.get("semester")

    

    conn = sqlite3.connect(DB)
    cur = conn.cursor()

    rows = cur.execute("""
        SELECT name FROM subjects
        WHERE department=? AND semester=?
    """, (dept, sem)).fetchall()

    

    conn.close()

    return jsonify([r[0] for r in rows])




@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = sqlite3.connect(DB)
        cur = conn.cursor()

        u = cur.execute(
            "SELECT * FROM users WHERE username=? AND password=?",
            (username, password)
        ).fetchone()

        conn.close()

        if u:
            session['username'] = u[1]   # username column
            return redirect("/home")
        else:
            return "Invalid Username or Password"

    return render_template("login.html")

# ---------------- LOGOUT ----------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


# ---------------- RUN ----------------
if __name__ == "__main__":
    init_db()
    app.run(debug=True)
