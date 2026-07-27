# AI Attendance Management System

AI Attendance is a simple, modern attendance management system designed for demonstrating AI agent and Model Context Protocol (MCP) integrations. It provides a versioned REST API (`/api/v1/`) and a premium, dark-themed responsive user interface.

## 🏗️ Architecture Overview

The application follows a lightweight, clean, and modular design. The backend is built using **FastAPI** and **SQLite**, exposing REST APIs that allow both human users and AI agents to manage employees, clock-in records, approvals, and system logs.

```text
                                  +-----------------------+
                                  |   AI Desktop Agent    |
                                  | (Claude Desktop, etc) |
                                  +-----------+-----------+
                                              |
                                              | MCP Protocol
                                              v
+------------------+              +-----------+-----------+
|  Human User      |              |   External MCP Server |
|  (Web Browser)   |              |   for Attendance API  |
+--------+---------+              +-----------+-----------+
         |                                    |
         | HTTP / JSON                        | HTTP / JSON (API Client)
         +-----------------+   +--------------+
                           |   |
                           v   v
                 +---------+---------+
                 |    FastAPI App    | (Port 8000)
                 +---------+---------+
                           |
            +--------------+--------------+
            |                             |
            v                             v
   +--------+--------+           +--------+--------+
   |   SQLite DB     |           |  Static Assets  |
   | (attendance.db) |           |  (HTML/CSS/JS)  |
   +-----------------+           +-----------------+
```

---

## ✨ Features

1. **Dashboard Overview**: Key real-time metrics including total pending approvals, today's approved count, a list of pending employee names, and the latest 5 audit trail entries.
2. **Employee Management (CRUD)**: Create, view, update, and delete employee profiles with custom IDs, names, departments, managers, and email addresses.
3. **Attendance Registration**: Record work date, start time, and end time. Initial status is logged as `Pending`.
4. **Attendance Actions**: Single-click approve/reject actions, or bulk approve all pending records with options to exclude specific employees.
5. **AI Operation Audit Trail**: An audit log table recording every critical system change (creates, updates, deletes, approvals) and identifying the operator (e.g., `User`, `ChatGPT`, `Claude`).
6. **Demo Reset API**: A dedicated endpoint that resets the database to initial seeds instantly—ideal for CI/CD Playwright tests and live demos.
7. **Docker Support**: Ready for containerized setups and deployments.
8. **Interactive OpenAPI (Swagger)**: Out-of-the-box API testing at `/docs`.

---

## 🗄️ Database Schema (SQLite)

The system uses three SQLite tables:

### 1. `employees`
* `id` (TEXT PRIMARY KEY): Employee ID (e.g., `EMP001`)
* `name` (TEXT NOT NULL): Full Name
* `department` (TEXT NOT NULL): Department name
* `manager_name` (TEXT): Name of direct manager
* `email` (TEXT NOT NULL): Email address

### 2. `attendance`
* `id` (INTEGER PRIMARY KEY AUTOINCREMENT)
* `employee_id` (TEXT REFERENCES employees(id) ON DELETE CASCADE)
* `work_date` (TEXT NOT NULL): Date string (`YYYY-MM-DD`)
* `start_time` (TEXT NOT NULL): Clock-in timestamp (`YYYY-MM-DDTHH:MM:SS`)
* `end_time` (TEXT): Clock-out timestamp (`YYYY-MM-DDTHH:MM:SS`, nullable)
* `status` (TEXT NOT NULL): State, one of `Pending`, `Approved`, `Rejected`
* `approver` (TEXT): Name of person/agent who performed the action
* `approved_at` (TEXT): Action timestamp (nullable)

### 3. `operation_logs`
* `id` (INTEGER PRIMARY KEY AUTOINCREMENT)
* `operation` (TEXT NOT NULL): Action performed (e.g., `EmployeeCreated`, `AttendanceApproved`, `BulkApproval`)
* `operator` (TEXT NOT NULL): Initiator of the action (e.g., `User`, `ChatGPT`, `Claude`)
* `target` (TEXT NOT NULL): Target reference ID or name
* `result` (TEXT NOT NULL): Outcome, one of `Success`, `Failure`
* `details` (TEXT): Extended description or error messages
* `created_at` (TEXT NOT NULL): Timestamp of log entry

