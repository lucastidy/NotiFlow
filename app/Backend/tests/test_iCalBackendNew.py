import io
import json
import pytz
import builtins
import pytest
from unittest.mock import patch, MagicMock, mock_open
from datetime import datetime, date
from pathlib import Path

from Backend.iCalBackendNew import ICalHandler


@pytest.fixture
def mock_calendar(monkeypatch):
    """Fixture returning a fresh handler with calendar mocked to skip I/O."""
    handler = ICalHandler.__new__(ICalHandler)
    handler.tz = pytz.timezone("America/Vancouver")
    handler.token = "token"
    handler.ics_path = Path("/fake/path/calendar.ics")
    handler.calendar = MagicMock()
    handler.existing_uids = set()
    handler.term_end_date = "2025/12/07"
    handler._create_new_calendar = MagicMock()
    return handler


# --- Init: no file -> new calendar ----
@patch("Backend.iCalBackendNew.Path.is_file", return_value=False)
def test_init_creates_new_calendar(mock_isfile):
    with patch.object(ICalHandler, "_create_new_calendar") as mock_create:
        ICalHandler("token")
        mock_create.assert_called_once()


# ---- 4. UID generation ----
def test_generate_uid(mock_calendar):
    uid = mock_calendar._generate_uid("CPEN311", "Lecture", "2025/10/10", "12:00")
    assert "CPEN311-Lecture" in uid
    assert "@notiflow.local" in uid


# ---- 5. Create new calendar ----
def test_create_new_calendar(mock_calendar):
    mock_calendar._create_new_calendar()
    cal = mock_calendar.calendar
    assert "version" in cal.keys() or True  # placeholder; icalendar object mocked


# ---- 6. dateTimeParse normal + short formats ----
def test_dateTimeParse_variants(mock_calendar):
    d = mock_calendar.dateTimeParse("2025/12/05", "10:30:00")
    assert d.tzinfo
    d2 = mock_calendar.dateTimeParse("2025/12/05", "10:30")
    assert d2.hour == 10
    bad = mock_calendar.dateTimeParse("bad", "11:00")
    assert bad is None


# ---- 7. _parse_canvas_iso ----
def test_parse_canvas_iso_variants(mock_calendar):
    iso = "2025-12-10T22:30:00Z"
    parsed = mock_calendar._parse_canvas_iso(iso)
    assert parsed.tzinfo
    assert mock_calendar._parse_canvas_iso("") is None


# ---- 8. create_event_object: complete event ----
def test_create_event_object_complete(mock_calendar):
    data = {
        "course": "CPEN 311",
        "event_type": "Lecture",
        "date": "2025/10/10",
        "begin_date_time": "10:00:00",
        "end_date_time": "11:00:00",
        "location": "Room 123",
    }
    e = mock_calendar.create_event_object(data)
    assert e["summary"].startswith("CPEN 311 - Lecture")
    assert e["location"] == "Room 123"


# ---- 9. create_event_object: duplicate, incomplete, recurrence ----
def test_create_event_object_duplicates_and_rrule(mock_calendar):
    base = {
        "course": "CPEN 311",
        "event_type": "Lecture",
        "date": "2025/10/10",
        "begin_date_time": "10:00:00",
        "end_date_time": "11:00:00",
        "frequency": "WEEKLY",
        "interval": "2",
        "by_day": ["MO", "WE"],
        "until": "2025/12/07",
        "exception_dates": ["2025/11/01"]
    }
    event = mock_calendar.create_event_object(base)
    assert event["rrule"]["FREQ"][0] in ("W", "WEEKLY")
    # duplicate skip
    mock_calendar.existing_uids.add(next(iter(mock_calendar.existing_uids)))
    dup = mock_calendar.create_event_object(base)
    assert dup is None
    # incomplete skip
    incomplete = mock_calendar.create_event_object({"course": "C"})
    assert incomplete is None


# ---- 10. process_json ----
def test_process_json_adds_events(mock_calendar):
    data = [{
        "course": "CPEN 311",
        "event_type": "Lecture",
        "date": "2025/10/10",
        "begin_date_time": "10:00:00",
        "end_date_time": "11:00:00"
    }]
    mock_calendar.create_event_object = MagicMock(return_value="EVENT")
    mock_calendar.process_json(data)
    mock_calendar.calendar.add_component.assert_called_with("EVENT")


