import sqlite3
import datetime
from typing import List, Optional, Tuple
from backend.database import get_db_connection, seed_data

# Audit helper
def write_audit_log(cursor: sqlite3.Cursor, operation: str, operator: str, target: str, result: str, details: Optional[str] = None):
    now_str = datetime.datetime.now().isoformat()
    cursor.execute(
        """
        INSERT INTO operation_logs (operation, operator, target, result, details, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (operation, operator, target, result, details, now_str)
    )

# Employee CRUD
def create_employee(conn: sqlite3.Connection, emp_id: str, name: str, dept: str, manager: Optional[str], email: str, operator: str = "User") -> dict:
    cursor = conn.cursor()
    try:
        # Check if exists
        cursor.execute("SELECT id FROM employees WHERE id = ?", (emp_id,))
        if cursor.fetchone():
            raise ValueError(f"Employee ID {emp_id} already exists.")
            
        cursor.execute(
            """
            INSERT INTO employees (id, name, department, manager_name, email)
            VALUES (?, ?, ?, ?, ?)
            """,
            (emp_id, name, dept, manager, email)
        )
        
        write_audit_log(
            cursor, 
            operation="EmployeeCreated", 
            operator=operator, 
            target=emp_id, 
            result="Success", 
            details=f"Name: {name}, Dept: {dept}"
        )
        conn.commit()
        return {"id": emp_id, "name": name, "department": dept, "manager_name": manager, "email": email}
    except Exception as e:
        conn.rollback()
        # Log failure in a separate connection/transaction so it is persisted
        try:
            with get_db_connection() as fail_conn:
                write_audit_log(fail_conn.cursor(), "EmployeeCreated", operator, emp_id, "Failure", str(e))
                fail_conn.commit()
        except:
            pass
        raise e

def get_employee(conn: sqlite3.Connection, emp_id: str) -> Optional[dict]:
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM employees WHERE id = ?", (emp_id,))
    row = cursor.fetchone()
    if row:
        return dict(row)
    return None

def get_all_employees(conn: sqlite3.Connection) -> List[dict]:
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM employees ORDER BY name ASC")
    return [dict(row) for row in cursor.fetchall()]

def update_employee(conn: sqlite3.Connection, emp_id: str, updates: dict, operator: str = "User") -> Optional[dict]:
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM employees WHERE id = ?", (emp_id,))
    existing = cursor.fetchone()
    if not existing:
        return None
        
    existing_dict = dict(existing)
    
    # Calculate fields to update
    fields = []
    values = []
    for k, v in updates.items():
        if v is not None:
            fields.append(f"{k} = ?")
            values.append(v)
            
    if not fields:
        return existing_dict
        
    values.append(emp_id)
    update_query = f"UPDATE employees SET {', '.join(fields)} WHERE id = ?"
    
    try:
        cursor.execute(update_query, tuple(values))
        
        # Get updated version
        cursor.execute("SELECT * FROM employees WHERE id = ?", (emp_id,))
        updated = dict(cursor.fetchone())
        
        # Log details
        details_str = f"Updated: {', '.join([f'{k}: {existing_dict[k]}->{updated[k]}' for k, v in updates.items() if v is not None])}"
        write_audit_log(
            cursor,
            operation="EmployeeUpdated",
            operator=operator,
            target=emp_id,
            result="Success",
            details=details_str
        )
        conn.commit()
        return updated
    except Exception as e:
        conn.rollback()
        try:
            with get_db_connection() as fail_conn:
                write_audit_log(fail_conn.cursor(), "EmployeeUpdated", operator, emp_id, "Failure", str(e))
                fail_conn.commit()
        except:
            pass
        raise e

def delete_employee(conn: sqlite3.Connection, emp_id: str, operator: str = "User") -> bool:
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM employees WHERE id = ?", (emp_id,))
    emp = cursor.fetchone()
    if not emp:
        return False
        
    emp_name = emp["name"]
    try:
        cursor.execute("DELETE FROM employees WHERE id = ?", (emp_id,))
        write_audit_log(
            cursor,
            operation="EmployeeDeleted",
            operator=operator,
            target=emp_id,
            result="Success",
            details=f"Name: {emp_name}"
        )
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        try:
            with get_db_connection() as fail_conn:
                write_audit_log(fail_conn.cursor(), "EmployeeDeleted", operator, emp_id, "Failure", str(e))
                fail_conn.commit()
        except:
            pass
        raise e

# Attendance CRUD
def create_attendance(conn: sqlite3.Connection, emp_id: str, work_date: str, start_time: str, end_time: Optional[str] = None, operator: str = "User") -> dict:
    cursor = conn.cursor()
    try:
        # Check if employee exists
        cursor.execute("SELECT name FROM employees WHERE id = ?", (emp_id,))
        emp = cursor.fetchone()
        if not emp:
            raise ValueError(f"Employee with ID {emp_id} does not exist.")
            
        emp_name = emp["name"]
        
        # Check if attendance record already exists for this date
        cursor.execute("SELECT id FROM attendance WHERE employee_id = ? AND work_date = ?", (emp_id, work_date))
        if cursor.fetchone():
            raise ValueError(f"Attendance record already exists for employee {emp_id} on {work_date}.")
            
        cursor.execute(
            """
            INSERT INTO attendance (employee_id, work_date, start_time, end_time, status)
            VALUES (?, ?, ?, ?, 'Pending')
            """,
            (emp_id, work_date, start_time, end_time)
        )
        record_id = cursor.lastrowid
        
        write_audit_log(
            cursor,
            operation="AttendanceCreated",
            operator=operator,
            target=f"{emp_name} ({emp_id})",
            result="Success",
            details=f"Record ID: {record_id}, Date: {work_date}, Start: {start_time}"
        )
        conn.commit()
        
        # Return record
        cursor.execute(
            """
            SELECT a.*, e.name as employee_name, e.department as employee_department
            FROM attendance a
            JOIN employees e ON a.employee_id = e.id
            WHERE a.id = ?
            """,
            (record_id,)
        )
        return dict(cursor.fetchone())
    except Exception as e:
        conn.rollback()
        try:
            with get_db_connection() as fail_conn:
                write_audit_log(fail_conn.cursor(), "AttendanceCreated", operator, emp_id, "Failure", str(e))
                fail_conn.commit()
        except:
            pass
        raise e

def get_attendance(conn: sqlite3.Connection, record_id: int) -> Optional[dict]:
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT a.*, e.name as employee_name, e.department as employee_department
        FROM attendance a
        JOIN employees e ON a.employee_id = e.id
        WHERE a.id = ?
        """,
        (record_id,)
    )
    row = cursor.fetchone()
    if row:
        return dict(row)
    return None

