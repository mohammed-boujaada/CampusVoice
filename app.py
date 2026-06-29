import os
import pyodbc
import csv
import io
import hashlib
from datetime import datetime, date, timedelta
from flask import Flask, render_template, request, redirect, url_for, session, flash, send_file
from flask_wtf.csrf import CSRFProtect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from markupsafe import escape
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'default_dev_key_change_in_production')

# ===== SECURITY CONFIGURATION =====
csrf = CSRFProtect(app)

# Rate limiter for brute force protection
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://"
)

# Session security
app.config['SESSION_COOKIE_SECURE'] = True      # HTTPS only
app.config['SESSION_COOKIE_HTTPONLY'] = True    # No JS access
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'   # CSRF protection
app.config['PERMANENT_SESSION_LIFETIME'] = int(os.getenv('SESSION_TIMEOUT', 1800))  # 30 min timeout

# Security Headers
@app.after_request
def set_security_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    # NOTE: This project uses extensive inline `style="..."` in templates.
    # Allow inline styles so UI (buttons/modals/forms) renders as designed.
    # Keep scripts restricted to self + inline (needed for on* handlers currently used).
    response.headers['Content-Security-Policy'] = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline'; "
        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
        "font-src 'self' https://fonts.gstatic.com;"
    )
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    return response

# ===== UTILITY FUNCTIONS =====
def hash_password_md5(password):
    """Hash password using MD5"""
    return hashlib.md5(password.encode()).hexdigest()

def verify_password_md5(stored_hash, provided_password):
    """Verify MD5 password"""
    return stored_hash == hashlib.md5(provided_password.encode()).hexdigest()

def sanitize_input(text):
    """Sanitize user input to prevent XSS"""
    if text is None:
        return ""
    return escape(str(text)).strip()

# --- ☁️ AZURE SQL CONFIGURATION ---
# Connection string using environment variables
conn_str = f"Driver={{ODBC Driver 18 for SQL Server}};Server=tcp:{os.getenv('DB_SERVER')},1433;Database={os.getenv('DB_NAME')};Uid={os.getenv('DB_USER')};Pwd={os.getenv('DB_PASSWORD')};Encrypt=yes;TrustServerCertificate=no;Connection Timeout=60;Command Timeout=30;"

def get_db_connection(retry=3):
    """Get database connection with retry logic"""
    for attempt in range(retry):
        try:
            conn = pyodbc.connect(conn_str, timeout=60)
            return conn
        except Exception as e:
            print(f"⚠️ DB Connection Attempt {attempt + 1}/{retry} Failed: {str(e)[:100]}")
            if attempt == retry - 1:
                print(f"❌ DB Connection Failed after {retry} attempts")
                print(f"   Error: {e}")
                print(f"   Check: 1) Azure firewall rules 2) Server name 3) Credentials 4) ODBC driver")
                return None
    return None

