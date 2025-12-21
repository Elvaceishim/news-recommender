from sqlalchemy.orm import Session
from app.ingestion.fetch_feeds import fetch_all_feeds
from app.embeddings.embedder import embedder
from app.storage.models import Article
from app.utils.logger import setup_logger
from app.storage.db import SessionLocal

logger = setup_logger("ingestion_service")

def ingest_feeds(feed_urls: list[str]):
    db = SessionLocal()
    try:
        # 1. Fetch articles
        raw_articles = fetch_all_feeds(feed_urls)
        if not raw_articles:
            logger.info("No articles found.")
            return

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
            return
        
        logger.info(f"Found {len(new_articles)} new articles. Generating embeddings...")

        # 3. Generate embeddings
        # Batch processing might be better for large N, but for now direct is fine
        contents = [f"{a['title']} {a['content']}" for a in new_articles]
        embeddings = embedder.embed(contents)

        # 4. Save to DB
        db_articles = []
        for i, article_data in enumerate(new_articles):
            db_articles.append(Article(
                title=article_data['title'],
                content=article_data['content'],
                link=article_data['link'],
                source=article_data['source'],
                published_date=article_data['published_date'],
                embedding=embeddings[i]
            ))
        
        db.add_all(db_articles)
        db.commit()
        logger.info(f"Successfully saved {len(db_articles)} articles.")

    except Exception as e:
        logger.error(f"Ingestion failed: {e}")
        db.rollback()
    finally:
        db.close()
