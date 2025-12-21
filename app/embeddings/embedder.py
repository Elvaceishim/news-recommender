from sentence_transformers import SentenceTransformer
from typing import List
from app.utils.logger import setup_logger

logger = setup_logger("embedder")

class Embedder:
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        logger.info(f"Loading embedding model: {model_name}")
        self.model = SentenceTransformer(model_name)

    def embed(self, texts: List[str]) -> List[List[float]]:
        """
        Embeds a list of texts. Returns a list of vectors (list of floats).
        """
        try:
            embeddings = self.model.encode(texts, convert_to_numpy=True)
            return embeddings.tolist()
        except Exception as e:
            logger.error(f"Error generating embeddings: {e}")
            return []

embedder = Embedder()