# --- INITIALIZE DATABASE (Runs once on startup) ---
def init_db():
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            # Create Users/Coordinators table
            cursor.execute("""
                IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='Users' and xtype='U')
                CREATE TABLE Users (
                    ID INT IDENTITY(1,1) PRIMARY KEY,
                    UserID NVARCHAR(50) UNIQUE,
                    Name NVARCHAR(100),
                    Role NVARCHAR(50),
                    Password NVARCHAR(255),
                    Email NVARCHAR(100),
                    CreatedDate DATETIME
                )
            """)
            
            # Create Professors table
            cursor.execute("""
                IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='Professors' and xtype='U')
                CREATE TABLE Professors (
                    ID INT IDENTITY(1,1) PRIMARY KEY,
                    ProfessorID NVARCHAR(50) UNIQUE,
                    Name NVARCHAR(100),
                    Email NVARCHAR(100),
                    Department NVARCHAR(100),
                    Password NVARCHAR(255),
                    CreatedDate DATETIME
                )
            """)
            
            # Add Password column if it doesn't exist (for existing databases)
            cursor.execute("""
                IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME='Professors' AND COLUMN_NAME='Password')
                ALTER TABLE Professors ADD Password NVARCHAR(255)
            """)
            
            # Check if table exists, if not, create it
            cursor.execute("""
                IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='Feedbacks' and xtype='U')
                CREATE TABLE Feedbacks (
                    ID INT IDENTITY(1,1) PRIMARY KEY,
                    ProfessorID NVARCHAR(50),
                    CourseName NVARCHAR(100),
                    Rating INT,
                    Comment NVARCHAR(MAX),
                    Suggestion NVARCHAR(MAX),
                    Timestamp DATETIME,
                    IPAddress NVARCHAR(50),
                    SubmissionDate DATE
                )
            """)
            
            # Insert coordinator if not exists
            cursor.execute("SELECT COUNT(*) FROM Users WHERE UserID = 'coordinator'")
            if cursor.fetchone()[0] == 0:
                admin_pass_hash = hash_password_md5('admin')
                cursor.execute("""
                    INSERT INTO Users (UserID, Name, Role, Password, Email, CreatedDate)
                    VALUES ('coordinator', 'Head Coordinator', 'admin', ?, 'coordinator@ump.ac.ma', GETDATE())
                """, (admin_pass_hash,))
            
            # Insert default professors if table is empty
            cursor.execute("SELECT COUNT(*) FROM Professors")
            if cursor.fetchone()[0] == 0:
                pass_hash_1234 = hash_password_md5('1234')
                cursor.execute("""
                    INSERT INTO Professors (ProfessorID, Name, Email, Department, Password, CreatedDate)
                    VALUES 
                    ('prof_ahmed', 'Prof. Ahmed', 'ahmed@ump.ac.ma', 'Computer Science', ?, GETDATE()),
                    ('prof_sarah', 'Prof. Sarah', 'sarah@ump.ac.ma', 'Mathematics', ?, GETDATE())
                """, (pass_hash_1234, pass_hash_1234))
            
            conn.commit()
            print("✅ Azure SQL Database Connected & Tables Verified")
        except Exception as e:
            print(f"❌ Database Error: {e}")
        finally:
            conn.close()

# Run DB check immediately 
init_db()

# --- TEST DATABASE CONNECTION ---
@app.route('/test-db')
def test_db():
    """Test database connectivity"""
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT GETDATE()")
            result = cursor.fetchone()
            conn.close()
            return {
                "status": "✅ Connected",
                "server_time": str(result[0]),
                "message": "Azure SQL connection is working!"
            }
        except Exception as e:
            return {"status": "❌ Error", "error": str(e)}, 500
    else:
        return {
            "status": "❌ Connection Failed",
            "troubleshooting": [
                "1. Check Azure portal: Is 'campus-server-2026' running?",
                "2. Check Firewall: Add your IP in Azure SQL Firewall rules",
                "3. Check Credentials: Is password correct?",
                "4. Check ODBC: Run 'odbcinst -j' in terminal",
                "5. Test: Try 'python -c \"import pyodbc; print(pyodbc.drivers())\"'"
            ]
        }, 500

# --- ROUTES ---

@app.route('/')
def index():
    # Load professors from database
    professors = {}
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT ProfessorID, Name FROM Professors ORDER BY Name")
            for row in cursor.fetchall():
                professors[row[0]] = row[1]
            conn.close()
        except Exception as e:
            print(f"Error loading professors: {e}")
    
    return render_template('index.html', professors=professors)

