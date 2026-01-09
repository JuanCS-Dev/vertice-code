# Backend Dockerfile - Node.js + Vertex AI (2026)
# Optimized for Google Cloud Run

FROM node:18-alpine

WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production

COPY . .
RUN npm run build

EXPOSE 8080
CMD ["npm", "start"]
