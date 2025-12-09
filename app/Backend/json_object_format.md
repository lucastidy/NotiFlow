## Formatting:
This is the format the follow for any json objects exported by a script/class.
The following is an example populated with an example event.
```
    event = {
        "course" : "CPEN 221",
        "event_type" = "final",
        "date" : "2025/12/10",
        "begin_date_time" : "12:00:00",
        "end_date_time" : "14:30:00",
        "location" : location // optional
    }
```
For class meeting times, one json object will represent all days of the week the class meeting occurs on.
eg. if a class meets tuesdays and thursdays, there will be one field in the json object (matching the format below)
MO, TU, WE, TH, FR, SA, SU

If there are biweekly meetings, the "interval" would be "2".

If a class meeting is cancelled or there is a break or smth and the user wants to add this, they can set an exception date.
Which is a specific date which a meeting will not occur on.

For any of these fields if there is no relevant information given by the user, leave them blank, the backend will parse them.
```
    class_meeting_time = {
        "course" : "CPEN 221",
        "event_type" = "class meeting",
        "date" : "2025/9/12",
        "begin_date_time" : "13:00:00",
        "end_date_time" : "14:00:00",
        "location" : "ESB 1319", // optional
        "frequency" : "WEEKLY",
        "interval" : "2"
        "by_day" : ["TU", "TH"],
        "exception_dates" : ["2025/10/30", "2025/11/1"]
    }
```
Example:
```
 BEGIN:VCALENDAR
 PRODID:-//xyz Corp//NONSGML PDA Calendar Version 1.0//EN
 VERSION:2.0
 BEGIN:VEVENT
 DTSTAMP:19960704T120000Z
 UID:uid1@example.com
 ORGANIZER:mailto:jsmith@example.com
 DTSTART:19960918T143000Z
 DTEND:19960920T220000Z
 STATUS:CONFIRMED
 CATEGORIES:CONFERENCE
 SUMMARY:Networld+Interop Conference
 DESCRIPTION:Networld+Interop Conference
   and Exhibit\nAtlanta World Congress Center\n
  Atlanta\, Georgia
 END:VEVENT
 END:VCALENDAR
```