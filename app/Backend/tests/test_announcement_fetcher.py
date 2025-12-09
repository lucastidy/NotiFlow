from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest

from Backend.announcement_feature.announcement_fetcher import AnnouncementFetcher

PATCH_GET = "Backend.announcement_feature.announcement_fetcher.requests.get"
# ---- Fixtures ----


@pytest.fixture
def mock_fetcher():
    f = AnnouncementFetcher.__new__(AnnouncementFetcher)
    f.course_names = {}
    f.course_ids = []
    return f  # bypass __init__ for isolated tests


# ---- Tests ----


def test_init_raises_on_none_token():
    with pytest.raises(ValueError):
        AnnouncementFetcher(None)


@patch.object(AnnouncementFetcher, "get_course_ids", return_value=[101])
def test_init_stores_token_and_courses(mock_get_ids):
    f = AnnouncementFetcher("abc123")
    assert f.token == "abc123"
    assert f.course_ids == [101]


def test_is_current_term_true(mock_fetcher):
    now = datetime.now(timezone.utc)
    term = {
        "start_at": (now.replace(hour=0).isoformat()),
        "end_at": (now.replace(hour=23).isoformat()),
    }
    assert mock_fetcher.is_current_term(term) is True


def test_is_current_term_none(mock_fetcher):
    now = datetime.now(timezone.utc)
    term = {"start_at": None, "end_at": (now.replace(hour=23).isoformat())}
    assert mock_fetcher.is_current_term(term) is False


def test_is_current_term_false(mock_fetcher):
    past = datetime(2020, 1, 1, tzinfo=timezone.utc).isoformat()
    future = datetime(2021, 1, 1, tzinfo=timezone.utc).isoformat()
    assert mock_fetcher.is_current_term({"start_at": past, "end_at": future}) is False


def test_html_to_string_removes_tags(mock_fetcher):
    html = "<p>plzScale <b>this course</b>!This is a Test</p>"
    out = mock_fetcher.html_to_string(html)
    assert out == "plzScale this course!This is a Test"


def test_html_to_string_with_none(mock_fetcher):
    html = None
    out = mock_fetcher.html_to_string(html)
    assert out == ""


@patch("requests.get")
def test_get_course_ids_filters_current_term(mock_get, mock_fetcher):
    # Mock API returning two courses, only one active
    mock_fetcher.is_current_term = MagicMock(side_effect=[True, False])
    mock_get.return_value.json.side_effect = [
        [
            {
                "id": 101,
                "name": "CPEN 311",
                "term": {},
                "access_restricted_by_date": None,
            },
            {
                "id": 202,
                "name": "CPEN 391",
                "term": {},
                "access_restricted_by_date": None,
            },
        ],
        [],  # stop pagination
    ]
    mock_fetcher.token = "token"
    result = mock_fetcher.get_course_ids()
    assert result == [101]


@patch("requests.get")
def test_get_announcements_groups_by_course(mock_get, mock_fetcher):
    mock_fetcher.token = "token"
    mock_fetcher.course_ids = [123]
    mock_fetcher.course_names = {123: "CPEN 311"}
    mock_fetcher.html_to_string = lambda x: "Parsed message"

    mock_get.return_value.json.return_value = [
        {
            "id": 1,
            "context_code": "course_123",
            "message": "<p>Hello</p>",
            "posted_at": "2025-11-27T00:00:00Z",
        }
    ]

    result = mock_fetcher.get_announcements()
    assert "CPEN 311" in result
    assert len(result["CPEN 311"]) == 1
    assert result["CPEN 311"][0]["message"] == "Parsed message"


@patch(PATCH_GET)
def test_duplicate_id_skipped(mock_get, mock_fetcher):
    mock_fetcher.token = "token"
    now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    mock_fetcher.course_ids = [123]
    mock_fetcher.course_names = {123: "CPEN 311"}

    mock_get.return_value.json.return_value = [
        {
            "id": 1,
            "context_code": "course_123",
            "message": "<p>First</p>",
            "posted_at": now,
        },
        {
            "id": 1,
            "context_code": "course_123",
            "message": "<p>Dup</p>",
            "posted_at": now,
        },
    ]

    result = mock_fetcher.get_announcements()
    assert list(result.keys()) == ["CPEN 311"]
    assert len(result["CPEN 311"]) == 1
    assert result["CPEN 311"][0]["message"] == "First"


# --- Missing context_code (covers: if context is not None False branch) ---
@patch(PATCH_GET)
def test_missing_context_skipped(mock_get, mock_fetcher):
    mock_fetcher.token = "token"
    now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    mock_fetcher.course_ids = [123]
    mock_fetcher.course_names = {123: "CPEN 311"}

    mock_get.return_value.json.return_value = [
        {"id": 10, "context_code": None, "message": "<p>Ignored</p>", "posted_at": now}
    ]

    result = mock_fetcher.get_announcements()
    assert result == {}


# --- Course name not yet in announcementsByCourse (True branch) ---
@patch(PATCH_GET)
def test_new_course_entry_created(mock_get, mock_fetcher):
    mock_fetcher.token = "token"
    now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    mock_fetcher.course_ids = [123]
    mock_fetcher.course_names = {123: "CPEN 311"}

    mock_get.return_value.json.return_value = [
        {
            "id": 20,
            "context_code": "course_123",
            "message": "<p>Hello</p>",
            "posted_at": now,
        }
    ]

    result = mock_fetcher.get_announcements()
    assert "CPEN 311" in result
    assert result["CPEN 311"][0]["message"] == "Hello"


# --- Missing msg or posted_at (covers: if msg and posted_at False) ---
@patch(PATCH_GET)
def test_missing_message_or_posted_at_skipped(mock_get, mock_fetcher):
    mock_fetcher.token = "token"
    mock_fetcher.course_ids = [123]
    mock_fetcher.course_names = {123: "CPEN 311"}

    mock_get.return_value.json.return_value = [
        {
            "id": 30,
            "context_code": "course_123",
            "message": None,
            "posted_at": "2025-01-01T00:00:00Z",
        },
        {
            "id": 31,
            "context_code": "course_123",
            "message": "<p>Hi</p>",
            "posted_at": None,
        },
    ]

    result = mock_fetcher.get_announcements()
    assert result == {"CPEN 311": []}


# --- Invalid response type (covers: if not isinstance(data, list)) ---
@patch(PATCH_GET)
def test_invalid_response_type(mock_get, mock_fetcher):
    mock_fetcher.token = "token"
    mock_fetcher.course_ids = [123]
    mock_fetcher.course_names = {123: "CPEN 311"}

    mock_get.return_value.json.return_value = {}  # not a list

    result = mock_fetcher.get_announcements()
    assert result == {}
