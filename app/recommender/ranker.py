from sqlalchemy.orm import Session
from sqlalchemy import func
from app.storage.models import User, Article, Interaction
from app.storage.db import SessionLocal
import numpy as np
import datetime
from app.utils.logger import setup_logger

logger = setup_logger("ranker")

# Weights for interaction types
INTERACTION_WEIGHTS = {
    "click": 1.0,
    "like": 2.0,
    "dislike": -1.0,  # Negative weight pushes user profile away from this content
}

# Time decay factor (half-life approx 14 days)
DECAY_RATE = 0.05 

def build_user_embedding(user_id: int):
    """
    Recalculates and updates the user embedding based on weighted interactions.
    Weights are determined by interaction type and time decay.
    """
    db = SessionLocal()
    try:
        # Fetch user's interactions with articles
        interactions = db.query(Interaction).filter(Interaction.user_id == user_id).all()
        
        if not interactions:
            logger.info(f"No interactions found for user {user_id}. Cannot build profile.")
            return
        
        # Get embeddings of these articles
        article_ids = [i.article_id for i in interactions]
        articles = db.query(Article).filter(Article.id.in_(article_ids)).all()
        article_map = {a.id: a for a in articles}
        
        weighted_vectors = []
        total_weight = 0.0
        
        now = datetime.datetime.utcnow()
        
        for interaction in interactions:
            article = article_map.get(interaction.article_id)
            if not article or article.embedding is None:
                continue
                
            # Base weight from interaction type
            base_weight = INTERACTION_WEIGHTS.get(interaction.interaction_type, 1.0)
            
            # Time decay
            days_diff = (now - interaction.timestamp).days
            time_decay = np.exp(-DECAY_RATE * max(0, days_diff))
            
            final_weight = base_weight * time_decay
            
            weighted_vectors.append(np.array(article.embedding) * final_weight)
            total_weight += final_weight
            
        if not weighted_vectors:
            return

        # Calculate weighted mean embedding
        mean_embedding = np.sum(weighted_vectors, axis=0) / total_weight
        
        # Update user
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            user = User(id=user_id)
            db.add(user)
        
        user.user_embedding = mean_embedding.tolist()
        db.commit()
        logger.info(f"Updated profile for user {user_id} with total weight {total_weight:.2f}")
        
    except Exception as e:
        logger.error(f"Error building user profile: {e}")
        db.rollback()
    finally:
        db.close()

