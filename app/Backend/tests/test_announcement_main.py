from unittest.mock import MagicMock, mock_open, patch

from Backend.announcement_feature.announcement_main import (
    main,  # rename to actual file path, e.g. Backend.announcement_feature.main
)

# Use a fixed patch target for consistent mocking
PATCH_FETCHER = "Backend.announcement_feature.announcement_main.AnnouncementFetcher"
PATCH_PARSER = "Backend.announcement_feature.announcement_main.AnnouncementParser"
PATCH_OPEN = "builtins.open"
PATCH_ENV = "Backend.announcement_feature.announcement_main.os.getenv"
PATCH_DOTENV = "Backend.announcement_feature.announcement_main.load_dotenv"


# ---- 1. Token is None → loads from dotenv ----
@patch(PATCH_FETCHER)
@patch(PATCH_DOTENV)
@patch(PATCH_ENV, return_value="FAKE_TOKEN")
def test_loads_env_token(mock_env, mock_dotenv, mock_fetcher):
    mock_instance = MagicMock()
    mock_instance.get_announcements.return_value = {}
    mock_fetcher.return_value = mock_instance

    result = main(None)
    mock_dotenv.assert_called_once()
    mock_env.assert_called_once_with("CANVAS_TOKEN")
    assert result == []


# ---- 2. No announcements found ----
@patch(PATCH_FETCHER)
def test_returns_empty_when_no_announcements(mock_fetcher):
    mock_instance = MagicMock()
    mock_instance.get_announcements.return_value = {}
    mock_fetcher.return_value = mock_instance

    result = main("token")
    assert result == []


# ---- 3. Announcement mentions midterm but also grades → skipped ----
@patch(PATCH_PARSER)
@patch(PATCH_FETCHER)
@patch(PATCH_OPEN, new_callable=mock_open)
def test_skips_grade_related_midterm(mock_openfile, mock_fetcher, mock_parser):
    mock_fetcher.return_value.get_announcements.return_value = {
        "CPEN_V 311 101 2025W1 Digital": [
            {"message": "Midterm grades are out!", "posted_at": "2025-10-10T00:00:00Z"}
        ]
    }
    result = main("token")
    assert result == []  # nothing parsed


# ---- 4. Valid midterm announcement → produces event ----
@patch(PATCH_PARSER)
@patch(PATCH_FETCHER)
@patch(PATCH_OPEN, new_callable=mock_open)
def test_extracts_midterm_and_builds_event(mock_openfile, mock_fetcher, mock_parser):
    mock_fetcher.return_value.get_announcements.return_value = {
        "CPEN_V 311 101 2025W1 Digital": [
            {
                "message": "Midterm is on 2025-10-23 at 15:00.",
                "posted_at": "2025-09-15T08:00:00Z",
            }
        ]
    }
    mock_parser.extract_midterm_dates.return_value = "2025-10-23T15:00:00"

    result = main("token")
    assert len(result) == 1
    event = result[0]
    assert event["course"] == "CPEN 311"
    assert event["event_type"] == "Midterm"
    assert event["begin_date_time"] == "15:00:00"
    assert event["end_date_time"] == "16:00:00"
    assert event["date"] == "2025/10/23"

    # file writing verified
    mock_openfile.assert_called_once_with("midterm_dates.json", "w")
    handle = mock_openfile()
    handle.write.assert_called()


# ---- 5. Parser returns None → no events added ----
@patch(PATCH_PARSER)
@patch(PATCH_FETCHER)
@patch(PATCH_OPEN, new_callable=mock_open)
def test_parser_returns_none(mock_openfile, mock_fetcher, mock_parser):
    mock_fetcher.return_value.get_announcements.return_value = {
        "CPEN_V 391 102 2025W1 Systems": [
            {
                "message": "Midterm details coming soon.",
                "posted_at": "2025-09-20T10:00:00Z",
            }
        ]
    }
    mock_parser.extract_midterm_dates.return_value = None
    result = main("token")
    assert result == []


# ---- 6. Midnight time → uses 12:00 / 1:00 branch ----
@patch(PATCH_PARSER)
@patch(PATCH_FETCHER)
@patch(PATCH_OPEN, new_callable=mock_open)
def test_midnight_time_branches(mock_openfile, mock_fetcher, mock_parser):
    mock_fetcher.return_value.get_announcements.return_value = {
        "CPEN_V 391 102 2025W1 Systems": [
            {
                "message": "Midterm is on 2025-10-20.",
                "posted_at": "2025-09-20T10:00:00Z",
            }
        ]
    }
    mock_parser.extract_midterm_dates.return_value = "2025-10-20T00:00:00"
    result = main("token")
    assert result[0]["begin_date_time"] == "12:00:00"
    assert result[0]["end_date_time"] == "1:00:00"
