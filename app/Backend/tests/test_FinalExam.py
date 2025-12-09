import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime
import json
import sys
import os

# --- Import Path Setup ---
# Add the parent directory to sys.path to allow imports from sibling directories.
# This assumes the file structure:
# /project_root
#    /final_exam_feature
#        FinalExam.py
#    /tests (or where this test file is)
#        test_final_exam_fetcher.py
# sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from Backend.final_exam_feature.FinalExam import FinalExamFetcher

# try:
#     from final_exam_feature.FinalExam import FinalExamFetcher
# except ImportError:
#     # Fallback if the folder name is different, or try direct import if in same dir
#     try:
#         from final_exam_feature.FinalExam import FinalExamFetcher
#     except ImportError:
#         raise ImportError("Could not locate FinalExam.py. Ensure the test file is in a directory sibling to 'final_exam_feature' or check the folder name.")

# --- Fixtures for Mock Data ---

@pytest.fixture
def mock_html_success():
    """Returns HTML simulating a found exam."""
    return """
    <div class="exam-content">
        <div class="datetime">Mon Apr 21 2025 | 12:00 pm</div>
        <div class="location">
            <div class="split">A-K</div>
            <div class="location-url">SRC A</div>
        </div>
        <div class="location">
            <div class="split">L-Z</div>
            <div class="location-url">SRC B</div>
        </div>
    </div>
    """

@pytest.fixture
def mock_html_no_exam():
    """Returns HTML simulating a response where no exam block exists."""
    return """
    <div class="some-other-content">
        No scheduled exams found.
    </div>
    """

@pytest.fixture
def mock_api_response_success(mock_html_success):
    """Simulates the JSON list returned by the AJAX endpoint."""
    return [
        {"command": "settings"},
        {
            "command": "insert",
            "method": "replaceWith",
            "selector": ".view-id-pi_exam_sched",
            "data": mock_html_success
        }
    ]

# --- Helper Method Tests ---

def test_date_parse():
    input_str = "Mon Apr 21 2025 | 12:00 pm"
    expected = "2025/04/21"
    assert FinalExamFetcher._date_parse(input_str) == expected

def test_time_parse():
    input_str = "Mon Apr 21 2025 | 12:00 pm"
    expected = "12:00:00"
    assert FinalExamFetcher._time_parse(input_str) == expected

def test_end_time():
    start_time = "12:00:00"
    expected = "14:30:00" # 2.5 hours later
    assert FinalExamFetcher._end_time(start_time) == expected

def test_end_time_rollover():
    """Test if time calculation handles hour rollover correctly."""
    start_time = "22:00:00"
    expected = "00:30:00" # Next day
    assert FinalExamFetcher._end_time(start_time) == expected

# --- Main Logic Tests (get_final) ---

@patch('requests.get')
def test_get_final_success(mock_get, mock_api_response_success):
    """Test happy path: valid course, valid HTML, successful parsing."""
    
    # Configure the mock
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = mock_api_response_success
    mock_get.return_value = mock_response

    course_name = "CPEN 221"
    result = FinalExamFetcher.get_final(course_name)

    # Assertions
    assert result is not None
    assert result['course'] == course_name
    assert result['event_type'] == "Final Exam"
    assert result['date'] == "2025/04/21"
    assert result['begin_date_time'] == "12:00:00"
    assert result['end_date_time'] == "14:30:00"
    # Check if locations were joined correctly
    assert "A-K: SRC A" in result['location']
    assert "L-Z: SRC B" in result['location']
    assert ", " in result['location']

@patch('requests.get')
def test_get_final_404_error(mock_get):
    """Test API returning a non-200 status code."""
    mock_response = MagicMock()
    mock_response.status_code = 404
    mock_get.return_value = mock_response

    result = FinalExamFetcher.get_final("CPEN 221")
    assert result is None

@patch('requests.get')
def test_get_final_no_exam_data(mock_get, mock_html_no_exam):
    """Test valid API response but HTML contains no exam info."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = [
        {
            "command": "insert",
            "data": mock_html_no_exam
        }
    ]
    mock_get.return_value = mock_response

    result = FinalExamFetcher.get_final("CPEN 221")
    assert result is None

@patch('requests.get')
def test_get_final_malformed_json(mock_get):
    """Test valid API response but JSON doesn't contain 'insert' command."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = [{"command": "alert", "data": "Something else"}]
    mock_get.return_value = mock_response

    result = FinalExamFetcher.get_final("CPEN 221")
    assert result is None

# --- Batch Logic Tests (get_finals) ---

@patch('requests.get')
def test_get_finals_batch(mock_get, mock_api_response_success):
    """
    Test processing a list of courses.
    Scenario: 
    - Course 1 returns valid data.
    - Course 2 returns None (e.g., 404).
    """
    
    # Mock for Success
    response_success = MagicMock()
    response_success.status_code = 200
    response_success.json.return_value = mock_api_response_success

    # Mock for Failure
    response_fail = MagicMock()
    response_fail.status_code = 404

    # side_effect allows us to define different return values for sequential calls
    # Sequence based on get_finals implementation (naive vs optimized):
    # Optimized: 1 call for CPEN 221 (Success), 1 call for INVALID 101 (Fail)
    # Naive (current): 2 calls for CPEN 221 (Check+Append), 1 call for INVALID 101
    
    # Assuming the code is currently Naive (calling get_final twice):
    mock_get.side_effect = [response_success, response_success, response_fail]

    courses = ["CPEN 221", "INVALID 101"]
    
    results = FinalExamFetcher.get_finals(courses)

    assert len(results) == 1
    assert results[0]['course'] == "CPEN 221"