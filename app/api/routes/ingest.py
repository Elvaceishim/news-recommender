"""
Ingestion trigger endpoint for external cron services.
Protected by a secret token to prevent unauthorized access.
"""
from fastapi import APIRouter, HTTPException, Header
from app.ingestion.service import ingest_feeds
from app.utils.config import settings
from app.utils.logger import setup_logger

logger = setup_logger("ingest_api")

router = APIRouter()

# RSS Feeds to ingest
FEEDS = [
    "http://feeds.bbci.co.uk/news/rss.xml",
    "https://rss.nytimes.com/services/xml/rss/nyt/HomePage.xml",
    "https://techcrunch.com/feed/",
    "https://www.theguardian.com/world/rss",
    "https://feeds.npr.org/1001/rss.xml",
]


@router.post("/ingest")
def trigger_ingestion(x_cron_secret: str = Header(None)):
    """
    Trigger RSS feed ingestion.
    Protected by X-Cron-Secret header matching CRON_SECRET env var.
    """
    expected_secret = getattr(settings, 'CRON_SECRET', None)
    
    if not expected_secret:
        raise HTTPException(status_code=500, detail="CRON_SECRET not configured")
    
    if x_cron_secret != expected_secret:
        logger.warning("Unauthorized ingestion attempt")
        raise HTTPException(status_code=401, detail="Invalid secret")
    
    logger.info("Ingestion triggered via API")
    try:
        ingest_feeds(FEEDS)
        return {"status": "success", "message": "Ingestion completed"}
    except Exception as e:
        logger.error(f"Ingestion failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
