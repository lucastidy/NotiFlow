# NotiFlow
![Team Logo](img/notiflow.png)
### Our goal is to make student life at UBC a little less chaotic by automatically pulling all of your deadlines and classes into one dynamic, reliable schedule.

## Purpose
Students often struggle to keep track of assignments, exams, and class schedules across multiple Canvas courses. While Canvas offers an iCal export for assignment deadlines, it excludes critical information like exams and lecture times, forcing students to manually check each course and update their calendars.

The NotiFlow streamlines this process by automatically syncing course data, parsing announcements for exam information, and generating updated `.ics` calendar files every time the user accesses Canvas -- ensuring all important dates stay accurate and up to date without manual effort.

## Installation

#### Frontend
To set up and run the frontend, execute the following commands from the project root. You will need to have `Docker` installed for this step:
```
cd ./app/Frontend
docker-compose up --build
```
If you do not have `Docker`, you can run the app using `Node.js` which can be downloaded here [here](https://nodejs.org/en/download). Then use:
```
npm install
npm run build
```
This should accomplish the same thing of building the react app on your local machine. You can confirm this if you see a dist folder under Frontend. You need this for the next step.
If you want to see the Chrome extension on your local machine, go to:
```
chrome://extensions/
```
Then click **loadunpacked** and select app/Frontend/dist from folders. This should give you a Chrome extension locally. 

#### Backend 
To start the backend (required for the frontend to receive and render data), you need python for depenencies which you can download [here](https://www.python.org/downloads/) Then run the following command from the `~/app/backend` directory:
```
pip install uv
uv run python server.py
```
Make sure your `OPENAI_API_KEY` is set in a `.env` file or else the Midterm feature will not work.

Then follow the instructions on the browser extension to get access to canvas data.
