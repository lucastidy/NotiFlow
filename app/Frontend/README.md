# READ BEFORE EDITING

DO NOT PUSH CODE WITHOUT SUBMITTING A PULL REQUEST ON GITHUB PLEASE!!!!

This application uses npm to run it's frontend. This means that if you want to see the webpage in real time, change to notiflow directory and use:

```
npm run dev
```



If you want to see the chrome extension on your local machine, go to:
```
chrome://extensions/
```
in your webbrowser. Then in the top left click **Developer Mode**.

Then click **loadunpacked** and select Frontend/dist from folders. This should give you a chrome extension locally. To ship any changes you make the chrome you need:

```
npm run build
```

Testing backend using:
```
pip install flask
```
```
pip install flask-cors
```

## I configured Docker to work using these commands:

To build the image:
```
docker build -t react-app:dev .
```
### Options to run with Docker:
#### Using Docker compose (recommended)
To run the container:
```
docker-compose up --build 
```
To stop the container:
```
docker-compose down
```
#### Running manually
To run the container:
```
docker run -p 5173:5173 react-app:dev
```
To stop the container:
```
docker ps 
```
From the list of processes, find the `container_id` and run the following:
```
docker stop <container_id>
```
#### Optionally, to remove all dangling containers/images
```
docker system prune
```

