from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from app.api.routes import recommend
from app.utils.logger import setup_logger
import os

logger = setup_logger("api")

app = FastAPI(title="News Recommender API")

# Get the project root directory
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
STATIC_DIR = os.path.join(BASE_DIR, "static")

# Mount static files
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# Include API routes
app.include_router(recommend.router)

@app.get("/")
def serve_frontend():
    """Serve the frontend UI."""
    return FileResponse(os.path.join(STATIC_DIR, "index.html"))

@app.get("/health")
def health_check():
    """Health check endpoint for monitoring."""
    return {"status": "ok", "service": "news-recommender"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

