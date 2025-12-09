import re
from datetime import datetime, timedelta, timezone

import requests
from bs4 import BeautifulSoup

BASE_URL = "https://canvas.ubc.ca/api/v1"
START_TIME = 80  # days back to fetch announcements


class AnnouncementFetcher:
    """
    Fetches announcements from Canvas LMS courses for the current term.

    This class interacts with the Canvas REST API to:
      - Retrieve all active courses in the current term
      - Fetch recent announcements for those courses
      - Convert announcement HTML messages to plain text
      - Group announcements by course name

    Attributes:
        token (str): Canvas API authentication token.
        course_names (dict[int, str]): Maps course IDs to their corresponding names.
        course_ids (list[int]): List of course IDs for the current term.
    """

    def __init__(self, token):
        """
        Initializes the AnnouncementFetcher with a valid Canvas API token.

        Args:
            token (str): A valid Canvas API token for authorization.

        Raises:
            ValueError: If the token is None or invalid.
        """
        if token is None:
            raise ValueError("token must be a valid Canvas API token")
        self.token = token
        self.course_names = {}
        self.course_ids = self.get_course_ids()

    def is_current_term(self, term):
        """
        Determines whether a given Canvas term is currently active.

        Args:
            term (dict): A term object returned by the Canvas API.
                Expected keys include "start_at" and "end_at" (ISO-8601 format).

        Returns:
            bool: True if the term start/end dates include the current UTC time; False otherwise.
        """
        start = term.get("start_at")
        end = term.get("end_at")
        if not start or not end:
            return False
        now = datetime.now(timezone.utc)

        start = datetime.fromisoformat(start.replace("Z", "+00:00"))
        end = datetime.fromisoformat(end.replace("Z", "+00:00"))
        return start <= now <= end

    def get_course_ids(self):
        """
        Retrieves the IDs of all active courses for the current term.

        This function paginates through all user-accessible courses via
        the Canvas `/courses` endpoint, filtering out inactive or restricted ones.

        Returns:
            list[int]: A list of Canvas course IDs for active current-term courses.
        """
        course_ids = set()
        page = 1
        params = {
            "include[]": "term"
        }  # if we need others later add here, cant be incremental
        while True:
            r = requests.get(
                f"{BASE_URL}/courses",
                headers={"Authorization": f"Bearer {self.token}"},
                params={**params, "page": page},
            )
            data = r.json()

            if not isinstance(data, list) or len(data) == 0:
                break

            for course in data:
                if (
                    course.get("id") not in course_ids
                    and course.get("access_restricted_by_date") is None
                ):
                    if self.is_current_term(course.get("term")):
                        course_ids.add(course.get("id"))
                        self.course_names[course.get("id")] = course.get("name")
            page += 1

        return list(course_ids)

    def get_announcements(self):
        """
        Fetches announcements for all current-term courses within a recent time window.

        Returns:
            dict[str, list[dict]]: A mapping of course names to lists of announcements.
            Each announcement is represented as:
                {
                    "posted_at": str (ISO datetime),
                    "message": str (plain text message)
                }
        """
        params = []
        for c in self.course_ids:
            params.append(("context_codes[]", f"course_{c}"))

        cutoff = datetime.now(timezone.utc) - timedelta(days=START_TIME)
        cutoff = cutoff.isoformat().replace("+00:00", "Z")
        params.append(("start_date", cutoff))

        announcementsByCourse = {}
        seen_ids = set()
        for course_id in self.course_ids:
            url = f"{BASE_URL}/announcements"
            r = requests.get(
                url, headers={"Authorization": f"Bearer {self.token}"}, params=params
            )
            data = r.json()
            for a in data:
                id = a.get("id")
                if id in seen_ids:
                    continue
                seen_ids.add(id)
                context = a.get("context_code")
                if context is not None:
                    id = int(context.split("_")[1])
                    course_name = self.course_names.get(id)
                    if course_name not in announcementsByCourse:
                        announcementsByCourse[course_name] = []
                    msg = a.get("message")
                    posted_at = a.get("posted_at")
                    if msg and posted_at:
                        msg_text = self.html_to_string(msg)
                        announcementsByCourse[course_name].append(
                            {"posted_at": posted_at, "message": msg_text}
                        )
            for course_name, msgs in announcementsByCourse.items():
                msgs.sort(key=lambda x: x["posted_at"])  # sort by posted_at ascending
        return announcementsByCourse

    def html_to_string(self, html):
        """
        Converts an HTML message body into clean plain text.

        Args:
            html (str): Raw HTML content from a Canvas announcement.

        Returns:
            str: Cleaned, readable plain text string.
        """
        if not html:
            return ""

        parsed = BeautifulSoup(html, "html.parser")
        text = parsed.get_text(separator=" ", strip=True)
        text = text.replace("\xa0", "").strip()
        text = re.sub(r"\s+([.,!?;:])", r"\1", text)  # collapse multiple spaces
        return text


# DEBUG
# if __name__ == "__main__":
#     load_dotenv()
#     token = os.getenv("CANVAS_TOKEN")
#     fetcher = AnnouncementFetcher(token)
#     for key, value in fetcher.announcements.items():
#         for announcement in value:
#             print(f"COURSE: {key} \nANNOUNCEMENT: \n{announcement}")
