"""
Fetch courses and assignments from Canvas and map them into a simplified
course → assignments structure used by the NotiFlow backend.

This module:
- Fetches all Canvas courses for the user.
- Filters them to the current academic term.
- Normalizes course names (e.g., "CPEN_V 221 101" → "CPEN 221").
- Fetches upcoming assignments for each course.
- Produces a JSON-serializable mapping of simplified course codes to
  Canvas IDs, original class names, and assignment lists.
"""

import json
import re
from datetime import datetime, timezone

from dotenv import load_dotenv
import requests
import os

# Info Gathering
# -------------------------

def mapCourses(token: str) -> str:
    """
    Build a JSON mapping from simplified course codes to assignments.

    For each current-term Canvas course:
    - Simplifies the course name (e.g., "CPEN_V 221 101" → "CPEN 221").
    - Aggregates all Canvas course IDs that map to the same simplified code.
    - Fetches upcoming assignments for each course ID.

    Args:
        token: Canvas API access token for the current user.

    Returns:
        str: A JSON string representing a dict of the form:
            {
              "CPEN 221": {
                "ids": [12345, 67890],
                "classes": ["CPEN_V 221 101", "CPEN 221 102"],
                "assignments": [
                  [[name, date, time, iso_due_at], ...],  # for id 12345
                  [[name, date, time, iso_due_at], ...],  # for id 67890
                ]
              },
              ...
            }
    """
    course_map.clear()
    getClasses(token)

    for name, id in zip(classesValid, classesIdValid):
        key = simplify_name(name)

        if key is None:
            continue

        if key not in course_map:
            course_map[key] = {"ids": [], "classes": [], "assignments": []}

        if id not in course_map[key]["ids"]:
            course_map[key]["ids"].append(id)
            course_map[key]["classes"].append(name)
            course_map[key]["assignments"].append(getAssignmentsClass(id, token))

    data = json.dumps(course_map, indent=2)

    return data


def get_all_pages(url: str, headers: dict, params: dict | None = None) -> list:
    """
    Follow Canvas-style pagination and return all pages of results.

    This helper repeatedly calls the given URL, following the `Link` header
    with rel="next" until no further pages remain.

    Args:
        url: Initial request URL.
        headers: HTTP headers to include (e.g., Authorization).
        params: Optional query parameters for the first request.

    Returns:
        list: Concatenated list of JSON-decoded response objects from all pages.
    """

    all_data = []
    while url:
        r = requests.get(url, headers=headers, params=params)
        r.raise_for_status()
        all_data.extend(r.json())

        link = r.headers.get("Link", "")
        match = re.search(r'<([^>]+)>\s*;\s*rel="next"', link)
        url = match.group(1) if match else None

        params = None
    return all_data

load_dotenv()

classesValid: list[str] = []
classNames: list[str] = []
classesIdValid: list[str] = []
classesAssignmentsValid: list[str] = []
NoDueDate: list[str] = []
course_map: dict = {}
classes: set = set()


# gets the info from the requested URL
def requestUrl(requestScope: str, accessToken: str) -> list:
    """
    Perform a Canvas API request for a given scope and return all pages.

    Args:
        requestScope: Path + query string for the Canvas API
            (e.g., "api/v1/users/self/courses?per_page=100&...").
        accessToken: Canvas API access token.

    Returns:
        list: Aggregated JSON-decoded response from all pages.
    """

    headers = {"Authorization": f"Bearer {accessToken}"}

    canvasUBCBaseUrl = "https://canvas.ubc.ca/"

    requestUrl = canvasUBCBaseUrl + requestScope

    urlInfo = get_all_pages(requestUrl, headers)

    return urlInfo


