# Multi-stage build for production-ready Vite dashboard

FROM node:18-slim AS deps

# Install dependencies only when needed
WORKDIR /app

# Copy package files
COPY package.json package-lock.json* ./

# Install dependencies
RUN npm install

# Rebuild the source code only when needed
FROM node:18-slim AS builder
WORKDIR /app

# Copy dependencies from deps stage
COPY --from=deps /app/node_modules ./node_modules

# Copy all application files (respects .dockerignore)
COPY . .

# Accept build arguments for Vite environment variables
ARG VITE_API_URL=http://localhost:55000/api/v1
ARG VITE_WS_URL=ws://localhost:55000/ws
ARG VITE_APP_NAME=CyberSentinel DLP
ARG VITE_APP_VERSION=2.0.0

# Set environment variables for build
ENV NODE_ENV=production
ENV VITE_API_URL=${VITE_API_URL}
ENV VITE_WS_URL=${VITE_WS_URL}
ENV VITE_APP_NAME=${VITE_APP_NAME}
ENV VITE_APP_VERSION=${VITE_APP_VERSION}

# Build application
RUN npm run build

# Production image
FROM node:18-slim AS runner
WORKDIR /app

ENV NODE_ENV production

# Create non-root user
RUN groupadd --system --gid 1001 nodejs && \
    useradd --system --uid 1001 --gid nodejs nodejs

# Copy built files and node_modules
COPY --from=builder /app/dist ./dist
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/package.json ./package.json

# Set proper permissions
RUN chown -R nodejs:nodejs /app

# Switch to non-root user
USER nodejs

# Expose port
EXPOSE 3000

ENV PORT 3000
ENV HOSTNAME "0.0.0.0"

# Run vite preview server
CMD ["npx", "vite", "preview", "--host", "0.0.0.0", "--port", "3000"]
