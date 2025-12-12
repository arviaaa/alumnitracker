
from flask import Flask, render_template, request, redirect, url_for, flash, session
import sqlite3

app = Flask(__name__)
app.secret_key = "supersecretkey"
DB_PATH = "alumni_tracker.db"

# -----------------------------
# DATABASE CONNECTION
# -----------------------------
def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# -----------------------------
# HELPER FUNCTIONS
# -----------------------------
def get_programs():
    conn = get_db_connection()
    programs = conn.execute("SELECT * FROM programs").fetchall()
    conn.close()
    return programs

def get_alumni():
    conn = get_db_connection()
    alumni = conn.execute("""
        SELECT a.*, p.program_name 
        FROM alumni a LEFT JOIN programs p 
        ON a.program_id = p.program_id
    """).fetchall()
    conn.close()
    return alumni

def get_announcements():
    conn = get_db_connection()
    announcements = conn.execute("""
        SELECT e.*, p.program_name 
        FROM events e LEFT JOIN programs p 
        ON e.program_id = p.program_id
    """).fetchall()
    conn.close()
    return announcements

def get_careers():
    conn = get_db_connection()
    careers = conn.execute("""
        SELECT c.*, a.first_name, a.last_name
        FROM careers c LEFT JOIN alumni a
        ON c.alumni_id = a.alumni_id
    """).fetchall()
    conn.close()
    return careers

# -----------------------------
# HOME PAGE
# -----------------------------
@app.route("/")
def index():
    return render_template("index.html")

# -----------------------------
# ADMIN ROUTES
# -----------------------------
@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = get_db_connection()
        admin = conn.execute("SELECT * FROM admin WHERE username = ?", (username,)).fetchone()
        conn.close()

        if admin and password == admin["password"]:  
            session["admin_logged_in"] = True
            session["admin_username"] = username
            flash("Logged in successfully!", "success")
            return redirect(url_for("admin_dashboard"))
        else:
            flash("Invalid username or password!", "danger")

    return render_template("admin_login.html")

@app.route("/admin/logout")
def admin_logout():
    session.clear()
    flash("Logged out successfully.", "info")
    return redirect(url_for("index"))

@app.route("/admin/dashboard")
def admin_dashboard():
    if not session.get("admin_logged_in"):
        flash("Please log in first.", "warning")
        return redirect(url_for("admin_login"))
    return render_template("admin_dashboard.html")

# # -----------------------------
# # ALUMNI ROUTES
# # -----------------------------
# @app.route("/alumni")
# def alumni():
#     alumni_list = get_alumni()
#     return render_template("alumni.html", alumni=alumni_list)

# @app.route("/alumni/login", methods=["GET", "POST"])
# def alumni_login():
#     if request.method == "POST":
#         email = request.form["email"]
#         password = request.form["password"]

#         conn = get_db_connection()
#         alumni = conn.execute("SELECT * FROM alumni WHERE email = ?", (email,)).fetchone()
#         conn.close()

#         if alumni and password == alumni["password"]: 
#             session["alumni_logged_in"] = True
#             session["alumni_id"] = alumni["alumni_id"]
#             session["alumni_name"] = f"{alumni['first_name']} {alumni['last_name']}"
#             flash("Logged in successfully!", "success")
#             return redirect(url_for("alumni_dashboard"))
#         else:
#             flash("Invalid email or password!", "danger")

#     return render_template("alumni_login.html")

# @app.route("/alumni/dashboard")
# def alumni_dashboard():
#     if not session.get("alumni_logged_in"):
#         flash("Please log in first.", "warning")
#         return redirect(url_for("alumni_login"))
#     return render_template("alumni_dashboard.html")

# -----------------------------
# ALUMNI ROUTES
# -----------------------------
@app.route("/alumni")
def alumni():
    alumni_list = get_alumni()
    return render_template("alumni.html", alumni=alumni_list)

@app.route("/alumni/add", methods=["GET", "POST"])
def add_alumni():
    if not session.get("admin_logged_in"):
        flash("Please log in first.", "warning")
        return redirect(url_for("admin_login"))

    programs = get_programs()

    if request.method == "POST":
        first_name = request.form["first_name"]
        last_name = request.form["last_name"]
        email = request.form["email"]
        phone = request.form.get("phone")
        graduation_year = request.form.get("graduation_year")
        program_id = request.form.get("program_id") or None

        conn = get_db_connection()
        conn.execute(
            "INSERT INTO alumni (first_name, last_name, email, phone, graduation_year, program_id) VALUES (?, ?, ?, ?, ?, ?)",
            (first_name, last_name, email, phone, graduation_year, program_id)
        )
        conn.commit()
        conn.close()
        flash("Alumni added successfully!", "success")
        return redirect(url_for("alumni"))

    return render_template("add_alumni.html", programs=programs, alumni=None)

