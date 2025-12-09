### Frontend installation
To set up and run the frontend, execute the following commands from the project root. You will need to have Docker installed for this step:
```
cd ./app/Frontend
docker-compose up --build
```
If you don't want to install Docker for whatever reason, you need to install node [here](https://nodejs.org/en/download). Then use:
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

### Backend installation
To start the backend (required for the frontend to receive and render data), you need python for depenencies which you can download [here](https://www.python.org/downloads/) Then run the following command from the `~/app/backend` directory:
```
pip install uv
uv run python server.py
```
Make sure your `OPENAI_API_KEY` is set in a `.env` file or else the Midterm feature will not work.

Then follow instructions on the browser extension to get access to canvas data.



