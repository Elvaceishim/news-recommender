"""
Production-grade ingestion scheduler using APScheduler with cron triggers.

Usage:
    python scripts/schedule_ingestion.py          # Run scheduler (continuous)
    python scripts/schedule_ingestion.py --once   # Run ingestion once and exit

Environment Variables:
    INGESTION_CRON_HOUR: Cron hour expression (default: "*/3" = every 3 hours)
    INGESTION_CRON_MINUTE: Cron minute expression (default: "0")
"""

import sys
import os
import signal
import argparse

# Ensure app is in path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
from app.ingestion.service import ingest_feeds
from app.utils.logger import setup_logger

logger = setup_logger("scheduler")

# RSS Feeds to ingest
FEEDS = [
    "http://feeds.bbci.co.uk/news/rss.xml",
    "https://rss.nytimes.com/services/xml/rss/nyt/HomePage.xml",
    "https://techcrunch.com/feed/",
    "https://www.theguardian.com/world/rss",
    "https://feeds.npr.org/1001/rss.xml",
]

# Cron schedule configuration (configurable via env vars)
CRON_HOUR = os.getenv("INGESTION_CRON_HOUR", "*/3")  # Every 3 hours
CRON_MINUTE = os.getenv("INGESTION_CRON_MINUTE", "0")


def run_ingestion():
    """Job function to run the ingestion pipeline."""
    logger.info("=== Starting scheduled ingestion ===")
    try:
        ingest_feeds(FEEDS)
        logger.info("=== Ingestion completed successfully ===")
    except Exception as e:
        logger.error(f"=== Ingestion failed: {e} ===")


def graceful_shutdown(signum, frame):
    """Handle shutdown signals gracefully."""
    logger.info("Received shutdown signal. Stopping scheduler...")
    sys.exit(0)


def main():
    parser = argparse.ArgumentParser(description="News Ingestion Scheduler")
    parser.add_argument(
        "--once",
        action="store_true",
        help="Run ingestion once and exit (no scheduling)"
    )
    args = parser.parse_args()

    if args.once:
        logger.info("Running one-time ingestion...")
        run_ingestion()
        return

    # Register signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, graceful_shutdown)
    signal.signal(signal.SIGTERM, graceful_shutdown)

    scheduler = BlockingScheduler()

    # Add the ingestion job with cron trigger
    trigger = CronTrigger(hour=CRON_HOUR, minute=CRON_MINUTE)
    scheduler.add_job(
        run_ingestion,
        trigger=trigger,
        id="news_ingestion",
        name="News RSS Ingestion",
        replace_existing=True,
        max_instances=1,  # Prevent overlapping runs
    )

    logger.info(f"Scheduler started. Ingestion will run at hour={CRON_HOUR}, minute={CRON_MINUTE}")
    logger.info("Press Ctrl+C to stop.")

    # Run initial ingestion on startup
    logger.info("Running initial ingestion on startup...")
    run_ingestion()

    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        logger.info("Scheduler stopped.")


if __name__ == "__main__":
    main()