def get_all_attendance(conn: sqlite3.Connection, status: Optional[str] = None) -> List[dict]:
    cursor = conn.cursor()
    query = """
        SELECT a.*, e.name as employee_name, e.department as employee_department
        FROM attendance a
        JOIN employees e ON a.employee_id = e.id
    """
    params = []
    if status:
        query += " WHERE a.status = ?"
        params.append(status)
    query += " ORDER BY a.work_date DESC, a.start_time DESC"
    
    cursor.execute(query, tuple(params))
    return [dict(row) for row in cursor.fetchall()]

def get_pending_attendance(conn: sqlite3.Connection) -> List[dict]:
    return get_all_attendance(conn, status="Pending")

def update_attendance(conn: sqlite3.Connection, record_id: int, updates: dict, operator: str = "User") -> Optional[dict]:
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT a.*, e.name as employee_name 
        FROM attendance a 
        JOIN employees e ON a.employee_id = e.id 
        WHERE a.id = ?
        """,
        (record_id,)
    )
    existing = cursor.fetchone()
    if not existing:
        return None
        
    emp_name = existing["employee_name"]
    
    fields = []
    values = []
    for k, v in updates.items():
        # Prevent manual raw status/approver/approved_at bypass if update_attendance is used generally
        fields.append(f"{k} = ?")
        values.append(v)
        
    if not fields:
        return dict(existing)
        
    values.append(record_id)
    update_query = f"UPDATE attendance SET {', '.join(fields)} WHERE id = ?"
    
    try:
        cursor.execute(update_query, tuple(values))
        
        # Fetch updated
        cursor.execute(
            """
            SELECT a.*, e.name as employee_name, e.department as employee_department
            FROM attendance a
            JOIN employees e ON a.employee_id = e.id
            WHERE a.id = ?
            """,
            (record_id,)
        )
        updated = dict(cursor.fetchone())
        
        write_audit_log(
            cursor,
            operation="AttendanceUpdated",
            operator=operator,
            target=f"{emp_name} (ID: {record_id})",
            result="Success",
            details=f"Updates: {list(updates.keys())}"
        )
        conn.commit()
        return updated
    except Exception as e:
        conn.rollback()
        raise e

def change_attendance_status(conn: sqlite3.Connection, record_id: int, status: str, operator: str = "Debug User") -> Optional[dict]:
    """Apply a complete status transition for the debug UI and future MCP clients."""
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT a.status, e.name AS employee_name
        FROM attendance a
        JOIN employees e ON a.employee_id = e.id
        WHERE a.id = ?
        """,
        (record_id,)
    )
    existing = cursor.fetchone()
    if not existing:
        return None

    previous_status = existing["status"]
    approver = None if status == "Pending" else "Debug User"
    approved_at = None if status == "Pending" else datetime.datetime.now().isoformat()

    try:
        cursor.execute(
            "UPDATE attendance SET status = ?, approver = ?, approved_at = ? WHERE id = ?",
            (status, approver, approved_at, record_id)
        )
        write_audit_log(
            cursor,
            operation="Status Changed",
            operator=operator,
            target=existing["employee_name"],
            result=f"{previous_status} → {status}",
            details=f"Record ID: {record_id}"
        )
        conn.commit()
        return get_attendance(conn, record_id)
    except Exception:
        conn.rollback()
        raise

