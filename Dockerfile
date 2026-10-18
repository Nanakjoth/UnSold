# ---- Stage 1: build the frontend SPA -----------------------------------------
FROM node:22-slim AS webbuild
WORKDIR /web
COPY web/package.json web/package-lock.json ./
RUN npm ci --no-audit --no-fund
COPY web/ ./
RUN npm run build

# ---- Stage 2: API + static frontend ------------------------------------------
FROM python:3.12-slim
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1
WORKDIR /app

COPY server/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY server/app ./app
# Built SPA from stage 1; WEB_DIST points the API at it.
COPY --from=webbuild /web/dist ./static/web
ENV WEB_DIST=/app/static/web

# Cloud Run provides $PORT; default to 8080 for local image runs.
EXPOSE 8080
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8080}"]