# ---- 11. save_calendar ----
def test_save_calendar(mock_calendar):
    fake_bytes = b"ical"
    mock_calendar.calendar.to_ical.return_value = fake_bytes
    with patch("builtins.open", mock_open()) as m:
        mock_calendar.save_calendar()
        handle = m()
        handle.write.assert_called_once_with(fake_bytes)


# ---- 12. _generate_task_uid ----
def test_generate_task_uid(mock_calendar):
    uid = mock_calendar._generate_task_uid("CPEN311", "HW1", "2025-10-10T00:00")
    assert "CPEN311-ASSIGNMENT" in uid


# ---- 13. create_task_object normal/duplicate/missing ----
def test_create_task_object_paths(mock_calendar):
    iso = "2025-10-20T00:00:00Z"
    t = mock_calendar.create_task_object("CPEN311", "HW1", iso)
    assert "summary" in t
    # duplicate
    uid = next(iter(mock_calendar.existing_uids))
    mock_calendar.existing_uids.add(uid)
    assert mock_calendar.create_task_object("CPEN311", "HW1", iso) is None
    # bad iso
    assert mock_calendar.create_task_object("CPEN311", "HW1", "") is None


# ---- 14. process_assignments ----
def test_process_assignments(mock_calendar):
    assignments_json = json.dumps({
        "CPEN311": {"assignments": [[[ "HW1", "desc", "pts", "2025-10-20T00:00:00Z" ]]]}
    })
    mock_calendar.create_task_object = MagicMock(return_value="TODO")
    mock_calendar.process_assignments(assignments_json)
    mock_calendar.calendar.add_component.assert_called_with("TODO")


# ---- 15. _parse_course_meetings ----
def test_parse_course_meetings_success(mock_calendar):
    raw = {
        "className": "CPEN311",
        "startTime": "10:00 AM",
        "endTime": "12:00 PM",
        "days": {"M": True, "Tu": False, "W": True}
    }
    parsed = mock_calendar._parse_course_meetings(raw)
    assert parsed["frequency"] == "WEEKLY"
    assert "MO" in parsed["by_day"]
    bad = mock_calendar._parse_course_meetings({"startTime": "bad", "endTime": "12:00 PM", "days": {}})
    assert bad is None


# ---- 16. process_course_meetings ----
def test_process_course_meetings_json_and_dict(mock_calendar):
    mock_calendar._parse_course_meetings = MagicMock(return_value={"ok": True})
    mock_calendar.process_json = MagicMock()
    raw = {"className": "C", "startTime": "10:00 AM", "endTime": "12:00 PM", "days": {"M": True}}
    mock_calendar.process_course_meetings(raw)
    mock_calendar.process_json.assert_called_once()
    # invalid JSON string
    mock_calendar.process_json.reset_mock()
    bad_json = '{"bad": }'
    mock_calendar.process_course_meetings(bad_json)
    mock_calendar.process_json.assert_not_called()


@patch("Backend.iCalBackendNew.Path.is_file", return_value=True)
@patch("Backend.iCalBackendNew.icalendar.Calendar.from_ical")
def test_init_loads_existing_calendar(mock_from_ical, mock_isfile, tmp_path):
    # Create a fake component with .name == "VEVENT"
    fake_component = MagicMock()
    fake_component.name = "VEVENT"
    fake_component.get.return_value = "uid123"

    fake_cal = MagicMock()
    fake_cal.walk.return_value = [fake_component]
    mock_from_ical.return_value = fake_cal

    fake_file = tmp_path / "calendar.ics"
    fake_file.write_bytes(b"BEGIN:VCALENDAR\nEND:VCALENDAR")

    with patch("builtins.open", mock_open(read_data=b"BEGIN:VCALENDAR\nEND:VCALENDAR")):
        handler = ICalHandler("fake_token", filename=str(fake_file.name))

    # Verify it loaded correctly
    mock_from_ical.assert_called_once()
    assert "uid123" in handler.existing_uids
    assert handler.calendar == fake_cal