@app.route("/alumni/edit/<int:alumni_id>", methods=["GET", "POST"])
def edit_alumni(alumni_id):
    if not session.get("admin_logged_in"):
        flash("Please log in first.", "warning")
        return redirect(url_for("admin_login"))

    conn = get_db_connection()
    alumni_data = conn.execute("SELECT * FROM alumni WHERE alumni_id=?", (alumni_id,)).fetchone()
    programs = get_programs()

    if request.method == "POST":
        conn.execute(
            """UPDATE alumni 
               SET first_name=?, last_name=?, email=?, phone=?, graduation_year=?, program_id=?
               WHERE alumni_id=?""",
            (request.form["first_name"], request.form["last_name"], request.form["email"],
             request.form.get("phone"), request.form.get("graduation_year"),
             request.form.get("program_id") or None, alumni_id)
        )
        conn.commit()
        conn.close()
        flash("Alumni updated successfully!", "success")
        return redirect(url_for("alumni"))

    conn.close()
    return render_template("add_alumni.html", programs=programs, alumni=alumni_data)

@app.route("/alumni/delete/<int:alumni_id>", methods=["POST"])
def delete_alumni(alumni_id):
    if not session.get("admin_logged_in"):
        flash("Please log in first.", "warning")
        return redirect(url_for("admin_login"))

    conn = get_db_connection()
    conn.execute("DELETE FROM alumni WHERE alumni_id=?", (alumni_id,))
    conn.commit()
    conn.close()
    flash("Alumni deleted successfully!", "info")
    return redirect(url_for("alumni"))

@app.route("/alumni/login", methods=["GET", "POST"])
def alumni_login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        conn = get_db_connection()
        alumni = conn.execute("SELECT * FROM alumni WHERE email=?", (email,)).fetchone()
        conn.close()

        if alumni and password == alumni["password"]:  # Use hashing for production
            session["alumni_logged_in"] = True
            session["alumni_id"] = alumni["alumni_id"]
            session["alumni_name"] = f"{alumni['first_name']} {alumni['last_name']}"
            flash("Logged in successfully!", "success")
            return redirect(url_for("alumni_dashboard"))
        else:
            flash("Invalid email or password!", "danger")

    return render_template("alumni_login.html")

@app.route("/alumni/dashboard")
def alumni_dashboard():
    if not session.get("alumni_logged_in"):
        flash("Please log in first.", "warning")
        return redirect(url_for("alumni_login"))
    return render_template("alumni_dashboard.html")


# -----------------------------
# ANNOUNCEMENTS ROUTES
# -----------------------------
@app.route("/announcements")
def announcements():
    announcements_list = get_announcements()
    return render_template("announcements.html", announcements=announcements_list)

@app.route("/announcements/add", methods=["GET","POST"])
def add_announcement():
    if not session.get("admin_logged_in"):
        return redirect(url_for("admin_login"))
    programs = get_programs()
    if request.method == "POST":
        conn = get_db_connection()
        conn.execute("""INSERT INTO events (event_title, event_description, event_date, program_id)
                        VALUES (?, ?, ?, ?)""",
                     (request.form["title"], request.form["description"], request.form["announcement_date"],
                      request.form["program_id"] or None))
        conn.commit()
        conn.close()
        flash("Announcement added successfully!", "success")
        return redirect(url_for("announcements"))
    return render_template("add_announcement.html", programs=programs)

@app.route("/announcements/edit/<int:event_id>", methods=["GET","POST"])
def edit_announcement(event_id):
    if not session.get("admin_logged_in"):
        return redirect(url_for("admin_login"))
    conn = get_db_connection()
    announcement = conn.execute("SELECT * FROM events WHERE event_id=?", (event_id,)).fetchone()
    programs = get_programs()
    if request.method == "POST":
        conn.execute("""UPDATE events SET event_title=?, event_description=?, event_date=?, program_id=?
                        WHERE event_id=?""",
                     (request.form["title"], request.form["description"], request.form["announcement_date"],
                      request.form["program_id"] or None, event_id))
        conn.commit()
        conn.close()
        flash("Announcement updated successfully!", "success")
        return redirect(url_for("announcements"))
    conn.close()
    return render_template("edit_announcements.html", announcement=announcement, programs=programs)

