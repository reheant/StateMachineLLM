FROM node:20-alpine

WORKDIR /app

# Install dependencies first (better layer caching)
COPY StateMachineLLM/frontend/package*.json ./
RUN npm ci

# Copy source and build
COPY StateMachineLLM/frontend/ .
RUN npm run build

EXPOSE 3000

ENV NODE_ENV=production

CMD ["npm", "run", "start"]