def recommend_articles(user_id: int, limit: int = 10, candidates: int = 50):
    """
    Returns top-k recommended articles using semantic search + recency re-ranking.
    Filters out articles the user has already interacted with (deduplication).
    Applies MMR-style diversity to avoid filter bubbles.
    Applies source variety penalty to avoid publisher dominance.
    Injects trending/breaking news regardless of user profile.
    """
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == user_id).first()
        now = datetime.datetime.utcnow()
        
        # Get article IDs the user has already interacted with (for deduplication)
        interacted_ids = set(
            i.article_id for i in 
            db.query(Interaction.article_id).filter(Interaction.user_id == user_id).all()
        )
        
        # === TRENDING OVERRIDE ===
        # Reserve slots for breaking news (< 6 hours old) regardless of similarity
        TRENDING_SLOTS = 2  # Number of slots reserved for breaking news
        TRENDING_HOURS = 6  # Articles less than this many hours old qualify
        
        trending_cutoff = now - datetime.timedelta(hours=TRENDING_HOURS)
        trending_query = db.query(Article).filter(
            Article.published_date >= trending_cutoff
        ).order_by(Article.published_date.desc())
        
        if interacted_ids:
            trending_query = trending_query.filter(~Article.id.in_(interacted_ids))
        
        trending_articles = trending_query.limit(TRENDING_SLOTS).all()
        trending_ids = {a.id for a in trending_articles}
        
        if trending_articles:
            logger.info(f"Injecting {len(trending_articles)} trending articles for user {user_id}")
        
        if not user or user.user_embedding is None:
            # Cold start: return latest articles (excluding already seen)
            logger.info(f"Cold start for user {user_id}")
            query = db.query(Article).order_by(Article.published_date.desc())
            if interacted_ids:
                query = query.filter(~Article.id.in_(interacted_ids))
            return query.limit(limit).all()
        
        # 1. Candidate Generation: Get top N articles by semantic similarity
        # pgvector uses <=> for cosine distance (lower is better)
        # Exclude already interacted articles AND trending (we'll add those separately)
        query = db.query(Article)
        if interacted_ids:
            query = query.filter(~Article.id.in_(interacted_ids))
        if trending_ids:
            query = query.filter(~Article.id.in_(trending_ids))
        similar_articles = query.order_by(
            Article.embedding.cosine_distance(user.user_embedding)
        ).limit(candidates).all()
        
        # 2. Score each article (relevance + recency)
        user_vec = np.array(user.user_embedding)
        
        scored_candidates = []
        for article in similar_articles:
            art_vec = np.array(article.embedding)
            
            # Cosine similarity
            similarity = np.dot(user_vec, art_vec) / (np.linalg.norm(user_vec) * np.linalg.norm(art_vec) + 1e-9)
            
            # Recency boost
            age_hours = (now - article.published_date).total_seconds() / 3600
            recency_decay = 1.0 / (1.0 + (age_hours / 24.0))
            
            base_score = similarity * (1 + (recency_decay * 0.5))
            
            scored_candidates.append({
                'article': article,
                'embedding': art_vec,
                'score': base_score,
                'source': (article.source or '').lower()
            })
        
        # 3. MMR-style Diversity Selection
        # Balance relevance with novelty (distance from already-selected items)
        LAMBDA_DIVERSITY = 0.3  # 0 = pure relevance, 1 = pure diversity
        SOURCE_PENALTY = 0.15  # Penalty for consecutive same-source articles
        
        # Start with trending articles (they get priority slots)
        selected = list(trending_articles)
        selected_embeddings = [np.array(a.embedding) for a in trending_articles if a.embedding is not None]
        source_counts = {}
        for a in trending_articles:
            src = (a.source or '').lower()
            source_counts[src] = source_counts.get(src, 0) + 1
        
        # Fill remaining slots with personalized + diverse articles
        remaining_slots = limit - len(selected)
        
        while len(selected) < limit and scored_candidates:
            best_idx = -1
            best_mmr_score = float('-inf')
            
            for i, candidate in enumerate(scored_candidates):
                relevance = candidate['score']
                
                # Diversity: max similarity to any already-selected article
                if selected_embeddings:
                    max_sim_to_selected = max(
                        np.dot(candidate['embedding'], sel_emb) / 
                        (np.linalg.norm(candidate['embedding']) * np.linalg.norm(sel_emb) + 1e-9)
                        for sel_emb in selected_embeddings
                    )
                else:
                    max_sim_to_selected = 0
                
                # MMR score: balance relevance and diversity
                mmr_score = (1 - LAMBDA_DIVERSITY) * relevance - LAMBDA_DIVERSITY * max_sim_to_selected
                
                # Source variety penalty
                source = candidate['source']
                if source in source_counts and source_counts[source] > 0:
                    mmr_score -= SOURCE_PENALTY * source_counts[source]
                
                if mmr_score > best_mmr_score:
                    best_mmr_score = mmr_score
                    best_idx = i
            
            if best_idx == -1:
                break
                
            # Add best candidate to selected
            best = scored_candidates.pop(best_idx)
            selected.append(best['article'])
            selected_embeddings.append(best['embedding'])
            
            # Update source count
            source = best['source']
            source_counts[source] = source_counts.get(source, 0) + 1
        
        logger.info(f"Recommended {len(selected)} articles for user {user_id} ({len(trending_articles)} trending)")
        return selected
        
    except Exception as e:
        logger.error(f"Error getting recommendations: {e}")
        return []
    finally:
        db.close()