@app.route('/submit', methods=['POST'])
def submit_feedback():
    prof_id = sanitize_input(request.form.get('professor_id', ''))
    course = sanitize_input(request.form.get('course', ''))
    rating = request.form.get('rating', '')
    comment = sanitize_input(request.form.get('comment', ''))
    suggestion = sanitize_input(request.form.get('suggestion', ''))
    
    # Validate rating
    try:
        rating = int(rating)
        if rating < 1 or rating > 5:
            flash("❌ Invalid rating", "error")
            return redirect(url_for('index'))
    except:
        flash("❌ Invalid rating", "error")
        return redirect(url_for('index'))
    
    # Security Data
    ip_addr = request.remote_addr
    today = str(date.today())

    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()

        # 1. CHECK 24H LIMIT (Prevent Spam)
        cursor.execute("""
            SELECT COUNT(*) FROM Feedbacks 
            WHERE IPAddress = ? AND ProfessorID = ? AND SubmissionDate = ?
        """, (ip_addr, prof_id, today))
        
        if cursor.fetchone()[0] > 0:
            flash(f"🚫 Limit Reached: You have already reviewed this professor today.", "error")
            conn.close()
            return redirect(url_for('index'))

        # 2. INSERT FEEDBACK
        cursor.execute("""
            INSERT INTO Feedbacks (ProfessorID, CourseName, Rating, Comment, Suggestion, Timestamp, IPAddress, SubmissionDate)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (prof_id, course, rating, comment, suggestion, datetime.now(), ip_addr, today))
        
        conn.commit()
        conn.close()
        flash("✅ Evaluation submitted securely to Azure SQL.", "success")
    else:
        flash("❌ Error connecting to cloud database.", "error")

    return redirect(url_for('index'))

@app.route('/admin', methods=['GET', 'POST'])
@limiter.limit("5 per minute")  # Max 5 attempts per minute
def login():
    if request.method == 'POST':
        username = sanitize_input(request.form.get('username', ''))
        password = request.form.get('password', '')
        
        if not username or not password:
            flash("❌ Username and password required", "error")
            return render_template('login.html')
        
        conn = get_db_connection()
        if conn:
            try:
                cursor = conn.cursor()
                
                # Check coordinators in Users table
                cursor.execute("SELECT Name, Role, Password FROM Users WHERE UserID = ?", (username,))
                user_result = cursor.fetchone()
                
                if user_result and verify_password_md5(user_result[2], password):  # user_result[2] is password hash
                    session['user'] = username
                    session['role'] = user_result[1]  # user_result[1] is role
                    session['name'] = user_result[0]
                    session.permanent = True
                    conn.close()
                    flash(f"✅ Welcome, {user_result[0]}!", "success")
                    return redirect(url_for('dashboard'))
                
                # Check professors in Professors table
                cursor.execute("SELECT Name, Password FROM Professors WHERE ProfessorID = ?", (username,))
                prof_result = cursor.fetchone()
                
                if prof_result and verify_password_md5(prof_result[1], password):  # prof_result[1] is password hash
                    session['user'] = username
                    session['role'] = 'professor'
                    session['name'] = prof_result[0]
                    session.permanent = True
                    conn.close()
                    flash(f"✅ Welcome, {prof_result[0]}!", "success")
                    return redirect(url_for('dashboard'))
                
                conn.close()
            except Exception as e:
                print(f"Login error: {e}")
        
        flash("❌ Invalid Credentials", "error")
            
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if 'user' not in session: return redirect(url_for('login'))
    
    user_id = session['user']
    role = session['role']
    conn = get_db_connection()
    
    feedbacks = []
    alerts = []
    avg = 0

    # Get filter parameters
    date_from = request.args.get('date_from', '')
    date_to = request.args.get('date_to', '')
    rating_filter = request.args.get('rating_filter', '')

    if conn:
        cursor = conn.cursor()
        
        if role == 'admin':
            # Coordinator sees ALL
            cursor.execute("SELECT * FROM Feedbacks ORDER BY Timestamp DESC")
            cols = [column[0] for column in cursor.description]
            feedbacks = [dict(zip(cols, row)) for row in cursor.fetchall()]
            
            # Apply filters
            if date_from:
                feedbacks = [f for f in feedbacks if f['SubmissionDate'] >= date.fromisoformat(date_from)]
            if date_to:
                feedbacks = [f for f in feedbacks if f['SubmissionDate'] <= date.fromisoformat(date_to)]
            if rating_filter:
                feedbacks = [f for f in feedbacks if f['Rating'] == int(rating_filter)]
            
            # Generate Alerts for professors with many negative reviews
            cursor.execute("SELECT ProfessorID, Name FROM Professors")
            professors_list = cursor.fetchall()
            for prof_id, prof_name in professors_list:
                neg_count = sum(1 for f in feedbacks if f['ProfessorID'] == prof_id and f['Rating'] < 3)
                if neg_count > 5:
                    alerts.append(f"⚠️ ALERT: {prof_name} has {neg_count} negative reviews.")
        else:
            # Professor sees ONLY THEIR OWN
            cursor.execute("SELECT * FROM Feedbacks WHERE ProfessorID = ? ORDER BY Timestamp DESC", (user_id,))
            cols = [column[0] for column in cursor.description]
            feedbacks = [dict(zip(cols, row)) for row in cursor.fetchall()]
            
            # Apply filters
            if date_from:
                feedbacks = [f for f in feedbacks if f['SubmissionDate'] >= date.fromisoformat(date_from)]
            if date_to:
                feedbacks = [f for f in feedbacks if f['SubmissionDate'] <= date.fromisoformat(date_to)]
            if rating_filter:
                feedbacks = [f for f in feedbacks if f['Rating'] == int(rating_filter)]

            if feedbacks:
                avg = round(sum(f['Rating'] for f in feedbacks) / len(feedbacks), 1)
        
        conn.close()

    return render_template('dashboard.html', feedbacks=feedbacks, alerts=alerts, avg=avg, role=role, 
                         date_from=date_from, date_to=date_to, rating_filter=rating_filter)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

@app.route('/professors', methods=['GET', 'POST'])
def manage_professors():
    """Coordinator can view and add professors"""
    if 'user' not in session or session['role'] != 'admin':
        flash("❌ Unauthorized - Admin only", "error")
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    professors = []
    
    if request.method == 'POST':
        # Add new professor
        prof_id = sanitize_input(request.form.get('professor_id', ''))
        name = sanitize_input(request.form.get('name', ''))
        email = sanitize_input(request.form.get('email', ''))
        department = sanitize_input(request.form.get('department', ''))
        password = request.form.get('password', '')
        
        if not all([prof_id, name, email, department, password]):
            flash("❌ All fields are required", "error")
            return redirect(url_for('manage_professors'))
        
        # Validate email format
        if '@' not in email:
            flash("❌ Invalid email format", "error")
            return redirect(url_for('manage_professors'))
        
        if conn:
            try:
                cursor = conn.cursor()
                
                # Check if professor ID already exists
                cursor.execute("SELECT ProfessorID FROM Professors WHERE ProfessorID = ?", (prof_id,))
                if cursor.fetchone():
                    flash(f"❌ Professor ID '{prof_id}' already exists. Please use a different ID.", "error")
                    conn.close()
                    return redirect(url_for('manage_professors'))
                
                # Hash the password
                password_hash = hash_password_md5(password)
                
                cursor.execute("""
                    INSERT INTO Professors (ProfessorID, Name, Email, Department, Password, CreatedDate)
                    VALUES (?, ?, ?, ?, ?, GETDATE())
                """, (prof_id, name, email, department, password_hash))
                conn.commit()
                flash(f"✅ Professor '{name}' added successfully! Share ID: {prof_id} and Password: {password}", "success")
            except Exception as e:
                flash(f"❌ Error: {str(e)}", "error")
            finally:
                conn.close()
        
        return redirect(url_for('manage_professors'))
    
    # Get all professors
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT ProfessorID, Name, Email, Department, CreatedDate FROM Professors ORDER BY CreatedDate DESC")
            cols = [column[0] for column in cursor.description]
            professors = [dict(zip(cols, row)) for row in cursor.fetchall()]
            conn.close()
        except Exception as e:
            print(f"Error loading professors: {e}")
    
    return render_template('professors.html', professors=professors)

@app.route('/professor/<prof_id>/delete', methods=['POST'])
def delete_professor(prof_id):
    """Delete a professor (coordinator only)"""
    if 'user' not in session or session['role'] != 'admin':
        flash("❌ Unauthorized", "error")
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            # Get professor name before deleting
            cursor.execute("SELECT Name FROM Professors WHERE ProfessorID = ?", (prof_id,))
            result = cursor.fetchone()
            prof_name = result[0] if result else "Unknown"
            
            # Delete professor
            cursor.execute("DELETE FROM Professors WHERE ProfessorID = ?", (prof_id,))
            conn.commit()
            flash(f"✅ Professor '{prof_name}' deleted successfully!", "success")
        except Exception as e:
            flash(f"❌ Error: {str(e)}", "error")
        finally:
            conn.close()
    
    return redirect(url_for('manage_professors'))

@app.route('/export')
def export():
    """Export feedback as CSV.

    - Professors export only their own feedback.
    - Coordinators (admin) can export all feedback.
    - Supports the same filters used on the dashboard: date_from, date_to, rating_filter.
    """
    if 'user' not in session:
        flash("❌ Unauthorized", "error")
        return redirect(url_for('login'))

    role = session.get('role')
    user_id = session.get('user')

    if role not in {'professor', 'admin'}:
        flash("❌ Unauthorized", "error")
        return redirect(url_for('login'))

    # Read optional filters (same names as dashboard)
    date_from = request.args.get('date_from', '')
    date_to = request.args.get('date_to', '')
    rating_filter = request.args.get('rating_filter', '')

    where_clauses = []
    params = []

    if role == 'professor':
        where_clauses.append("ProfessorID = ?")
        params.append(user_id)

    if date_from:
        try:
            date.fromisoformat(date_from)
        except ValueError:
            flash("❌ Invalid From Date", "error")
            return redirect(url_for('dashboard'))
        where_clauses.append("SubmissionDate >= ?")
        params.append(date_from)

    if date_to:
        try:
            date.fromisoformat(date_to)
        except ValueError:
            flash("❌ Invalid To Date", "error")
            return redirect(url_for('dashboard'))
        where_clauses.append("SubmissionDate <= ?")
        params.append(date_to)

    if rating_filter:
        try:
            rating_int = int(rating_filter)
        except ValueError:
            flash("❌ Invalid Rating Filter", "error")
            return redirect(url_for('dashboard'))
        where_clauses.append("Rating = ?")
        params.append(rating_int)

    where_sql = (" WHERE " + " AND ".join(where_clauses)) if where_clauses else ""

    conn = get_db_connection()
    if not conn:
        flash("❌ Error connecting to database", "error")
        return redirect(url_for('dashboard'))

    cursor = conn.cursor()

    if role == 'admin':
        cursor.execute(
            "SELECT Timestamp, ProfessorID, CourseName, Rating, Comment, Suggestion "
            "FROM Feedbacks" + where_sql + " ORDER BY Timestamp DESC",
            params,
        )
        cols = [column[0] for column in cursor.description]
        feedbacks = [dict(zip(cols, row)) for row in cursor.fetchall()]
        fieldnames = ['Date', 'Instructor', 'Course', 'Rating', 'Comment', 'Suggestion']
        download_name = f"Feedback_All_{date.today()}.csv"
    else:
        cursor.execute(
            "SELECT Timestamp, Rating, Comment, Suggestion "
            "FROM Feedbacks" + where_sql + " ORDER BY Timestamp DESC",
            params,
        )
        cols = [column[0] for column in cursor.description]
        feedbacks = [dict(zip(cols, row)) for row in cursor.fetchall()]
        fieldnames = ['Date', 'Rating', 'Comment', 'Suggestion']
        download_name = f"Feedback_{user_id}_{date.today()}.csv"

    conn.close()

    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()

    for fb in feedbacks:
        if role == 'admin':
            writer.writerow({
                'Date': fb['Timestamp'].strftime('%Y-%m-%d %H:%M:%S') if fb['Timestamp'] else '',
                'Instructor': fb['ProfessorID'],
                'Course': fb['CourseName'],
                'Rating': fb['Rating'],
                'Comment': fb['Comment'],
                'Suggestion': fb['Suggestion'] or '',
            })
        else:
            writer.writerow({
                'Date': fb['Timestamp'].strftime('%Y-%m-%d %H:%M:%S') if fb['Timestamp'] else '',
                'Rating': fb['Rating'],
                'Comment': fb['Comment'],
                'Suggestion': fb['Suggestion'] or '',
            })

    output.seek(0)
    return send_file(
        io.BytesIO(output.getvalue().encode('utf-8')),
        mimetype='text/csv',
        as_attachment=True,
        download_name=download_name,
    )

if __name__ == '__main__':
    app.run(debug=True)