FROM node:18-alpine

# Install basic shell utilities including coreutils (which provides cd)
RUN apk add --no-cache bash coreutils

# Set working directory
WORKDIR /app

# Copy package files
COPY package.json ./

# Install all dependencies (including dev dependencies for building)
RUN npm install

# Copy source code
COPY . .

# Build the React app
RUN npm run build

# Remove dev dependencies to reduce image size
RUN npm prune --production

# Expose port
EXPOSE 3000

# Start the server directly
CMD ["node", "server.js"] 