# News Recommender System

A production-grade personalized news recommender that fetches articles from RSS feeds, generates semantic embeddings via HuggingFace API, and serves ML-powered recommendations through a FastAPI backend.

**Live Demo**: [https://news-recommender-7ads.onrender.com](https://news-recommender-7ads.onrender.com)

## Features

- **Personalized Recommendations**: ML-based content matching using semantic embeddings
- **User Preference Learning**: Tracks clicks, likes, and dislikes to build user profiles
- **Diversity Algorithm (MMR)**: Prevents filter bubbles by ensuring topic variety
- **Trending Injection**: Ensures users see breaking news regardless of preferences
- **Real-time Updates**: Fresh articles ingested every 4 hours via scheduled cron
- **Modern UI**: Responsive web interface with authentication

## How It Works

```
┌─────────────┐     ┌──────────────┐     ┌─────────────────┐     ┌──────────────┐
│ RSS Feeds   │────▶│ Ingestion    │────▶│ HuggingFace API │────▶│ PostgreSQL   │
│ (BBC, NYT,  │     │ Service      │     │ (Embeddings)    │     │ + pgvector   │
│  NPR, etc.) │     └──────────────┘     └─────────────────┘     └──────────────┘
└─────────────┘                                                         │
                                                                        ▼
┌─────────────┐     ┌──────────────┐     ┌─────────────────┐     ┌──────────────┐
│ Frontend    │◀────│ FastAPI      │◀────│ Ranker (MMR +   │◀────│ User Profile │
│ (Web App)   │     │ /recommend   │     │ Similarity)     │     │ Embeddings   │
└─────────────┘     └──────────────┘     └─────────────────┘     └──────────────┘
```

### System Flow

1. **Ingestion (cron-job.org → `/ingest` endpoint)**
   - External cron triggers the `/ingest` API every 4 hours
   - Fetches articles from 5 RSS feeds (BBC, NYT, TechCrunch, Guardian, NPR)
   - Generates 384-dimension embeddings via HuggingFace Inference API
   - Stores articles with embeddings in PostgreSQL (Supabase + pgvector)

2. **User Interactions**
   - Users click, like, or dislike articles
   - Each interaction is logged to the `/interactions` endpoint
   - User profile embedding is recomputed in the background (weighted average)

3. **Recommendations (`/recommend` endpoint)**
   - Computes cosine similarity between user profile and article embeddings
   - Applies MMR (Maximal Marginal Relevance) for diversity
   - Injects trending articles and applies recency boost
   - Returns top-N personalized articles

## Tech Stack

| Component | Technology |
|-----------|------------|
| **Backend** | FastAPI + Gunicorn |
| **Database** | PostgreSQL + pgvector (Supabase) |
| **Embeddings** | HuggingFace Inference API (`all-MiniLM-L6-v2`) |
| **Scheduling** | External cron (cron-job.org) |
| **Hosting** | Render.com (Free Tier) |
| **Frontend** | Vanilla JS + CSS |

## Environment Variables

```bash
# Database (Supabase)
DATABASE_URL=postgresql://user:password@db.project.supabase.co:5432/postgres
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key

# HuggingFace (for embeddings)
HF_API_TOKEN=hf_your_token_here

# Security
JWT_SECRET=your-jwt-secret
CRON_SECRET=your-cron-secret  # Protects the /ingest endpoint
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| GET | `/recommend?user_id=X&limit=N` | Get personalized recommendations |
| POST | `/interactions` | Log user interaction (click/like/dislike) |
| POST | `/ingest` | Trigger article ingestion (protected by CRON_SECRET) |
| POST | `/auth/signup` | User registration |
| POST | `/auth/login` | User authentication |

## Local Development

### 1. Setup
```bash
git clone https://github.com/Elvaceishim/news-recommender.git
cd news-recommender
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure
```bash
cp .env.example .env
# Edit .env with your credentials
```

### 3. Initialize Database
```bash
python scripts/init_db.py
```

### 4. Run Locally
```bash
uvicorn app.api.main:app --reload
```

### 5. Trigger Ingestion
```bash
curl -X POST http://localhost:8000/ingest -H "X-Cron-Secret: YOUR_SECRET"
```

## Deployment (Render)

1. Push to GitHub
2. Create new Web Service on Render, connect repo
3. Add environment variables in Render dashboard
4. Set up external cron at [cron-job.org](https://cron-job.org):
   - URL: `https://your-app.onrender.com/ingest`
   - Method: POST
   - Header: `X-Cron-Secret: your-secret`
   - Schedule: Every 4 hours

## Project Structure

```
news-recommender/
├── app/
│   ├── api/           # FastAPI routes (recommend, auth, ingest)
│   ├── embeddings/    # HuggingFace API wrapper
│   ├── ingestion/     # RSS fetching & article processing
│   ├── recommender/   # Ranking algorithms (MMR, similarity)
│   ├── storage/       # SQLAlchemy models & database
│   └── utils/         # Config, logging
├── static/            # Frontend (HTML, CSS, JS)
├── scripts/           # CLI tools (init_db, etc.)
├── Dockerfile
├── Procfile
└── requirements.txt
```

## ML Approach

### Embedding Model
- **Model**: `sentence-transformers/all-MiniLM-L6-v2`
- **Dimensions**: 384
- **Hosted via**: HuggingFace Inference API (cloud-based, low memory footprint)

### User Profile Building
```python
# Weighted average of interacted article embeddings
weights = {'click': 1.0, 'like': 3.0, 'dislike': -2.0}
user_embedding = weighted_average(article_embeddings, weights)
```

### Ranking Algorithm
1. **Cosine Similarity**: Match user profile to article embeddings
2. **MMR Diversity**: Balance relevance with diversity (λ=0.7)
3. **Recency Boost**: Recent articles get score multiplier
4. **Trending Injection**: Top trending articles added regardless of profile

## License

MIT