# gets all the classes a student is enrolled in on Canvas
def getClasses(token: str) -> list[str]:
    """
    Populate global course lists with all current-term Canvas classes.

    Fetches all courses for the user, filters them to the current term,
    and stores names and IDs into `classesValid` and `classesIdValid`.

    Args:
        token: Canvas API access token.

    Returns:
        list[str]: The list of valid course names for the current term.
    """

    classesValid.clear()
    classesIdValid.clear()
    classNames.clear()
    classes.clear()

    requestScope = (
        "api/v1/users/self/courses?per_page=100&enrollment_state[]="
        "active&enrollment_state[]=completed&enrollment_state[]=invited_or_pending&state"
        "[]=available&state[]=completed&include[]=term&include[]=course_code"
    )

    classesInfo = requestUrl(requestScope, token)

    for classInfo in classesInfo:
        if classInfo.get("name") is not None:
            if is_current_term(classInfo.get("term")):
                classesValid.append(classInfo.get("name"))
                classesIdValid.append(classInfo.get("id"))

    for e in classesValid:
        classes.add(simplify_name(e))

    classNames.extend(x for x in classes if x is not None)

    return classNames


def is_due_in_future(due: str) -> bool:
    """
    Check whether a Canvas `due_at` timestamp is in the future.

    Args:
        due: ISO 8601 timestamp string from Canvas, e.g. "2025-11-29T23:59:00Z".

    Returns:
        bool: True if the due date is strictly in the future relative to now (UTC).
    """

    now = datetime.now(timezone.utc)
    due_dt = datetime.fromisoformat(due.replace("Z", "+00:00"))
    return due_dt > now


def is_current_term(term: str | None) -> bool:
    """
    Determine whether the current time falls within a Canvas term.

    Args:
        term: Dictionary containing at least `start_at` and `end_at` keys
            with ISO 8601 timestamps, or None.

    Returns:
        bool: True if the current UTC time is between start_at and end_at
        (inclusive), False otherwise or if dates are missing.
    """
        
    start = term.get("start_at")
    end = term.get("end_at")
    if not start or not end:
        return False
    now = datetime.now(timezone.utc)

    start = datetime.fromisoformat(start.replace("Z", "+00:00"))
    end = datetime.fromisoformat(end.replace("Z", "+00:00"))
    return start <= now <= end


def simplify_name(name: str) -> str | None:
    """
    Normalize a Canvas course name into `DEPT NUM` form.

    Expected input examples:
        - "CPEN_V 221 101"
        - "CPEN 221 L1A"

    Rules:
        - Requires at least two whitespace-separated parts.
        - Second token must start with digits (the course number).
        - Department token has `_V` removed and must be at least 4 chars.

    Args:
        name: Original Canvas course name.

    Returns:
        str | None: Simplified name like "CPEN 221", or None if the name
        does not match the expected pattern.
    """
    
    parts = name.split()
    if len(parts) < 2:
        return None

    m = re.match(r"\d+", parts[1])
    if not m:
        return None

    dept = parts[0]

    if len(dept) < 6:
        return None

    else:
        num = m.group(0)

    return f"{dept} {num}"


# gets the upcoming assignments for a specific class
def getAssignmentsClass(classId: int, token: str) -> list[list[str]]:
    """
    Fetch upcoming assignments for a specific Canvas course.

    Assignments with a non-null `due_at` in the future are included in the
    returned list. Others are recorded in `NoDueDate`.

    Args:
        classId: Canvas course ID.
        token: Canvas API access token.

    Returns:
        list[list[str]]: A list of assignments, each in the form:
            [name, "YYYY/MM/DD", "HH:MM:SS", raw_due_at_iso]
    """

    assignmentsClassNameDue: list[list[str]] = []

    requestScope = "api/v1/courses/" + str(classId) + "/assignments?per_page=100"

    assignmentsInfo = requestUrl(requestScope, token)

    for assignmentInfo in assignmentsInfo:
        if assignmentInfo.get("due_at") is not None and is_due_in_future(
            assignmentInfo.get("due_at")
        ):
            time = assignmentInfo.get("due_at")
            time = time.rstrip("Z")
            date_part, time_part = time.split("T")
            date_part = date_part.replace("-", "/")

            assignmentsClassNameDue.append(
                [
                    assignmentInfo.get("name"),
                    date_part,
                    time_part,
                    assignmentInfo.get("due_at"),
                ]
            )

        else:
            NoDueDate.append(
                [assignmentInfo.get("name"), assignmentInfo.get("course_Id")]
            )

    return assignmentsClassNameDue

if __name__ == "__main__":
    print(mapCourses(os.getenv('TOKEN')))