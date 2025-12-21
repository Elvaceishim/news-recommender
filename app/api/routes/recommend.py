from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from app.recommender.ranker import recommend_articles, build_user_embedding
from app.storage.db import get_db
from app.storage.models import Interaction, Article
import datetime

router = APIRouter()

class ArticleResponse(BaseModel):
    id: int
    title: str
    link: str
    source: Optional[str] = None
    published_date: datetime.datetime

    class Config:
        from_attributes = True

class InteractionRequest(BaseModel):
    user_id: int
    article_id: int
    interaction_type: str = "click"

@router.get("/recommend", response_model=List[ArticleResponse])
def get_recommendations(user_id: int, limit: int = 10, db: Session = Depends(get_db)):
    """
    Get personalized recommendations for a user.
    """
    try:
        articles = recommend_articles(user_id, limit)
        return articles
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/interactions")
def log_interaction(request: InteractionRequest, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """
    Log a user interaction (click/like) and update user profile in background.
    """
    try:
        interaction = Interaction(
            user_id=request.user_id,
            article_id=request.article_id,
            interaction_type=request.interaction_type
        )
        db.add(interaction)
        db.commit()
        
        # Trigger profile update in background
        background_tasks.add_task(build_user_embedding, request.user_id)
        
        return {"status": "success", "message": "Interaction logged"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