---

## 🔌 REST API Endpoints Overview

All REST API endpoints are prefixed with `/api/v1/`.

| Category | Method | Path | Description |
|---|---|---|---|
| **System** | `GET` | `/api/v1/health` | Service health status |
| **System** | `POST` | `/api/v1/demo/reset` | Clear database and reload default seed data |
| **Dashboard** | `GET` | `/api/v1/dashboard` | Fetch active metrics, pending list, and 5 latest audit logs |
| **Employees** | `GET` | `/api/v1/employees` | List all employees |
| **Employees** | `GET` | `/api/v1/employees/{id}` | Get single employee details |
| **Employees** | `POST` | `/api/v1/employees` | Register new employee |
| **Employees** | `PUT` | `/api/v1/employees/{id}` | Update employee profile |
| **Employees** | `DELETE` | `/api/v1/employees/{id}` | Delete employee |
| **Attendance** | `GET` | `/api/v1/attendance` | List attendance records (filter via `?status=`) |
| **Attendance** | `GET` | `/api/v1/attendance/pending` | List pending attendance records only |
| **Attendance** | `GET` | `/api/v1/attendance/{id}` | Get single attendance record |
| **Attendance** | `POST` | `/api/v1/attendance` | Register work attendance |
| **Attendance** | `PUT` | `/api/v1/attendance/{id}` | Update attendance record |
| **Attendance** | `DELETE` | `/api/v1/attendance/{id}` | Delete attendance record |
| **Actions** | `POST` | `/api/v1/attendance/{id}/approve` | Approve a pending attendance record |
| **Actions** | `POST` | `/api/v1/attendance/{id}/reject` | Reject a pending attendance record |
| **Actions** | `POST` | `/api/v1/attendance/bulk-approve` | Bulk approve (supports `exclude_employee_names`) |
| **Audit Logs** | `GET` | `/api/v1/logs` | Fetch system audit logs |
| **Audit Logs** | `DELETE` | `/api/v1/logs` | Clear audit logs trail |

### 🛠️ Interactive Documentation (OpenAPI)
* **Swagger UI URL**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

---

## 🚀 Running the Application

### Option A: Running Locally (Recommended)

A smart launcher script is provided to automate directory navigation, create a virtual environment (`.venv`), install dependencies, and start the development server.

1. Open a terminal and run the launcher:
   ```bash
   python run.py
   ```
2. Open your browser and navigate to:
   * **Web Application UI**: [http://127.0.0.1:8000](http://127.0.0.1:8000)
   * **OpenAPI Specs**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

### Option B: Running with Docker

1. Build the Docker image:
   ```bash
   docker build -t ai-attendance .
   ```
2. Start the container:
   ```bash
   docker run -d -p 8000:8000 --name attendance-app ai-attendance
   ```
3. Access the UI at [http://localhost:8000](http://localhost:8000).

---

## 🦾 Future Integrations

### 1. Model Context Protocol (MCP) Server
An external MCP server can be configured to wrap the REST API. This exposes tools directly to LLMs (like Claude Desktop or VS Code AI Agents):
- `list_pending_attendance`: Calls `GET /api/v1/attendance/pending`.
- `approve_attendance`: Calls `POST /api/v1/attendance/{id}/approve` with headers defining the operator (e.g. `X-Operator: Claude`).
- `bulk_approve`: Calls `POST /api/v1/attendance/bulk-approve` to approve multiple records.

### 2. CI/CD & Automated Deployment
- **Playwright Testing**: Automated tests can use `POST /api/v1/demo/reset` at the start of each test suite to ensure consistent state. Test scripts target elements using standard `data-testid` attributes (e.g., `data-testid="attendance-form"`, `data-testid="bulk-approve-btn"`).
- **GitHub Actions**: Pipeline builds the Docker image and performs deployment validation using the `GET /api/v1/health` endpoint.
- **Infrastructure as Code (IaC)**: Deploy and configure automatically to AWS/GCP using Terraform and Ansible.
