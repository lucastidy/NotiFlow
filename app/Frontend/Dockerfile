FROM node:22

WORKDIR /app

# Copy package json and lock.json
COPY package*.json ./

# install dependencies
RUN npm install

COPY . .

EXPOSE 5173

CMD [ "npm", "run", "build"]