from pydantic import BaseModel, EmailStr
from typing import Optional, List, Literal

# Employee schemas
class EmployeeBase(BaseModel):
    id: str
    name: str
    department: str
    manager_name: Optional[str] = None
    email: str

class EmployeeCreate(EmployeeBase):
    pass

class EmployeeUpdate(BaseModel):
    name: Optional[str] = None
    department: Optional[str] = None
    manager_name: Optional[str] = None
    email: Optional[str] = None

class EmployeeOut(EmployeeBase):
    pass

# Attendance schemas
class AttendanceBase(BaseModel):
    employee_id: str
    work_date: str
    start_time: str
    end_time: Optional[str] = None

class AttendanceCreate(AttendanceBase):
    pass

class AttendanceUpdate(BaseModel):
    employee_id: Optional[str] = None
    work_date: Optional[str] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    status: Optional[str] = None
    approver: Optional[str] = None
    approved_at: Optional[str] = None

class AttendanceStatusChange(BaseModel):
    """A status transition shared by the debug UI and external integrations."""
    status: Literal["Pending", "Approved", "Rejected"]

class AttendanceOut(AttendanceBase):
    id: int
    status: str
    approver: Optional[str] = None
    approved_at: Optional[str] = None
    employee_name: Optional[str] = None
    employee_department: Optional[str] = None

# Audit Log schemas
class OperationLogOut(BaseModel):
    id: int
    operation: str
    operator: str
    target: str
    result: str
    details: Optional[str] = None
    created_at: str

# Bulk Approval schemas
class BulkApproveRequest(BaseModel):
    approver: str
    exclude_employee_names: List[str] = []

# Approval/Rejection Request
class ApproveRejectActionRequest(BaseModel):
    approver: str

# Dashboard schemas
class DashboardStats(BaseModel):
    pending_approvals: int
    approved_today: int
    pending_employee_names: List[str]
    latest_logs: List[OperationLogOut]

# Health check schemas
class HealthResponse(BaseModel):
    status: str = "ok"
    version: str = "1.0.0"

# Reset schemas
class ResetResponse(BaseModel):
    message: str = "Demo data has been reset."
