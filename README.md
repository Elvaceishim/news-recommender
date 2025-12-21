# News Recommender System

A production-style news recommender that fetches articles from RSS feeds, generates embeddings using SentenceTransformers, and serves personalized recommendations via a FastAPI endpoint.

## Tech Stack

- **API**: FastAPI
- **Embeddings**: SentenceTransformers (MiniLM)
- **Database**: PostgreSQL + pgvector (Supabase)
- **Scheduler**: APScheduler

## Quick Start

### 1. Install Dependencies
```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure Environment
```bash
cp .env.example .env
```
Edit `.env` with your Supabase credentials:
```
DATABASE_URL=postgresql://user:password@db.project.supabase.co:5432/postgres
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key
```

### 3. Initialize Database
```bash
python scripts/init_db.py
```

### 4. Run Ingestion
```bash
# One-time ingestion
python scripts/schedule_ingestion.py --once

# Continuous scheduler (every 3 hours)
python scripts/schedule_ingestion.py
```

### 5. Start API
```bash
uvicorn app.api.main:app --reload
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Health check |
| GET | `/recommend?user_id=1` | Get recommendations |
| POST | `/interactions` | Log user interaction |

### Example: Log Interaction
```bash
curl -X POST "http://127.0.0.1:8000/interactions" \
  -H "Content-Type: application/json" \
  -d '{"user_id": 1, "article_id": 1, "interaction_type": "click"}'
```

## Project Structure
```
news-recommender/
├── app/
│   ├── api/           # FastAPI routes
│   ├── embeddings/    # SentenceTransformers wrapper
│   ├── ingestion/     # RSS fetching & preprocessing
│   ├── recommender/   # Ranking & user profiling
│   ├── storage/       # SQLAlchemy models & DB
│   └── utils/         # Config & logging
├── scripts/           # CLI tools
└── requirements.txt
```

## License

MIT
