# Deployment Guide

This project is configured for easy deployment on platforms like **Render**, **Railway**, or any **Docker-compatible** hosting.

## Prerequisites
- A **Supabase** project (PostgreSQL + pgvector).
- A **PaaS** account (Render/Railway/Heroku) OR a server with Docker.

## Configuration
Ensure your environment variables are set in your deployment platform:
```bash
DATABASE_URL=postgresql://user:pass@host:5432/db
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key
JWT_SECRET=your-secure-hex-key
LOG_LEVEL=INFO
```

## Option 1: Deploy with Docker (Recommended)
This method works on any VPS (AWS, DigitalOcean) or PaaS that supports Docker (Render, Railway, Fly.io).

1.  **Build the Image**:
    ```bash
    docker build -t news-recommender .
    ```

2.  **Run the API**:
    ```bash
    docker run -p 8000:8000 --env-file .env news-recommender
    ```

3.  **Run the Scheduler (Worker)**:
    *For production, run a separate container/process for the scheduler.*
    ```bash
    docker run --env-file .env news-recommender python scripts/schedule_ingestion.py
    ```

## Option 2: Render (PaaS)
1.  Connect your GitHub repository to Render.
2.  Select **Web Service**.
3.  Runtime: **Docker**.
4.  Add your Environment Variables.
5.  Deploy!

## Option 3: Railway (PaaS)
1.  Imports from GitHub.
2.  Railway automatically detects the `Dockerfile` or `Procfile`.
3.  Add Variables.
4.  Deploy.

## Post-Deployment
After deploying, if you are starting fresh:
1.  Run the initialization script (one-off):
    ```bash
    python scripts/init_db.py
    ```
    *Note: In Docker, you can run this via `docker run ... python scripts/init_db.py`*
