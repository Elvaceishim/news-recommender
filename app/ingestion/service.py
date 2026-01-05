from sqlalchemy.orm import Session
from app.ingestion.fetch_feeds import fetch_all_feeds
from app.embeddings.embedder_api import embedder  # Use API-based embedder
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
        contents = [f"{a['title']} {a['content']}" for a in new_articles]
        embeddings = embedder.embed(contents)

        # Validate embeddings were generated
        if not embeddings or len(embeddings) != len(new_articles):
            logger.error(f"Embedding generation failed: got {len(embeddings) if embeddings else 0} embeddings for {len(new_articles)} articles")
            raise Exception("Failed to generate embeddings - check HF_API_TOKEN")

        # 4. Save to DB - insert one by one to handle duplicates gracefully
        saved_count = 0
        skipped_count = 0
        
        for i, article_data in enumerate(new_articles):
            try:
                article = Article(
                    title=article_data['title'],
                    content=article_data['content'],
                    link=article_data['link'],
                    source=article_data['source'],
                    published_date=article_data['published_date'],
                    embedding=embeddings[i]
                )
                db.add(article)
                db.commit()
                saved_count += 1
            except Exception as e:
                db.rollback()
                if "duplicate key" in str(e).lower() or "unique" in str(e).lower():
                    skipped_count += 1
                else:
                    logger.error(f"Error saving article: {e}")
        
        logger.info(f"Successfully saved {saved_count} articles with embeddings. Skipped {skipped_count} duplicates.")

    except Exception as e:
        logger.error(f"Ingestion failed: {e}")
        db.rollback()
    finally:
        db.close()