def delete_attendance(conn: sqlite3.Connection, record_id: int, operator: str = "User") -> bool:
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT a.work_date, e.name as employee_name 
        FROM attendance a 
        JOIN employees e ON a.employee_id = e.id 
        WHERE a.id = ?
        """,
        (record_id,)
    )
    existing = cursor.fetchone()
    if not existing:
        return False
        
    emp_name = existing["employee_name"]
    work_date = existing["work_date"]
    
    try:
        cursor.execute("DELETE FROM attendance WHERE id = ?", (record_id,))
        write_audit_log(
            cursor,
            operation="AttendanceDeleted",
            operator=operator,
            target=f"{emp_name} (ID: {record_id})",
            result="Success",
            details=f"Date: {work_date}"
        )
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        raise e

# Approve / Reject actions
def approve_attendance(conn: sqlite3.Connection, record_id: int, approver: str, operator: str = "User") -> Optional[dict]:
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT a.status, e.name as employee_name 
        FROM attendance a 
        JOIN employees e ON a.employee_id = e.id 
        WHERE a.id = ?
        """,
        (record_id,)
    )
    existing = cursor.fetchone()
    if not existing:
        return None
        
    emp_name = existing["employee_name"]
    now_str = datetime.datetime.now().isoformat()
    
    try:
        cursor.execute(
            """
            UPDATE attendance 
            SET status = 'Approved', approver = ?, approved_at = ?
            WHERE id = ?
            """,
            (approver, now_str, record_id)
        )
        
        write_audit_log(
            cursor,
            operation="AttendanceApproved",
            operator=operator,
            target=emp_name,
            result="Success",
            details=f"Record ID: {record_id}, Approver: {approver}"
        )
        conn.commit()
        
        # Fetch updated
        cursor.execute(
            """
            SELECT a.*, e.name as employee_name, e.department as employee_department
            FROM attendance a
            JOIN employees e ON a.employee_id = e.id
            WHERE a.id = ?
            """,
            (record_id,)
        )
        return dict(cursor.fetchone())
    except Exception as e:
        conn.rollback()
        try:
            with get_db_connection() as fail_conn:
                write_audit_log(fail_conn.cursor(), "AttendanceApproved", operator, emp_name, "Failure", str(e))
                fail_conn.commit()
        except:
            pass
        raise e

