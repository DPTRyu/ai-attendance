import urllib.request
import json
import sys

BASE_URL = "http://127.0.0.1:8000/api/v1"

def api_request(path, method="GET", data=None, headers=None):
    url = f"{BASE_URL}{path}"
    req_headers = {"Content-Type": "application/json"}
    if headers:
        req_headers.update(headers)
        
    req_data = None
    if data is not None:
        req_data = json.dumps(data).encode("utf-8")
        
    req = urllib.request.Request(url, data=req_data, headers=req_headers, method=method)
    try:
        with urllib.request.urlopen(req) as res:
            return res.status, json.loads(res.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8")
        try:
            err_data = json.loads(body)
            detail = err_data.get("detail", body)
        except:
            detail = body
        print(f"Error {e.code} on {method} {path}: {detail}")
        return e.code, detail
    except Exception as e:
        print(f"Exception on {method} {path}: {str(e)}")
        return 500, str(e)

def run_tests():
    print("Starting API Verification...")
    
    # 1. Health check
    code, res = api_request("/health")
    assert code == 200, f"Health check failed with {code}"
    assert res["status"] == "ok", "Expected status ok"
    print("[OK] Health Check API passed")

    # 2. Get initial dashboard stats
    code, res = api_request("/dashboard")
    assert code == 200, f"Dashboard API failed with {code}"
    assert res["pending_approvals"] == 2, f"Expected 2 pending, got {res['pending_approvals']}"
    assert res["approved_today"] == 2, f"Expected 2 approved today, got {res['approved_today']}"
    assert "Charlie Brown" in res["pending_employee_names"], "Expected Charlie Brown in pending list"
    assert len(res["latest_logs"]) > 0, "Expected seed operation logs"
    print("[OK] Initial Dashboard Stats passed")

    # 3. Create Employee
    emp_payload = {
        "id": "EMP005",
        "name": "Frank Miller",
        "department": "Finance",
        "manager_name": "John Doe",
        "email": "frank@example.com"
    }
    code, res = api_request("/employees", method="POST", data=emp_payload, headers={"X-Operator": "SystemTest"})
    assert code == 201, f"Create employee failed with {code}"
    assert res["name"] == "Frank Miller", "Employee name mismatch"
    print("[OK] Create Employee API passed")

    # 4. Check if employee list updated
    code, res = api_request("/employees")
    assert code == 200
    ids = [e["id"] for e in res]
    assert "EMP005" in ids, "EMP005 not in list"
    print("[OK] Get Employees List passed")

    # 5. Create Attendance record
    att_payload = {
        "employee_id": "EMP005",
        "work_date": "2026-07-27",
        "start_time": "2026-07-27T09:30:00"
    }
    code, res = api_request("/attendance", method="POST", data=att_payload, headers={"X-Operator": "SystemTest"})
    assert code == 201, f"Create attendance failed with {code}"
    assert res["status"] == "Pending", "Expected Pending status"
    record_id = res["id"]
    print(f"[OK] Create Attendance API passed (Record ID: {record_id})")

    # 6. Verify pending list has the new record
    code, res = api_request("/attendance/pending")
    assert code == 200
    pending_ids = [r["id"] for r in res]
    assert record_id in pending_ids, "New record not in pending list"
    print("[OK] Get Pending Attendance passed")

    # 7. Approve the attendance record
    approve_payload = {"approver": "Test Manager"}
    code, res = api_request(f"/attendance/{record_id}/approve", method="POST", data=approve_payload, headers={"X-Operator": "SystemTest"})
    assert code == 200, f"Approve failed with {code}"
    assert res["status"] == "Approved", "Expected status to update to Approved"
    assert res["approver"] == "Test Manager", "Expected approver name to be set"
    print("[OK] Approve Attendance API passed")

    # 8. Check Dashboard stats updated
    code, res = api_request("/dashboard")
    assert code == 200
    # Initial pending was 2, went up to 3 when EMP005 registered, then back to 2 when approved.
    assert res["pending_approvals"] == 2, f"Expected 2 pending approvals, got {res['pending_approvals']}"
    # Today's approved count was 2, now should be 3 (since we approved EMP005's record for today's date)
    assert res["approved_today"] == 3, f"Expected 3 approved today, got {res['approved_today']}"
    # Verify audit trail logs updated
    operators = [log["operator"] for log in res["latest_logs"]]
    assert "SystemTest" in operators, "Expected SystemTest in audit logs operators"
    print("[OK] Dashboard Stats Update after approval passed")

    # 9. Verify bulk approve works with exclusion
    # Create another pending record
    att_payload2 = {
        "employee_id": "EMP003",
        "work_date": "2026-07-27",
        "start_time": "2026-07-27T10:30:00"
    }
    # EMP003 already has a seed record for today, but we can register attendance for yesterday to test bulk approval if needed.
    # Let's verify dashboard stats before bulk approval:
    code, res = api_request("/dashboard")
    assert res["pending_approvals"] == 2, f"Pending count before bulk approval: {res['pending_approvals']}"
    
    # Bulk approve, excluding Charlie Brown
    bulk_payload = {
        "approver": "Bulk Manager",
        "exclude_employee_names": ["Charlie Brown"]
    }
    code, res = api_request("/attendance/bulk-approve", method="POST", data=bulk_payload, headers={"X-Operator": "SystemTest"})
    assert code == 200
    assert res["approved_ids"] == [4], f"Expected only record 4 (Diana Prince) to be approved, got {res['approved_ids']}"
    print("[OK] Bulk Approve with Exclusions API passed")

    # 10. Reset Demo Data
    code, res = api_request("/demo/reset", method="POST")
    assert code == 200
    assert res["message"] == "Demo data has been reset."
    
    # Check dashboard is back to seeds
    code, res = api_request("/dashboard")
    assert res["pending_approvals"] == 2, f"After reset expected 2 pending, got {res['pending_approvals']}"
    assert res["approved_today"] == 2, f"After reset expected 2 approved, got {res['approved_today']}"
    print("[OK] Demo Reset API passed")

    print("\n[SUCCESS] ALL REST API ENDPOINTS VERIFIED SUCCESSFULLY!")

if __name__ == "__main__":
    try:
        run_tests()
    except AssertionError as e:
        print(f"\n[FAILED] VERIFICATION FAILED: {str(e)}")
        sys.exit(1)
