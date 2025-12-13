# Known Bugs:

- ICal handler currently uses VTODO objects to handle assignments. Google Calendar and other calendar services ignore VTODO objects, meaning assignments do not get added to a Google Calendar.

- The main server controller does not have a functioning way to push class meeting information to the backend

- Currently the options to manually modify pre-existing events are limited, with only classes having an "Edit" or "Delete" option with no way to do the same for midterms, exams, or assignments. We are working on implementing this feature for all of them, not just classes.

- The final exam fetcher relies on an API call to the UBC final exam schedule. Although not necessarily a bug, if this API becomes depreciated that feature will no longer work.

- The ICal handler for some events are not able to be parsed into google calendar.

- For the demo, the fetcher retrieves announcements from the current date minus 80 days to ensure that some midterm data is available for display. In a production environment, this window would be reduced to 5 days to reflect real-world usage. The larger 80-day window occasionally causes the system to miss later midterm announcements (since it stops after the first detection), but this trade-off was made to better showcase the feature during the demo period when few midterms are occurring.

- Although not necessarily a bug, retrieval of information from the Canvas API is a complex procedure and takes up to a minute to process.

- If there is ever a class name which is not in the form *letters*_V *three digit number*..., the class will not be parsed and its assignments/final exam will not be added to the calendar.

### The midterm detection feature currently has two main limitations:

1. Missing Location Data - Midterm events do not include location information, as this detail is not reliably available in Canvas announcements.

2. Incomplete Midterm Updates - Midterm data may not update correctly depending on how frequently the user visits Canvas. The system fetches recent announcements from the Canvas API and uses an LLM to identify any midterm dates mentioned. Once a midterm is detected for a course, the parser ignores subsequent announcements from that same course within the same API call. This means that if multiple midterms are mentioned across different announcements, only the first one will be captured.



