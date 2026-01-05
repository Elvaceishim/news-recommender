from sentence_transformers import SentenceTransformer
from typing import List
from app.utils.logger import setup_logger

logger = setup_logger("embedder")

class Embedder:
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model_name = model_name
        self._model = None  # Lazy load

    @property
    def model(self):
        """Lazy load the model on first use to speed up app startup."""
        if self._model is None:
            logger.info(f"Loading embedding model: {self.model_name}")
            self._model = SentenceTransformer(self.model_name)
        return self._model

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

