import os
from typing import List, Optional
from fastapi import FastAPI, Depends, HTTPException, Header, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from backend.database import init_db, get_db_connection
from backend.schemas import (
    EmployeeCreate, EmployeeUpdate, EmployeeOut,
    AttendanceCreate, AttendanceUpdate, AttendanceOut,
    OperationLogOut, BulkApproveRequest, ApproveRejectActionRequest,
    DashboardStats, HealthResponse, ResetResponse
)
from backend import crud

app = FastAPI(
    title="AI Attendance API",
    description="Attendance Management System for AI and MCP Demonstration",
    version="1.0.0"
)

# CORS middleware to allow external integrations easily
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Startup DB initialization
@app.on_event("startup")
def startup_event():
    init_db()

# Resolve paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATIC_DIR = os.path.join(BASE_DIR, "static")

# Helper dependency to resolve operator name
def get_operator(x_operator: Optional[str] = Header(default=None, alias="X-Operator"), operator: Optional[str] = Query(default=None)) -> str:
    if x_operator:
        return x_operator
    if operator:
        return operator
    return "User"

# --- REST APIs (v1) ---

# Health Check
@app.get("/api/v1/health", response_model=HealthResponse, tags=["System"])
def health_check():
    return {"status": "ok", "version": "1.0.0"}

