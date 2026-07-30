import requests

BASE_URL = "http://attendance-api:8000/api/v1"


def get_pending_attendance():

    response = requests.get(
        f"{BASE_URL}/attendance/pending"
    )

    response.raise_for_status()

    return response.json()


def bulk_approve(exclude_names):

    response = requests.post(
        f"{BASE_URL}/attendance/bulk-approve",
        json={
            "approver": "MCP",
            "exclude_employee_names": exclude_names,
        },
    )

    response.raise_for_status()

    return response.json()