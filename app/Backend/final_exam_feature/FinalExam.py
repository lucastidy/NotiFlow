from datetime import datetime, timedelta
import requests
from bs4 import BeautifulSoup


class FinalExamFetcher:
    """
    A utility class to scrape and parse final exam schedules from the UBC student services website.

    Attributes:
        url (str): The endpoint URL for the exam schedule AJAX requests.
        headers (dict): Standard HTTP headers to mimic a browser request.
    """
    url = "https://legacy.students.ubc.ca/views/ajax"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "X-Requested-With": "XMLHttpRequest",
    }

    def __init__(self):
        """Initializes the FinalExamFetcher instance."""
        pass

    def get_final(course):
        """
        Fetches and parses the final exam information for a specific course.

        Args:
            course (str): The course identifier formatted as "{Department code} {Course number}".
                Example: "CPEN 221"

        Returns:
            dict: A dictionary containing final exam details (date, time, location, etc.)
                adhering to the format specified in "json_object_format.md".
            None: If the API request fails, the HTML cannot be parsed, or the course is invalid.
        """
        params = {
            "view_name": "pi_exam_sched",
            "view_display_id": "block_main",
            "view_args": "",
            "course": course,
        }

        response = requests.get(
            FinalExamFetcher.url, params=params, headers=FinalExamFetcher.headers
        )

        if response.status_code == 200:
            data = response.json()

            html_content = None
            for item in data:
                if item.get("command") == "insert" and "data" in item:
                    html_content = item["data"]
                    break

            # html parsing with beautifulsoup
            if html_content:
                soup = BeautifulSoup(html_content, "html.parser")

                exam_div = soup.find("div", class_="exam-content")

                if exam_div:
                    date_time = exam_div.find("div", class_="datetime").get_text(
                        strip=True
                    )

                    locations = []
                    loc_divs = exam_div.find_all("div", class_="location")

                    for loc in loc_divs:
                        split = loc.find("div", class_="split")
                        building = loc.find("div", class_="location-url")

                        split_text = split.get_text(strip=True) if split else "All"
                        building_text = (
                            building.get_text(strip=True) if building else "Unknown"
                        )
                        locations.append(f"{split_text}: {building_text}")

                    separator = ", "
                    locationString = separator.join(locations)

                    start_time = FinalExamFetcher._time_parse(date_time)

                    final = {
                        "course": course,
                        "event_type": "Final Exam",
                        "date": FinalExamFetcher._date_parse(date_time),
                        "begin_date_time": start_time,
                        "end_date_time": FinalExamFetcher._end_time(start_time),
                        "location": locationString,
                    }
                    return final

                # debugging/error handling
                else:
                    print("No exam found for this course.")
            else:
                print("Could not find HTML data in the AJAX response.")
        else:
            print(f"Request failed: {response.status_code}")

    def get_finals(courses):
        """
        Retrieves final exam information for a list of courses.

        Iterates through the provided list of course codes, fetching data for each
        individually. Invalid courses or failed requests are excluded from the result.

        Args:
            courses (list[str]): A list of course identifiers.
                Example: ["CPEN 221", "CPEN 211"]

        Returns:
            list[dict]: A list of dictionaries, where each dictionary contains the
                final exam information for a successfully fetched course.
        """
        finalsList = []
        for course in courses:
            if FinalExamFetcher.get_final(course) is not None:
                finalsList.append(FinalExamFetcher.get_final(course))
        return finalsList

    def _date_parse(date_time):
        """
        Extracts and formats the date from a raw datetime string.

        Args:
            date_time (str): The raw datetime string scraped from the HTML.
                Expected format: "%a %b %d %Y | %H:%M pm"

        Returns:
            str: The formatted date string in "%Y/%m/%d" format.
        """
        format_string = "%a %b %d %Y | %H:%M pm"
        format_out = "%Y/%m/%d"
        date_time_obj = datetime.strptime(date_time, format_string)
        return date_time_obj.strftime(format_out)

    def _time_parse(date_time):
        """
        Extracts and formats the start time from a raw datetime string.

        Args:
            date_time (str): The raw datetime string scraped from the HTML.
                Expected format: "%a %b %d %Y | %H:%M pm"

        Returns:
            str: The formatted time string in "%H:%M:00" format.
        """
        format_string = "%a %b %d %Y | %H:%M pm"
        format_out = "%H:%M:00"
        date_time_obj = datetime.strptime(date_time, format_string)
        return date_time_obj.strftime(format_out)

    def _end_time(start_time):
        """
        Calculates the exam end time assuming a standard 2.5-hour duration.
        
        Args:
            start_time (str): The exam start time.
                Expected format: "%H:%M:00"

        Returns:
            str: The calculated end time formatted as "%H:%M:00".
        """
        return datetime.strftime(
            datetime.strptime(start_time, "%H:%M:00") + timedelta(hours=2, minutes=30),
            "%H:%M:00",
        )


# debugging
if __name__ == '__main__':
    courses = ["CPEN_V 211", "CPEN_V 281"]
    finals = FinalExamFetcher.get_finals(courses)
    print(finals)
