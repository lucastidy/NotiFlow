from unittest.mock import MagicMock, patch

from Backend.announcement_feature.announcement_parser import AnnouncementParser

PATCH_CLIENT = "Backend.announcement_feature.announcement_parser.OpenAI"


# ---- 1. No midterm mention → early return (covers: if not midterm_sentences) ----
@patch(PATCH_CLIENT)
def test_returns_none_when_no_midterm(mock_openai):
    """Should return None when no 'midterm' is found."""
    mock_openai.return_value = MagicMock()  # avoid needing a real key
    text = "Reminder: project report due next week. See syllabus."
    result = AnnouncementParser.extract_midterm_dates(text, "2025-10-01T12:00:00Z")
    assert result is None


# ---- 2. Normal OpenAI call path ----
@patch(PATCH_CLIENT)
def test_calls_openai_and_returns_output(mock_openai):
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.output_text = "2025-10-23T15:00"
    mock_client.responses.create.return_value = mock_response
    mock_openai.return_value = mock_client

    text = "Midterm is on October 23 at 3 PM!"
    result = AnnouncementParser.extract_midterm_dates(text, "2025-10-01T12:00:00Z")

    mock_openai.assert_called_once()
    mock_client.responses.create.assert_called_once()
    assert result == "2025-10-23T15:00"


# ---- 3. Strip output text ----
@patch(PATCH_CLIENT)
def test_strips_output_text(mock_openai):
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.output_text = "   2025-11-02   "
    mock_client.responses.create.return_value = mock_response
    mock_openai.return_value = mock_client

    text = "Midterm is on November 2."
    result = AnnouncementParser.extract_midterm_dates(text, "2025-10-01T12:00:00Z")
    assert result == "2025-11-02"


# ---- 4. Prompt formatting ----
@patch(PATCH_CLIENT)
def test_prompt_contains_posted_at_and_sentence(mock_openai):
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.output_text = "2025-10-23"
    mock_client.responses.create.return_value = mock_response
    mock_openai.return_value = mock_client

    text = "Midterm will be held October 23."
    posted_at = "2025-09-15T08:00:00Z"

    AnnouncementParser.extract_midterm_dates(text, posted_at)

    args, kwargs = mock_client.responses.create.call_args
    prompt_text = kwargs["input"]
    assert "Midterm" in prompt_text
    assert posted_at in prompt_text
    assert "ISO 8601" in prompt_text


# ---- 5. Multiple midterm sentences ----
@patch(PATCH_CLIENT)
def test_multiple_midterm_sentences(mock_openai):
    text = "Midterm 1 on Feb 1. Midterm 2 on Mar 3!"
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.output_text = "2025-02-01"
    mock_client.responses.create.return_value = mock_response
    mock_openai.return_value = mock_client

    result = AnnouncementParser.extract_midterm_dates(text, "2025-01-01T00:00:00Z")
    assert result == "2025-02-01"
    joined = mock_client.responses.create.call_args.kwargs["input"]
    assert "Midterm 1" in joined and "Midterm 2" in joined
