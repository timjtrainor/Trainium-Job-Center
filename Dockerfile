# Dockerfile for the React frontend

# Use an official Node.js runtime as a parent image
FROM node:18-alpine

# Set the working directory in the container
WORKDIR /app

# Copy package.json and package-lock.json to the working directory
COPY package*.json ./
COPY package-lock.json ./

# Install the project dependencies
RUN npm install

# Copy the rest of the application's source code from the host to the container
COPY . .

# The create-react-app default port is 3000, but our API is using that.
# Vite/Next.js often use other ports, but we expose it here just in case.
# This port mapping is handled in the docker-compose.yml file.
EXPOSE 5173

# The command to start the development server
CMD ["npm", "run", "dev"]
