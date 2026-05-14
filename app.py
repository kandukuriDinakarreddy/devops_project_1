from flask import Flask, render_template, request, redirect, url_for
import mysql.connector
import os
import time

app = Flask(__name__)

# ✅ VERSION — change this to see CI/CD working
APP_VERSION = "v2.0 — Auto Deployed by Jenkins"

def get_db():
    retries = 10
    while retries:
        try:
            conn = mysql.connector.connect(
                host=os.environ.get("MYSQL_HOST", "mysql"),
                user=os.environ.get("MYSQL_USER", "root"),
                password=os.environ.get("MYSQL_PASSWORD", "root"),
                database=os.environ.get("MYSQL_DB", "devops")
            )
            return conn
        except Exception as e:
            retries -= 1
            print(f"DB not ready, retrying in 5s... ({e})")
            time.sleep(5)
    raise Exception("Could not connect to database")

def init_db():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id INT AUTO_INCREMENT PRIMARY KEY,
            message VARCHAR(255) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

@app.route("/")
def index():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT message, created_at FROM messages ORDER BY created_at DESC")
    messages = cursor.fetchall()
    conn.close()
    return render_template("index.html", messages=messages, version=APP_VERSION)

@app.route("/add", methods=["POST"])
def add():
    msg = request.form.get("message", "").strip()
    if msg:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO messages (message) VALUES (%s)", (msg,))
        conn.commit()
        conn.close()
    return redirect(url_for("index"))

@app.route("/health")
def health():
    try:
        conn = get_db()
        conn.close()
        return {"status": "healthy", "version": APP_VERSION}, 200
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}, 500

# ✅ NEW ROUTE — proof that new code was deployed
@app.route("/about")
def about():
    return {
        "project": "Two-Tier Flask DevOps Pipeline",
        "version": APP_VERSION,
        "author": "Kandukuri Dinakar Reddy",
        "pipeline": "GitHub → Jenkins → Docker → EC2",
        "message": "If you see this, your CI/CD pipeline is working perfectly!"
    }

if __name__ == "__main__":
    print("Waiting for database...")
    time.sleep(10)
    init_db()
    print("Database ready!")
    app.run(host="0.0.0.0", port=5000, debug=True)