# Reset Demo Data
@app.post("/api/v1/demo/reset", response_model=ResetResponse, tags=["System"])
def reset_demo():
    try:
        with get_db_connection() as conn:
            crud.reset_demo_data(conn)
        return {"message": "Demo data has been reset."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database reset failed: {str(e)}")

# Dashboard Statistics
@app.get("/api/v1/dashboard", response_model=DashboardStats, tags=["Dashboard"])
def get_dashboard():
    try:
        with get_db_connection() as conn:
            stats = crud.get_dashboard_stats(conn)
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Employee Management (CRUD)
@app.get("/api/v1/employees", response_model=List[EmployeeOut], tags=["Employees"])
def list_employees():
    with get_db_connection() as conn:
        return crud.get_all_employees(conn)

@app.get("/api/v1/employees/{employee_id}", response_model=EmployeeOut, tags=["Employees"])
def get_employee(employee_id: str):
    with get_db_connection() as conn:
        emp = crud.get_employee(conn, employee_id)
        if not emp:
            raise HTTPException(status_code=404, detail="Employee not found")
        return emp

@app.post("/api/v1/employees", response_model=EmployeeOut, status_code=201, tags=["Employees"])
def create_employee(employee: EmployeeCreate, operator: str = Depends(get_operator)):
    try:
        with get_db_connection() as conn:
            return crud.create_employee(
                conn, 
                emp_id=employee.id, 
                name=employee.name, 
                dept=employee.department, 
                manager=employee.manager_name, 
                email=employee.email, 
                operator=operator
            )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/v1/employees/{employee_id}", response_model=EmployeeOut, tags=["Employees"])
def update_employee(employee_id: str, updates: EmployeeUpdate, operator: str = Depends(get_operator)):
    with get_db_connection() as conn:
        updated = crud.update_employee(conn, employee_id, updates.dict(exclude_unset=True), operator=operator)
        if not updated:
            raise HTTPException(status_code=404, detail="Employee not found")
        return updated

@app.delete("/api/v1/employees/{employee_id}", tags=["Employees"])
def delete_employee(employee_id: str, operator: str = Depends(get_operator)):
    with get_db_connection() as conn:
        deleted = crud.delete_employee(conn, employee_id, operator=operator)
        if not deleted:
            raise HTTPException(status_code=404, detail="Employee not found")
        return {"message": f"Employee {employee_id} deleted successfully."}

# Attendance Management (CRUD)
@app.get("/api/v1/attendance", response_model=List[AttendanceOut], tags=["Attendance"])
def list_attendance(status: Optional[str] = Query(default=None, description="Filter by status (Pending, Approved, Rejected)")):
    if status and status not in ("Pending", "Approved", "Rejected"):
        raise HTTPException(status_code=400, detail="Invalid status filter")
    with get_db_connection() as conn:
        return crud.get_all_attendance(conn, status=status)

@app.get("/api/v1/attendance/pending", response_model=List[AttendanceOut], tags=["Attendance"])
def list_pending_attendance():
    with get_db_connection() as conn:
        return crud.get_pending_attendance(conn)

@app.get("/api/v1/attendance/{record_id}", response_model=AttendanceOut, tags=["Attendance"])
def get_attendance(record_id: int):
    with get_db_connection() as conn:
        record = crud.get_attendance(conn, record_id)
        if not record:
            raise HTTPException(status_code=404, detail="Attendance record not found")
        return record

@app.post("/api/v1/attendance", response_model=AttendanceOut, status_code=201, tags=["Attendance"])
def create_attendance(record: AttendanceCreate, operator: str = Depends(get_operator)):
    try:
        with get_db_connection() as conn:
            return crud.create_attendance(
                conn, 
                emp_id=record.employee_id, 
                work_date=record.work_date, 
                start_time=record.start_time, 
                end_time=record.end_time, 
                operator=operator
            )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/v1/attendance/{record_id}", response_model=AttendanceOut, tags=["Attendance"])
def update_attendance(record_id: int, updates: AttendanceUpdate, operator: str = Depends(get_operator)):
    with get_db_connection() as conn:
        updated = crud.update_attendance(conn, record_id, updates.dict(exclude_unset=True), operator=operator)
        if not updated:
            raise HTTPException(status_code=404, detail="Attendance record not found")
        return updated

@app.delete("/api/v1/attendance/{record_id}", tags=["Attendance"])
def delete_attendance(record_id: int, operator: str = Depends(get_operator)):
    with get_db_connection() as conn:
        deleted = crud.delete_attendance(conn, record_id, operator=operator)
        if not deleted:
            raise HTTPException(status_code=404, detail="Attendance record not found")
        return {"message": f"Attendance record {record_id} deleted successfully."}

# Attendance operations (Approve / Reject / Bulk)
@app.post("/api/v1/attendance/{record_id}/approve", response_model=AttendanceOut, tags=["Attendance Actions"])
def approve_attendance(record_id: int, action: ApproveRejectActionRequest, operator: str = Depends(get_operator)):
    with get_db_connection() as conn:
        approved = crud.approve_attendance(conn, record_id, approver=action.approver, operator=operator)
        if not approved:
            raise HTTPException(status_code=404, detail="Attendance record not found")
        return approved

@app.post("/api/v1/attendance/{record_id}/reject", response_model=AttendanceOut, tags=["Attendance Actions"])
def reject_attendance(record_id: int, action: ApproveRejectActionRequest, operator: str = Depends(get_operator)):
    with get_db_connection() as conn:
        rejected = crud.reject_attendance(conn, record_id, approver=action.approver, operator=operator)
        if not rejected:
            raise HTTPException(status_code=404, detail="Attendance record not found")
        return rejected

@app.post("/api/v1/attendance/bulk-approve", tags=["Attendance Actions"])
def bulk_approve_attendance(request: BulkApproveRequest, operator: str = Depends(get_operator)):
    with get_db_connection() as conn:
        approved_ids = crud.bulk_approve_attendance(
            conn, 
            approver=request.approver, 
            exclude_employee_names=request.exclude_employee_names, 
            operator=operator
        )
    return {"message": f"Successfully approved {len(approved_ids)} attendance records.", "approved_ids": approved_ids}

# Audit Logs endpoints
@app.get("/api/v1/logs", response_model=List[OperationLogOut], tags=["Audit Logs"])
def list_logs(limit: Optional[int] = Query(default=None, description="Limit number of logs returned")):
    with get_db_connection() as conn:
        return crud.get_logs(conn, limit=limit)

@app.delete("/api/v1/logs", tags=["Audit Logs"])
def clear_logs():
    with get_db_connection() as conn:
        crud.clear_logs(conn)
    return {"message": "Audit logs cleared successfully."}

# Mount static files and SPA root
if os.path.exists(STATIC_DIR):
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

@app.get("/")
def read_index():
    index_path = os.path.join(STATIC_DIR, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"message": "Welcome to AI Attendance REST API! UI static files folder is empty or not created yet."}
