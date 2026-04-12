FROM node:22-alpine AS frontend-builder

WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
COPY index.html ./
COPY src ./src
COPY tsconfig.json tsconfig.node.json vite.config.ts ./
RUN npm run build

FROM python:3.12-slim AS runtime

WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV TREND_DB_PATH=/app/data/trends.db

COPY requirements-data.txt ./
RUN pip install --no-cache-dir -r requirements-data.txt

COPY backend ./backend
COPY scripts ./scripts
COPY --from=frontend-builder /app/dist ./dist

RUN mkdir -p /app/data

EXPOSE 8000
CMD ["python3", "-m", "backend.app"]
