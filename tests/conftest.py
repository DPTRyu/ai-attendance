import pytest

from fastapi.testclient import TestClient

import backend.database as database
from backend.main import app


@pytest.fixture
def client(tmp_path, monkeypatch):
    test_db_path = tmp_path / "test_attendance.db"

    database.DB_PATH = str(test_db_path)

    monkeypatch.setenv("ATTENDANCE_SEED", "false")

    with TestClient(app) as test_client:
        yield test_client