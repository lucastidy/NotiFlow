# test_assignment_fetcher.py
import json
from datetime import datetime, timezone

from Backend.assignment_feature import AssignmentFetcher as af


def setup_function(_):
    af.classesValid.clear()
    af.classesIdValid.clear()
    af.classesAssignmentsValid.clear()
    af.NoDueDate.clear()
    af.classNames.clear()
    af.course_map.clear()


# ---------- simplify_name ----------

def test_simplify_name_too_few_parts():
    assert af.simplify_name("CPEN") is None


def test_simplify_name_no_number():
    assert af.simplify_name("CPEN ABC") is None


def test_simplify_name_short_dept():
    assert af.simplify_name("CS 221") is None


def test_simplify_name_normal_with_V_suffix():
    assert af.simplify_name("CPEN_V 221 Something") == "CPEN_V 221"


# ---------- is_due_in_future ----------

def test_is_due_in_future_true():
    future = "2099-01-01T00:00:00Z"
    assert af.is_due_in_future(future) is True


def test_is_due_in_future_false():
    past = "2000-01-01T00:00:00Z"
    assert af.is_due_in_future(past) is False


# ---------- is_current_term ----------

def test_is_current_term_missing_dates():
    assert af.is_current_term({"start_at": None, "end_at": None}) is False
    assert af.is_current_term({"start_at": None, "end_at": "2099-01-01T00:00:00Z"}) is False
    assert af.is_current_term({"start_at": "2099-01-01T00:00:00Z", "end_at": None}) is False


def test_is_current_term_now_inside():
    term = {
        "start_at": "2000-01-01T00:00:00Z",
        "end_at": "2099-01-01T00:00:00Z",
    }
    assert af.is_current_term(term) is True


def test_is_current_term_now_before_or_after():
    # now before start
    term_future = {
        "start_at": "2099-01-01T00:00:00Z",
        "end_at": "2100-01-01T00:00:00Z",
    }
    assert af.is_current_term(term_future) is False

    # now after end
    term_past = {
        "start_at": "1990-01-01T00:00:00Z",
        "end_at": "1991-01-01T00:00:00Z",
    }
    assert af.is_current_term(term_past) is False


# ---------- get_all_pages ----------

class DummyResponse:
    def __init__(self, data, link_header=""):
        self._data = data
        self.headers = {"Link": link_header} if link_header else {}

    def json(self):
        return self._data

    def raise_for_status(self):
        pass


def test_get_all_pages_multiple(monkeypatch):
    calls = []

    def fake_get(url, headers=None, params=None):
        calls.append(url)
        if "page=1" in url:
            # first page, has next
            return DummyResponse(
                [{"id": 1}],
                '<https://example.com/api?page=2>; rel="next"'
            )
        else:
            # second (last) page, no Link header
            return DummyResponse([{"id": 2}])

    monkeypatch.setattr(af.requests, "get", fake_get)

    url = "https://example.com/api?page=1"
    data = af.get_all_pages(url, headers={"Authorization": "Bearer X"})

    assert data == [{"id": 1}, {"id": 2}]
    assert len(calls) == 2


# --------- requestUrl ----------

def test_requestUrl_uses_canvas_base(monkeypatch):
    def fake_get_all_pages(url, headers, params=None):
        assert url.startswith("https://canvas.ubc.ca/api/v1/users/self/courses")
        return [{"dummy": True}]

    monkeypatch.setattr(af, "get_all_pages", fake_get_all_pages)

    token = "TEST_TOKEN"
    scope = "api/v1/users/self/courses?per_page=100"
    result = af.requestUrl(scope, token)
    assert result == [{"dummy": True}]


# -------- getClasses ---------

def test_getClasses_filters_by_name_and_term(monkeypatch):
    def fake_requestUrl(scope, token):
        return [
            {
                "name": None,
                "term": {"start_at": "2000-01-01T00:00:00Z", "end_at": "2099-01-01T00:00:00Z"},
                "id": 1,
            },
            {
                "name": "Old Course",
                "term": {"start_at": "1990-01-01T00:00:00Z", "end_at": "1991-01-01T00:00:00Z"},
                "id": 2,
            },
            {
                # This matches the real Canvas-ish pattern and your new simplify_name
                "name": "CPEN_V 221 101",
                "term": {"start_at": "2000-01-01T00:00:00Z", "end_at": "2099-01-01T00:00:00Z"},
                "id": 3,
            },
        ]

    monkeypatch.setattr(af, "requestUrl", fake_requestUrl)

    token = "X"
    result = af.getClasses(token)

    # simplified names
    assert result == ["CPEN_V 221"]
    # raw Canvas names
    assert af.classesValid == ["CPEN_V 221 101"]
    assert af.classesIdValid == [3]



# ---------- getAssignmentsClass ---------

def test_getAssignmentsClass_future_and_past_and_nodue(monkeypatch):
    def fake_requestUrl(scope, token):
        return [
            {"name": "Future A", "due_at": "2099-01-02T03:04:05Z"},
            {"name": "Past B", "due_at": "2000-01-02T03:04:05Z"},
            {"name": "No Due", "due_at": None, "course_Id": 42},
        ]

    monkeypatch.setattr(af, "requestUrl", fake_requestUrl)

    token = "XYZ"
    class_id = 123
    res = af.getAssignmentsClass(class_id, token)

    assert len(res) == 1
    name, date_part, time_part, raw_due = res[0]
    assert name == "Future A"
    assert date_part == "2099/01/02"
    assert time_part == "03:04:05"
    assert raw_due == "2099-01-02T03:04:05Z"

    assert len(af.NoDueDate) == 2
    titles = {row[0] for row in af.NoDueDate}
    assert titles == {"Past B", "No Due"}


# --------- getAssignmentsStudent --------

def test_mapCourses_various_branches(monkeypatch):

    af.classesValid[:] = [
        "CPEN Bad",          # bad name -> simplify_name is None
        "CPEN_V 221 A",      # normal
        "CPEN_V 221 B",      # same simplified key as previous with diff id
        "CPEN_V 221 A",      # same simplified key, same id as second -> duplicate id
    ]
    af.classesIdValid[:] = [1, 2, 3, 2]

    def fake_getClasses(token):
        # We don't touch the globals here, they are already set above
        return af.classesValid

    def fake_getAssignmentsClass(cid, token):
        return [f"Assignments for {cid}"]

    monkeypatch.setattr(af, "getClasses", fake_getClasses)
    monkeypatch.setattr(af, "getAssignmentsClass", fake_getAssignmentsClass)

    token = "TEST_TOKEN"
    result_json = af.mapCourses(token)
    result = json.loads(result_json)

    # Only the CPEN_V 221 key should exist (class id 1 is dropped, id 2 deduped)
    assert list(result.keys()) == ["CPEN_V 221"]
    c = result["CPEN_V 221"]

    # ids: [2, 3] (1 skipped, last 2 is duplicate -> not added)
    assert c["ids"] == [2, 3]
    assert c["classes"] == ["CPEN_V 221 A", "CPEN_V 221 B"]
    assert c["assignments"] == [
        ["Assignments for 2"],
        ["Assignments for 3"],
    ]