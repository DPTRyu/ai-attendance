def test_health(client):
    response = client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_create_employee(client):
    employee = {
        "id": "TEST001",
        "name": "Test User",
        "department": "Testing",
        "manager_name": "Test Manager",
        "email": "test@example.com",
    }

    response = client.post(
        "/api/v1/employees",
        json=employee,
        headers={"X-Operator": "pytest"},
    )

    assert response.status_code == 201

    data = response.json()

    assert data["id"] == "TEST001"
    assert data["name"] == "Test User"


def test_create_attendance(client):
    employee = {
        "id": "TEST002",
        "name": "Attendance Test",
        "department": "Testing",
        "manager_name": "Test Manager",
        "email": "attendance@example.com",
    }

    employee_response = client.post(
        "/api/v1/employees",
        json=employee,
        headers={"X-Operator": "pytest"},
    )

    assert employee_response.status_code == 201

    attendance = {
        "employee_id": "TEST002",
        "work_date": "2026-08-17",
        "start_time": "2026-08-17T09:00:00",
    }

    response = client.post(
        "/api/v1/attendance",
        json=attendance,
        headers={"X-Operator": "pytest"},
    )

    assert response.status_code == 201

    data = response.json()

    assert data["employee_id"] == "TEST002"
    assert data["status"] == "Pending"


def test_approve_attendance(client):
    employee = {
        "id": "TEST003",
        "name": "Approval Test",
        "department": "Testing",
        "manager_name": "Test Manager",
        "email": "approval@example.com",
    }

    response = client.post(
        "/api/v1/employees",
        json=employee,
        headers={"X-Operator": "pytest"},
    )

    assert response.status_code == 201

    attendance = {
        "employee_id": "TEST003",
        "work_date": "2026-08-17",
        "start_time": "2026-08-17T09:00:00",
    }

    response = client.post(
        "/api/v1/attendance",
        json=attendance,
        headers={"X-Operator": "pytest"},
    )

    assert response.status_code == 201

    record_id = response.json()["id"]

    response = client.post(
        f"/api/v1/attendance/{record_id}/approve",
        json={
            "approver": "Test Manager",
        },
        headers={"X-Operator": "pytest"},
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == record_id
    assert data["status"] == "Approved"
    assert data["approver"] == "Test Manager"

def test_bulk_approve(client):
    employees = [
        {
            "id": "TEST005",
            "name": "Bulk Test One",
            "department": "Testing",
            "manager_name": "Test Manager",
            "email": "bulk1@example.com",
        },
        {
            "id": "TEST006",
            "name": "Bulk Test Two",
            "department": "Testing",
            "manager_name": "Test Manager",
            "email": "bulk2@example.com",
        },
    ]

    for employee in employees:
        response = client.post(
            "/api/v1/employees",
            json=employee,
            headers={"X-Operator": "pytest"},
        )

        assert response.status_code == 201

        attendance = {
            "employee_id": employee["id"],
            "work_date": "2026-08-17",
            "start_time": "2026-08-17T09:00:00",
        }

        response = client.post(
            "/api/v1/attendance",
            json=attendance,
            headers={"X-Operator": "pytest"},
        )

        assert response.status_code == 201

    response = client.post(
        "/api/v1/attendance/bulk-approve",
        json={
            "approver": "Bulk Manager",
            "exclude_employee_names": ["Bulk Test Two"],
        },
        headers={"X-Operator": "pytest"},
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data["approved_ids"]) == 1