import json
import os
import re
from datetime import datetime
from zoneinfo import ZoneInfo

from dotenv import load_dotenv

from .announcement_fetcher import AnnouncementFetcher
from .announcement_parser import AnnouncementParser


def main(token):
    """
    Orchestrates fetching Canvas announcements and extracting midterm dates.

    This function:
      1. Loads a Canvas API token (from parameter or .env file).
      2. Uses `AnnouncementFetcher` to retrieve announcements grouped by course.
      3. Iterates over announcements, filtering those mentioning "midterm"
         (but ignoring grade-related posts).
      4. Calls `AnnouncementParser.extract_midterm_dates` to find an ISO date string.
      5. Converts that date into a local Pacific time event dictionary and
         appends it to a results list.
      6. Saves all found midterm events to `midterm_dates.json`.

    Args:
        token (str | None): Canvas API token. If `None`, loads from environment variable
            `CANVAS_TOKEN` in the .env file.

    Returns:
        list[dict[str, str]]: A list of midterm event objects with keys:
            - `"course"`: Course name (first two words, `_V` removed)
            - `"event_type"`: Always `"Midterm"`
            - `"begin_date_time"`: Start time in HH:MM:SS format
            - `"date"`: Date in YYYY/MM/DD format
            - `"end_date_time"`: End time one hour after start

    Raises:
        FileNotFoundError: If the working directory is unwritable for JSON output.
        ValueError: If parsed dates are invalid ISO strings.

    Notes:
        * Announcements containing words like "grades", "marks", "results", etc.
          are skipped even if they mention "midterm".
        * Only the first valid midterm date per course is recorded.
        * The JSON file is primarily for debugging and inspection.
    """
    if not token:
        load_dotenv()
        token = os.getenv("CANVAS_TOKEN")

    # first get announcements , sorted by course
    fetcher = AnnouncementFetcher(token)
    announcements = fetcher.get_announcements()

    # to be converted to final JSON obj
    output = []

    for course_name, announcements in announcements.items():
        # DEBUG
        # print(f"Processing course: {course_name}\n\n")
        midterm_date = None

        for ann in announcements:
            if re.search(r"\bmidterm\b", ann["message"], re.IGNORECASE):
                if re.search(
                    r"grades?|marks?|results?|scores?|passed?|failed?|review?",
                    ann["message"],
                    re.IGNORECASE,
                ):
                    continue  # ignore these announcements
            # DEBUG
            # print(f"message: {ann['message']} time: {ann['posted_at']}\n")
            utc_posted_at = datetime.fromisoformat(
                ann["posted_at"].replace("Z", "+00:00")
            )
            pst_posted_at = utc_posted_at.astimezone(ZoneInfo("America/Los_Angeles"))
            date = AnnouncementParser.extract_midterm_dates(
                ann["message"], posted_at=pst_posted_at.isoformat()
            )
            if date:
                midterm_date = date
                break  # stop after first found

        if midterm_date:
            dt = datetime.fromisoformat(midterm_date)
            time = (
                "12:00:00"
                if dt.hour == 0 and dt.minute == 0
                else f"{dt.hour:02}:{dt.minute:02}:00"
            )
            endTime = (
                "1:00:00"
                if dt.hour == 0 and dt.minute == 0
                else f"{(dt.hour + 1) % 24:02}:{dt.minute:02}:00"
            )
            course_name = " ".join(course_name.split(" ")[:2]).replace("_V", "")
            event = {
                "course": course_name,
                "event_type": "Midterm",
                "begin_date_time": time,
                "date": dt.strftime("%Y/%m/%d"),
                "end_date_time": endTime,
            }
            output.append(event)

    # DEBUG save as JSON file
    with open("midterm_dates.json", "w") as f:
        json.dump(output, f, indent=4)

    # DEBUG
    # print(json.dumps(output, indent=4))
    return output
