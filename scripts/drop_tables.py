import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sqlalchemy import text
from app.storage.db import engine

def drop_tables():
    with engine.connect() as conn:
        print("Dropping interactions table...")
        conn.execute(text('DROP TABLE IF EXISTS interactions'))
        print("Dropping users table...")
        conn.execute(text('DROP TABLE IF EXISTS users'))
        conn.commit()
    print("Tables dropped successfully.")

if __name__ == "__main__":
    drop_tables()
