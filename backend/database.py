import sqlite3
import os
import datetime

DB_PATH = os.getenv(
    "ATTENDANCE_DB_PATH",
    os.path.join(os.path.dirname(__file__), "..", "attendance.db"),
)

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    # Enable foreign keys
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def init_db(seed=True):
    conn = get_db_connection()
    cursor = conn.cursor()

    # Create tables
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS employees (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        department TEXT NOT NULL,
        manager_name TEXT,
        email TEXT NOT NULL
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS attendance (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        employee_id TEXT NOT NULL,
        work_date TEXT NOT NULL,
        start_time TEXT NOT NULL,
        end_time TEXT,
        status TEXT NOT NULL CHECK(status IN ('Pending', 'Approved', 'Rejected')),
        approver TEXT,
        approved_at TEXT,
        FOREIGN KEY (employee_id) REFERENCES employees(id) ON DELETE CASCADE
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS operation_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        operation TEXT NOT NULL,
        operator TEXT NOT NULL,
        target TEXT NOT NULL,
        result TEXT NOT NULL,
        details TEXT,
        created_at TEXT NOT NULL
    );
    """)

    conn.commit()

    # Seed only when requested
    if seed:
        seed_data(conn)

    conn.close()

def seed_data(conn):
    cursor = conn.cursor()
    
    # Check if employees table is empty
    cursor.execute("SELECT COUNT(*) FROM employees")
    if cursor.fetchone()[0] == 0:
        employees = [
            ("EMP001", "Alice Smith", "Engineering", "John Doe", "alice@example.com"),
            ("EMP002", "Bob Jones", "Marketing", "Jane Smith", "bob@example.com"),
            ("EMP003", "Charlie Brown", "Sales", "John Doe", "charlie@example.com"),
            ("EMP004", "Diana Prince", "HR", "Jane Smith", "diana@example.com")
        ]
        cursor.executemany(
            "INSERT INTO employees (id, name, department, manager_name, email) VALUES (?, ?, ?, ?, ?)",
            employees
        )
        
        # Log employee creation
        now_str = datetime.datetime.now().isoformat()
        cursor.execute(
            "INSERT INTO operation_logs (operation, operator, target, result, details, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            ("EmployeeCreated", "System", "EMP001, EMP002, EMP003, EMP004", "Success", "Initial seed employees registered by system", now_str)
        )

    # Check if attendance table is empty
    cursor.execute("SELECT COUNT(*) FROM attendance")
    if cursor.fetchone()[0] == 0:
        today = datetime.date.today()
        yesterday = today - datetime.timedelta(days=1)
        
        today_str = today.isoformat()
        yesterday_str = yesterday.isoformat()
        
        now_str = datetime.datetime.now().isoformat()

        attendance_records = [
            # 2 Approved today
            ("EMP001", today_str, f"{today_str}T09:00:00", f"{today_str}T18:00:00", "Approved", "John Doe", f"{today_str}T18:05:00"),
            ("EMP002", today_str, f"{today_str}T08:30:00", f"{today_str}T17:30:00", "Approved", "Jane Smith", f"{today_str}T17:45:00"),
            # 2 Pending (one today, one yesterday)
            ("EMP003", today_str, f"{today_str}T09:15:00", None, "Pending", None, None),
            ("EMP004", yesterday_str, f"{yesterday_str}T09:00:00", f"{yesterday_str}T17:00:00", "Pending", None, None),
            # 1 Rejected yesterday
            ("EMP001", yesterday_str, f"{yesterday_str}T10:00:00", f"{yesterday_str}T14:00:00", "Rejected", "John Doe", f"{yesterday_str}T15:00:00")
        ]
        
        cursor.executemany(
            "INSERT INTO attendance (employee_id, work_date, start_time, end_time, status, approver, approved_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
            attendance_records
        )
        
        # Log attendance creation
        cursor.execute(
            "INSERT INTO operation_logs (operation, operator, target, result, details, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            ("AttendanceCreated", "System", "EMP001, EMP002, EMP003, EMP004", "Success", "Initial seed attendance records registered by system", now_str)
        )

    conn.commit()

if __name__ == "__main__":
    init_db()
    print("Database initialized successfully at:", DB_PATH)
