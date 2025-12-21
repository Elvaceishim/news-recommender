import feedparser
import datetime
from typing import List, Dict
from app.utils.logger import setup_logger
from app.ingestion.preprocess import clean_text

logger = setup_logger("ingestion")

def parse_feed(url: str) -> List[Dict]:
    """
    Fetches and parses a single RSS feed.
    Returns a list of dictionaries with article data.
    """
    try:
        logger.info(f"Fetching feed: {url}")
        feed = feedparser.parse(url)
        articles = []
        
        for entry in feed.entries:
            # Extract basic info
            title = clean_text(entry.get('title', ''))
            summary = clean_text(entry.get('summary', ''))
            link = entry.get('link', '')
            
            # published_parsed is a struct_time, convert to datetime
            published_parsed = entry.get('published_parsed')
            if published_parsed:
                published_date = datetime.datetime(*published_parsed[:6])
            else:
                published_date = datetime.datetime.utcnow()
                
            # Prefer content if available, else summary
            content = summary
            if 'content' in entry:
                content = clean_text(entry.content[0].value)
            
            if title and link:
                articles.append({
                    "title": title,
                    "content": content,
                    "link": link,
                    "published_date": published_date,
                    "source": feed.feed.get('title', url)
                })
        
        logger.info(f"Fetched {len(articles)} articles from {url}")
        return articles
        
    except Exception as e:
        logger.error(f"Error fetching feed {url}: {e}")
        return []

def fetch_all_feeds(feed_urls: List[str]) -> List[Dict]:
    """
    Fetches multiple feeds and aggregates articles.
    """
    all_articles = []
    for url in feed_urls:
        articles = parse_feed(url)
        all_articles.extend(articles)
    return all_articles
