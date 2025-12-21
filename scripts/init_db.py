import sys
import os

# Ensure app is in path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sqlalchemy import text
from app.storage.db import engine, Base
from app.storage import models # Import models to register them
from app.utils.logger import setup_logger

logger = setup_logger("init_db")

def init_db():
    try:
        logger.info("Creating pgvector extension if not exists...")
        with engine.connect() as connection:
            connection.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
            connection.commit()
        
        logger.info("Creating tables...")
        Base.metadata.create_all(bind=engine)
        logger.info("Database initialized successfully.")
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        raise

if __name__ == "__main__":
    init_db()
