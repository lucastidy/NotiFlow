import json
from datetime import datetime, timezone, date
from pathlib import Path

import icalendar
import pytz

try:
    from .assignment_feature.AssignmentFetcher import mapCourses
except ImportError:
    from assignment_feature.AssignmentFetcher import mapCourses


# Mocking the fetcher return for demonstration purposes
# In our real project, you would import your actual modules here
# from final_exam_feature.FinalExam import FinalExamFetcher as ff


class ICalHandler:
    """
    Handles the creation, manipulation, and saving of iCalendar (.ics) files.

    This class provides methods to parse course schedules and assignments from
    JSON data, convert them into standard iCalendar events or tasks (VTODO),
    and manage recurrence rules and timezones.

    Attributes:
        term_end_date (str): The default end date for recurring events.
        tz (datetime.tzinfo): The timezone object (America/Vancouver).
        token (str): User authentication token.
        ics_path (Path): The file path where the calendar is stored.
        calendar (icalendar.Calendar): The internal calendar object.
        existing_uids (set): A tracking set of UIDs to prevent duplicate entries.
    """
    term_end_date = "2025/12/7"

    def __init__(self, token: str, filename='calendar.ics'):
        """
        Initializes the ICalHandler.

        Attempts to load an existing calendar file from the disk. If the file
        does not exist or is corrupted, a new calendar object is created.

        Args:
            token (str): The user's authentication token.
            filename (str, optional): The name of the .ics file. Defaults to 'calendar.ics'.
        """
        self.tz = pytz.timezone("America/Vancouver")
        self.token = token

        self.curr_path = Path(__file__).resolve()
        self.notiflow_path = self.curr_path.parent
        self.ics_path = self.notiflow_path / filename

        self.calendar = None
        self.existing_uids = set()

        if self.ics_path.is_file():
            print(f"Loading existing calendar from {self.ics_path}")
            try:
                with open(self.ics_path, "rb") as f:
                    self.calendar = icalendar.Calendar.from_ical(f.read())
                    for component in self.calendar.walk():
                        if component.name == "VEVENT":
                            self.existing_uids.add(component.get("uid"))
            except Exception as e:
                print(f"Error reading file, creating new: {e}")
                self._create_new_calendar()
        else:
            print("Creating new calendar file.")
            self._create_new_calendar()

    def _create_new_calendar(self):
        """
        Initializes a fresh icalendar.Calendar object with default metadata.
        """
        self.calendar = icalendar.Calendar()
        self.calendar.add("prodid", "-//NotiFlow//Finals Scheduler//EN")
        self.calendar.add("version", "2.0")
        self.calendar.add("x-wr-calname", "NotiFlow Winter Term 1")

    def _generate_uid(self, course, event_type, date_str, start_str):
        """
        Generates a deterministic Unique Identifier (UID) for an event.

        Args:
            course (str): The course identifier.
            event_type (str): The type of event (e.g., "Lecture").
            date_str (str): The date string.
            start_str (str): The start time string.

        Returns:
            str: A unique, sanitized string ID for the event.
        """
        raw_uid = f"{course}-{event_type}-{date_str}-{start_str}@notiflow.local"
        return raw_uid.replace(" ", "_").replace("/", "")

    def create_event_object(self, event_json):
        """
        Converts a JSON dictionary into an icalendar.Event object.

        Handles standard event fields as well as complex recurrence rules (RRULE)
        and exception dates (EXDATE).

        Args:
            event_json (dict): A dictionary containing event details. Expected keys include:
                - course, event_type, date, begin_date_time, end_date_time
                - Optional recurrence keys: frequency, interval, by_day, exception_dates, until

        Returns:
            icalendar.Event: The constructed event object.
            None: If the input data is incomplete or the event is a duplicate.
        """
        course = event_json.get("course")
        event_type = event_json.get("event_type")
        date_str = event_json.get("date")
        start_str = event_json.get("begin_date_time")
        end_str = event_json.get("end_date_time")
        location_str = event_json.get("location", "") 
        
        frequency = event_json.get("frequency")
        interval = event_json.get("interval")
        by_day = event_json.get("by_day")
        exception_dates = event_json.get("exception_dates")
        until = event_json.get("until", "")

        if not all([course, date_str, start_str, end_str]):
            print(f"Skipping incomplete event data: {event_json}")
            return None

        dt_start = self.dateTimeParse(date_str, start_str)
        dt_end = self.dateTimeParse(date_str, end_str)

        uid = self._generate_uid(course, event_type, date_str, start_str)

        if uid in self.existing_uids:
            print(f"Event already exists: {uid}")
            return None

        event = icalendar.Event()

        summary_text = f"{course} - {event_type}"
        if location_str:
            summary_text += f" - {location_str}"
            event.add('location', location_str)
            
        event.add('summary', summary_text)
        event.add('dtstart', dt_start)
        event.add('dtend', dt_end)
        event.add('dtstamp', datetime.now(pytz.utc))
        event.add('uid', uid)
        event.add('description', f"Entry for {course} {event_type}")

        if frequency:
            dt_until = self.dateTimeParse(until)
            rrule = {'FREQ': frequency}
            rrule['UNTIL'] = dt_until
            
            if interval:
                try:
                    rrule['INTERVAL'] = int(interval)
                except ValueError:
                    pass

            if by_day:
                rrule['BYDAY'] = by_day
                
            event.add('rrule', rrule)

        if exception_dates:
            for ex_date_str in exception_dates:
                ex_dt = self.dateTimeParse(ex_date_str, start_str)
                
                # if ex_dt:
                event.add('exdate', ex_dt)

        self.existing_uids.add(uid)

        return event

    def process_json(self, data):
        """
        Processes a list of event data, creating and adding events to the calendar.

        Args:
            data (list[dict]): A list of dictionaries representing events.
        """
        count = 0
        for item in data:
            event = self.create_event_object(item)
            # if event
            self.calendar.add_component(event)
            count += 1
        # DEBUG
        print(f"Processed {count} new events.")

    def save_calendar(self):
        """
        Serializes and writes the current calendar object to the .ics file.
        """
        with open(self.ics_path, "wb") as f:
            f.write(self.calendar.to_ical())
            print(f"Calendar saved successfully to {self.ics_path}")

    def dateTimeParse(self, date_str, time_str="12:00:00"):
        """
        Parses date and time strings into a timezone-aware datetime object.

        Args:
            date_str (str): Date in "YYYY/MM/DD" format.
            time_str (str, optional): Time in "HH:MM:SS" or "HH:MM" format. Defaults to "12:00:00".

        Returns:
            datetime: A timezone-aware datetime object (America/Vancouver).
            None: If parsing fails.
        """
        format_date = "%Y/%m/%d"
        format_time_full = "%H:%M:%S"
        format_time_short = "%H:%M"

        try:
            date_object = datetime.strptime(date_str, format_date).date()

            try:
                time_object = datetime.strptime(time_str, format_time_full).time()
            except ValueError:
                time_object = datetime.strptime(time_str, format_time_short).time()

            dt_naive = datetime.combine(date_object, time_object)
            dt_aware = dt_naive.replace(tzinfo=self.tz)
            return dt_aware

        except ValueError as e:
            print(f"Error parsing date/time ({date_str} {time_str}): {e}")
            return None

    def _parse_canvas_iso(self, iso_str: str):
        """
        Parses an ISO 8601 string into a local timezone-aware datetime.

        Args:
            iso_str (str): The ISO date string (e.g., '2025-12-10T22:30:00Z').

        Returns:
            datetime: The converted datetime object in the local timezone.
            None: If the string is empty.
        """
        if not iso_str:
            return None
        dt_utc = datetime.fromisoformat(iso_str.replace("Z", "+00:00"))

        # if dt_utc.tzinfo is None:
        #     dt_utc = dt_utc.replace(tzinfo=timezone.utc)
        dt_local = dt_utc.astimezone(self.tz)
        return dt_local

    def _generate_task_uid(
        self, course: str, assignment_name: str, iso_start: str
    ) -> str:
        """
        Generates a deterministic UID for an assignment task.

        Args:
            course (str): The course name.
            assignment_name (str): The name of the assignment.
            iso_start (str): The ISO start string.

        Returns:
            str: A unique identifier string.
        """
        raw_uid = f"{course}-ASSIGNMENT-{assignment_name}-{iso_start}@notiflow.local"
        return raw_uid.replace(" ", "_").replace("/", "")

    def create_task_object(self, course: str, assignment_name: str, iso_start: str):
        """
        Creates an iCalendar VTODO (Task) for a specific assignment.

        Args:
            course (str): The course identifier.
            assignment_name (str): The assignment title.
            iso_start (str): The due date/start date in ISO format.

        Returns:
            icalendar.Todo: The constructed task object.
            None: If data is incomplete or parsing fails.
        """
        if not all([course, assignment_name, iso_start]):
            print(
                f"Skipping incomplete assignment task: {course}, {assignment_name}, {iso_start}"
            )
            return None

        dt_start = self._parse_canvas_iso(iso_start)
        # if not dt_start:
        #     print(f"Could not parse start time for assignment: {assignment_name}")
        #     return None

        uid = self._generate_task_uid(course, assignment_name, iso_start)
        if uid in self.existing_uids:
            print(f"Task already exists: {uid}")
            return None

        todo = icalendar.Todo()
        summary_text = f"{course} - {assignment_name}"
        todo.add("summary", summary_text)
        todo.add("dtstart", dt_start)
        todo.add("dtstamp", datetime.now(pytz.utc))
        todo.add("uid", uid)
        todo.add("description", f"Assignment task for {course}: {assignment_name}")

        self.existing_uids.add(uid)
        return todo

    def process_assignments(self, assignments_data):
        """
        Parses Canvas assignment JSON data and adds them as tasks to the calendar.

        Args:
            assignments_data (str): A JSON string containing assignment data grouped by course.
        """
        data = json.loads(assignments_data)
        count = 0

        for course, course_data in data.items():
            for assignment_group in course_data.get("assignments", []):
                for assignment in assignment_group:
                    name = assignment[0]
                    iso_start = assignment[3]

                    todo = self.create_task_object(course, name, iso_start)
                    # if todo:
                    self.calendar.add_component(todo)
                    count += 1

        print(f"Processed {count} assignment tasks.")

    def _parse_course_meetings(self, course_meetings_json):
        """
        Maps frontend course meeting JSON to the internal event format.

        Args:
            course_meetings_json (dict): Dictionary with keys 'className',
                'startTime', 'endTime', and 'days'.

        Returns:
            dict: A normalized event dictionary compatible with create_event_object.
            None: If time parsing fails.
        """
        parsed_event = {}
        
        parsed_event["course"] = course_meetings_json.get("className", "Unknown Course")
        parsed_event["event_type"] = "Class Meeting"
        
        current_date = date.today()
        parsed_event["date"] = current_date.strftime("%Y/%m/%d") 

        try:
            start_dt = datetime.strptime(course_meetings_json["startTime"], "%I:%M %p")
            end_dt = datetime.strptime(course_meetings_json["endTime"], "%I:%M %p")
            
            parsed_event["begin_date_time"] = start_dt.strftime("%H:%M:%S")
            parsed_event["end_date_time"] = end_dt.strftime("%H:%M:%S")
        except ValueError as e:
            print(f"Time parsing error: {e}")
            return None

        parsed_event["frequency"] = "WEEKLY"
        
        day_map = {
            "M": "MO", 
            "Tu": "TU", 
            "W": "WE", 
            "Th": "TH", 
            "F": "FR", 
            "Sa": "SA", 
            "Su": "SU"
        }
        
        raw_days = course_meetings_json.get("days", {})
        selected_days = []

        for day_key, is_selected in raw_days.items():
            if is_selected and day_key in day_map:
                selected_days.append(day_map[day_key])

        parsed_event["by_day"] = selected_days
        
        parsed_event["until"] = self.term_end_date

        return parsed_event

    def process_course_meetings(self, course_meetings_json):
        """
        Processes course meeting data, handles JSON parsing, and triggers event creation.

        Args:
            course_meetings_json (str | dict): The course meeting data as a JSON string
                or dictionary.
        """
        if isinstance(course_meetings_json, str):
            try:
                data_dict = json.loads(course_meetings_json)
            except json.JSONDecodeError as e:
                print(f"Invalid JSON provided: {e}")
                return
        else:
            data_dict = course_meetings_json

        parsed_event = self._parse_course_meetings(data_dict)
        
        # if parsed_event:
        self.process_json([parsed_event])

# DEBUGGING
# if __name__ == '__main__' :
#     class_meeting_time = """ {
#     "className":"sdafasdf",
#     "days":{"F":false,"M":false,"Th":false,"Tu":false,"W":true},
#     "endTime":"2:30 PM",
#     "startTime":"10:00 AM"
#     } """

#     token = "4"
#     handler = ICalHandler(token)

#     handler.process_course_meetings(class_meeting_time)