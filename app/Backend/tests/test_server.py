import os
import sys
import pytest

# --- make Backend dir importable so `import server` works no matter how uv/pytest runs ---

CURRENT_DIR = os.path.dirname(__file__)          # .../app/Backend/tests
BACKEND_DIR = os.path.dirname(CURRENT_DIR)       # .../app/Backend

if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

import Backend.server as server


@pytest.fixture
def client():
    server.app.testing = True
    return server.app.test_client()


# ---------- Fake ICalHandler for announcements/assignments/finals ----------

class FakeICalHandler:
    """Simple fake to track how ICalHandler is used."""
    instances = []

    def __init__(self, token):
        self.token = token
        self.processed = None
        self.saved = False
        FakeICalHandler.instances.append(self)

    def process_json(self, data):
        self.processed = data

    # If you later switch announcements/assignments to use process_assignments, we support that too:
    def process_assignments(self, data):
        self.processed = data

    def save_calendar(self):
        self.saved = True


# ---------- /api/courses ----------

def test_classes_success(client, monkeypatch):
    called = {}

    def fake_getClasses(token):
        called["token"] = token
        return ["CPEN 221", "MATH 220"]

    monkeypatch.setattr(server, "getClasses", fake_getClasses)

    resp = client.get("/api/courses?token=test-token-123")
    assert resp.status_code == 200
    assert resp.get_json() == ["CPEN 221", "MATH 220"]
    assert called["token"] == "test-token-123"


def test_classes_no_token(client, monkeypatch):
    """Covers behaviour when token is missing (token=None)."""
    captured = {}

    def fake_getClasses(token):
        captured["token"] = token
        return []

    monkeypatch.setattr(server, "getClasses", fake_getClasses)

    resp = client.get("/api/courses")
    assert resp.status_code == 200
    assert resp.get_json() == []
    # Make sure None is passed through
    assert captured["token"] is None


# ---------- /api/finalexam ----------

def test_finalexam_success(client, monkeypatch):
    # Reset fake state so tests don't interfere with each other
    FakeICalHandler.instances = []

    called = {}

    def fake_get_finals(courses):
        called["courses"] = courses
        # Return some JSON-serializable structure
        return {"finals": [{"course": c, "date": "2099-01-01"} for c in courses]}

    # Patch the FinalExamFetcher used inside server.py
    monkeypatch.setattr(server.fe, "get_finals", fake_get_finals)
    # Patch ICalHandler so we don't hit the real calendar code
    monkeypatch.setattr(server, "ICalHandler", FakeICalHandler)

    resp = client.get("/api/finalexam?course[]=CPEN_221&course[]=MATH_220")
    assert resp.status_code == 200
    data = resp.get_json()
    assert "finals" in data
    assert len(data["finals"]) == 2
    assert called["courses"] == ["CPEN_221", "MATH_220"]


def test_finalexam_empty_list(client, monkeypatch):
    """Covers branch where getlist returns empty list."""
    FakeICalHandler.instances = []

    called = {"courses": None}

    def fake_get_finals(courses):
        called["courses"] = courses
        return {"finals": []}

    monkeypatch.setattr(server.fe, "get_finals", fake_get_finals)
    monkeypatch.setattr(server, "ICalHandler", FakeICalHandler)

    resp = client.get("/api/finalexam")  # no course[] query params
    assert resp.status_code == 200
    assert resp.get_json() == {"finals": []}
    assert called["courses"] == []


# ---------- /api/announcements ----------

def test_announcements_success(client, monkeypatch):
    FakeICalHandler.instances = []

    # Replace ICalHandler with our fake one
    monkeypatch.setattr(server, "ICalHandler", FakeICalHandler)

    def fake_announcement_main(token):
        # return some JSON-serializable structure
        return {"announcements": [{"title": "Hello", "course": "CPEN 221"}]}

    monkeypatch.setattr(server, "announcement_main", fake_announcement_main)

    resp = client.get("/api/announcements?token=my-ann-token")
    assert resp.status_code == 200

    # Flask will JSONify dict return values into a proper JSON response
    data = resp.get_json()
    assert data == {"announcements": [{"title": "Hello", "course": "CPEN 221"}]}

    # Check that ICalHandler was used correctly
    assert len(FakeICalHandler.instances) == 1
    handler = FakeICalHandler.instances[0]
    assert handler.token == "my-ann-token"
    assert handler.processed == data
    assert handler.saved is True


def test_announcements_failure(client, monkeypatch):
    """Force an exception to cover the error branch and 500 response."""
    FakeICalHandler.instances = []

    monkeypatch.setattr(server, "ICalHandler", FakeICalHandler)

    def fake_announcement_main(token):
        raise RuntimeError("boom!")

    monkeypatch.setattr(server, "announcement_main", fake_announcement_main)

    resp = client.get("/api/announcements?token=bad-token")
    assert resp.status_code == 500
    data = resp.get_json()
    assert "error" in data
    # Optional: check the error message we raised is included
    assert "boom" in data["error"]


# ---------- /api/assignments ----------

def test_assignments_success(client, monkeypatch):
    FakeICalHandler.instances = []

    monkeypatch.setattr(server, "ICalHandler", FakeICalHandler)

    called = {}

    def fake_mapCourses(token):
        called["token"] = token
        # Can be whatever your real function returns; use dict for clean JSON
        return {"assignments": [{"name": "PA1", "due": "2099-01-01"}]}

    monkeypatch.setattr(server, "mapCourses", fake_mapCourses)

    resp = client.get("/api/assignments?token=assign-token-42")
    assert resp.status_code == 200

    # They return assignments directly (not jsonify), but Flask will still
    # convert a dict to a proper JSON response.
    data = resp.get_json()
    assert data == {"assignments": [{"name": "PA1", "due": "2099-01-01"}]}
    assert called["token"] == "assign-token-42"


def test_assignments_failure(client, monkeypatch):
    """Covers exception path and 500 response for /api/assignments."""
    FakeICalHandler.instances = []

    monkeypatch.setattr(server, "ICalHandler", FakeICalHandler)

    def fake_mapCourses(token):
        raise ValueError("assignments exploded")

    monkeypatch.setattr(server, "mapCourses", fake_mapCourses)

    resp = client.get("/api/assignments?token=bad-token")
    assert resp.status_code == 500
    data = resp.get_json()
    assert "error" in data
    assert "assignments exploded" in data["error"]