@app.route("/announcements/delete/<int:event_id>", methods=["POST"])
def delete_announcement(event_id):
    if not session.get("admin_logged_in"):
        return redirect(url_for("admin_login"))
    conn = get_db_connection()
    conn.execute("DELETE FROM events WHERE event_id=?", (event_id,))
    conn.commit()
    conn.close()
    flash("Announcement deleted successfully!", "info")
    return redirect(url_for("announcements"))

# -----------------------------
# CAREERS ROUTES
# -----------------------------
@app.route("/careers")
def careers():
    careers_list = get_careers()
    return render_template("careers.html", careers=careers_list)

@app.route("/careers/add", methods=["GET","POST"])
def add_career():
    if not session.get("admin_logged_in"):
        return redirect(url_for("admin_login"))
    alumni_list = get_alumni()
    if request.method == "POST":
        conn = get_db_connection()
        conn.execute("""INSERT INTO careers (alumni_id, company_name, position, start_date, end_date)
                        VALUES (?, ?, ?, ?, ?)""",
                     (request.form["alumni_id"], request.form["company_name"], request.form["position"],
                      request.form["start_date"], request.form["end_date"] or None))
        conn.commit()
        conn.close()
        flash("Career added successfully!", "success")
        return redirect(url_for("careers"))
    return render_template("add_careers.html", alumni=alumni_list)

@app.route("/careers/edit/<int:career_id>", methods=["GET","POST"])
def edit_career(career_id):
    if not session.get("admin_logged_in"):
        return redirect(url_for("admin_login"))
    conn = get_db_connection()
    career = conn.execute("SELECT * FROM careers WHERE career_id=?", (career_id,)).fetchone()
    alumni_list = get_alumni()
    if request.method == "POST":
        conn.execute("""UPDATE careers SET alumni_id=?, company_name=?, position=?, start_date=?, end_date=?
                        WHERE career_id=?""",
                     (request.form["alumni_id"], request.form["company_name"], request.form["position"],
                      request.form["start_date"], request.form["end_date"] or None, career_id))
        conn.commit()
        conn.close()
        flash("Career updated successfully!", "success")
        return redirect(url_for("careers"))
    conn.close()
    return render_template("edit_careers.html", career=career, alumni=alumni_list)

@app.route("/careers/delete/<int:career_id>", methods=["POST"])
def delete_career(career_id):
    if not session.get("admin_logged_in"):
        return redirect(url_for("admin_login"))
    conn = get_db_connection()
    conn.execute("DELETE FROM careers WHERE career_id=?", (career_id,))
    conn.commit()
    conn.close()
    flash("Career deleted successfully!", "info")
    return redirect(url_for("careers"))

# -----------------------------
# 404 PAGE
# -----------------------------
@app.errorhandler(404)
def page_not_found(e):
    return render_template("404.html"), 404

@app.route("/alumni/profile", methods=["GET", "POST"])
def alumni_profile():
    if not session.get("alumni_logged_in"):
        flash("Please log in first.", "warning")
        return redirect(url_for("alumni_login"))

    alumni_id = session["alumni_id"]
    conn = get_db_connection()
    alumni_data = conn.execute("SELECT * FROM alumni WHERE alumni_id = ?", (alumni_id,)).fetchone()
    programs = get_programs()
    conn.close()

    if request.method == "POST":
        conn = get_db_connection()
        conn.execute("""UPDATE alumni SET first_name=?, last_name=?, email=?, phone=?, graduation_year=?, program_id=?
                        WHERE alumni_id=?""",
                     (request.form["first_name"], request.form["last_name"], request.form["email"],
                      request.form["phone"], request.form["graduation_year"], request.form["program_id"] or None, alumni_id))
        conn.commit()
        conn.close()
        flash("Profile updated successfully!", "success")
        return redirect(url_for("alumni_profile"))

    return render_template("alumni_profile.html", alumni=alumni_data, programs=programs)


@app.route("/alumni/logout")
def alumni_logout():
    session.clear()
    flash("Logged out successfully.", "info")
    return redirect(url_for("alumni_login"))


# -----------------------------
# RUN APP
# -----------------------------
if __name__ == "__main__":
    app.run(debug=True)





