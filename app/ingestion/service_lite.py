"""
Lightweight ingestion service that does NOT use embeddings.
This is designed for memory-constrained environments like Render free tier.
Articles are stored without embeddings - recommendations fall back to recency-based ranking.
"""
from app.ingestion.fetch_feeds import fetch_all_feeds
from app.storage.models import Article
from app.utils.logger import setup_logger
from app.storage.db import SessionLocal

logger = setup_logger("ingestion_service_lite")

def ingest_feeds_lite(feed_urls: list[str]):
    """
    Ingest articles without generating embeddings.
    Much lighter on memory - suitable for free tier hosting.
    """
    db = SessionLocal()
    try:
        # 1. Fetch articles
        raw_articles = fetch_all_feeds(feed_urls)
        if not raw_articles:
            logger.info("No articles found.")
            return {"status": "ok", "new_articles": 0}

        # 2. Filter duplicates (check by link)
        new_articles = []
        existing_links = {
            link for (link,) in db.query(Article.link).filter(
                Article.link.in_([a['link'] for a in raw_articles])
            ).all()
        }

        for article in raw_articles:
            if article['link'] not in existing_links:
                new_articles.append(article)
        
        if not new_articles:
            logger.info("No new articles to ingest.")
            return {"status": "ok", "new_articles": 0}
        
        logger.info(f"Found {len(new_articles)} new articles. Saving without embeddings...")

        # 3. Save to DB WITHOUT embeddings
        db_articles = []
        for article_data in new_articles:
            db_articles.append(Article(
                title=article_data['title'],
                content=article_data['content'],
                link=article_data['link'],
                source=article_data['source'],
                published_date=article_data['published_date'],
                embedding=None  # No embedding - will use recency-based ranking
            ))
        
        db.add_all(db_articles)
        db.commit()
        logger.info(f"Successfully saved {len(db_articles)} articles (no embeddings).")
        return {"status": "ok", "new_articles": len(db_articles)}

    except Exception as e:
        logger.error(f"Ingestion failed: {e}")
        db.rollback()
        raise
    finally:
        db.close()
