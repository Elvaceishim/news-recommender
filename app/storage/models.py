import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Float
from sqlalchemy.orm import relationship, mapped_column
from pgvector.sqlalchemy import Vector
from app.storage.db import Base

class Article(Base):
    __tablename__ = "articles"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    content = Column(Text, nullable=True)
    link = Column(String, unique=True, nullable=False)
    image_url = Column(String, nullable=True) # Added image_url just in case
    source = Column(String, nullable=True)
    published_date = Column(DateTime, default=datetime.datetime.utcnow)
    embedding = mapped_column(Vector(384)) # MiniLM uses 384 dimensions

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    full_name = Column(String, nullable=True)
    hashed_password = Column(String, nullable=False)
    user_embedding = mapped_column(Vector(384), nullable=True)

class Interaction(Base):
    __tablename__ = "interactions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    article_id = Column(Integer, ForeignKey("articles.id"))
    interaction_type = Column(String) # 'click', 'like'
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    
    user = relationship("User")
    article = relationship("Article")