def reject_attendance(conn: sqlite3.Connection, record_id: int, approver: str, operator: str = "User") -> Optional[dict]:
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT a.status, e.name as employee_name 
        FROM attendance a 
        JOIN employees e ON a.employee_id = e.id 
        WHERE a.id = ?
        """,
        (record_id,)
    )
    existing = cursor.fetchone()
    if not existing:
        return None
        
    emp_name = existing["employee_name"]
    now_str = datetime.datetime.now().isoformat()
    
    try:
        cursor.execute(
            """
            UPDATE attendance 
            SET status = 'Rejected', approver = ?, approved_at = ?
            WHERE id = ?
            """,
            (approver, now_str, record_id)
        )
        
        write_audit_log(
            cursor,
            operation="AttendanceRejected",
            operator=operator,
            target=emp_name,
            result="Success",
            details=f"Record ID: {record_id}, Approver: {approver}"
        )
        conn.commit()
        
        # Fetch updated
        cursor.execute(
            """
            SELECT a.*, e.name as employee_name, e.department as employee_department
            FROM attendance a
            JOIN employees e ON a.employee_id = e.id
            WHERE a.id = ?
            """,
            (record_id,)
        )
        return dict(cursor.fetchone())
    except Exception as e:
        conn.rollback()
        try:
            with get_db_connection() as fail_conn:
                write_audit_log(fail_conn.cursor(), "AttendanceRejected", operator, emp_name, "Failure", str(e))
                fail_conn.commit()
        except:
            pass
        raise e

def bulk_approve_attendance(conn: sqlite3.Connection, approver: str, exclude_employee_names: List[str], operator: str = "User") -> List[int]:
    cursor = conn.cursor()
    now_str = datetime.datetime.now().isoformat()
    
    # We select all pending attendance records
    cursor.execute(
        """
        SELECT a.id, e.name as employee_name
        FROM attendance a
        JOIN employees e ON a.employee_id = e.id
        WHERE a.status = 'Pending'
        """
    )
    pending_records = cursor.fetchall()
    
    approved_ids = []
    approved_names = []
    
    for rec in pending_records:
        rec_id = rec["id"]
        emp_name = rec["employee_name"]
        
        if emp_name in exclude_employee_names:
            continue
            
        cursor.execute(
            """
            UPDATE attendance
            SET status = 'Approved', approver = ?, approved_at = ?
            WHERE id = ?
            """,
            (approver, now_str, rec_id)
        )
        approved_ids.append(rec_id)
        approved_names.append(emp_name)
        
    if approved_ids:
        names_str = ", ".join(approved_names)
        write_audit_log(
            cursor,
            operation="BulkApproval",
            operator=operator,
            target=names_str,
            result="Success",
            details=f"Approved {len(approved_ids)} records. Approver: {approver}. Excluded: {', '.join(exclude_employee_names)}"
        )
        conn.commit()
    else:
        write_audit_log(
            cursor,
            operation="BulkApproval",
            operator=operator,
            target="None",
            result="Success",
            details=f"No records approved. Excluded: {', '.join(exclude_employee_names)}"
        )
        conn.commit()
        
    return approved_ids

# Audit Logs
def get_logs(conn: sqlite3.Connection, limit: Optional[int] = None) -> List[dict]:
    cursor = conn.cursor()
    query = "SELECT * FROM operation_logs ORDER BY created_at DESC"
    if limit:
        query += f" LIMIT {limit}"
    cursor.execute(query)
    return [dict(row) for row in cursor.fetchall()]

def clear_logs(conn: sqlite3.Connection) -> None:
    cursor = conn.cursor()
    cursor.execute("DELETE FROM operation_logs")
    conn.commit()

# Dashboard Stats
def get_dashboard_stats(conn: sqlite3.Connection) -> dict:
    cursor = conn.cursor()
    
    # 1. Number of Pending Approvals
    cursor.execute("SELECT COUNT(*) FROM attendance WHERE status = 'Pending'")
    pending_count = cursor.fetchone()[0]
    
    # 2. Number of Approved Records Today
    today_str = datetime.date.today().isoformat()
    cursor.execute("SELECT COUNT(*) FROM attendance WHERE status = 'Approved' AND work_date = ?", (today_str,))
    approved_today_count = cursor.fetchone()[0]
    
    # 3. Pending Employee Names
    cursor.execute(
        """
        SELECT DISTINCT e.name
        FROM attendance a
        JOIN employees e ON a.employee_id = e.id
        WHERE a.status = 'Pending'
        ORDER BY e.name ASC
        """
    )
    pending_names = [row["name"] for row in cursor.fetchall()]
    
    # 4. Latest 5 logs
    latest_logs = get_logs(conn, limit=5)
    
    return {
        "pending_approvals": pending_count,
        "approved_today": approved_today_count,
        "pending_employee_names": pending_names,
        "latest_logs": latest_logs
    }

# Reset Demo Data
def reset_demo_data(conn: sqlite3.Connection) -> None:
    cursor = conn.cursor()
    
    # Disable foreign keys temporarily during wipe to avoid order issues, or drop in order
    cursor.execute("PRAGMA foreign_keys = OFF;")
    cursor.execute("DELETE FROM attendance;")
    cursor.execute("DELETE FROM employees;")
    cursor.execute("DELETE FROM operation_logs;")
    cursor.execute("PRAGMA foreign_keys = ON;")
    conn.commit()
    
    # Seed new data
    seed_data(conn)
