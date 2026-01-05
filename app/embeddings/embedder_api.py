"""
Lightweight embedder using HuggingFace Inference API via huggingface_hub library.
Much lower memory footprint than loading models locally.
Uses the same all-MiniLM-L6-v2 model, just hosted remotely.
"""
from huggingface_hub import InferenceClient
from typing import List
from app.utils.logger import setup_logger
from app.utils.config import settings

logger = setup_logger("embedder_api")

# Model ID on HuggingFace Hub
MODEL_ID = "sentence-transformers/all-MiniLM-L6-v2"


class EmbedderAPI:
    def __init__(self):
        self._client = None

    @property
    def client(self):
        """Lazy load the inference client."""
        if self._client is None:
            token = getattr(settings, 'HF_API_TOKEN', None)
            if not token:
                logger.warning("HF_API_TOKEN not set - API calls may fail")
            self._client = InferenceClient(token=token)
        return self._client

    def embed(self, texts: List[str]) -> List[List[float]]:
        """
        Embeds a list of texts using HuggingFace Inference API.
        Returns a list of vectors (list of floats).
        """
        if not texts:
            return []

        try:
            embeddings = []
            
            # Process in batches of 10 to avoid rate limits
            batch_size = 10
            for i in range(0, len(texts), batch_size):
                batch = texts[i:i + batch_size]
                
                # Use feature_extraction for embeddings
                batch_embeddings = self.client.feature_extraction(
                    batch,
                    model=MODEL_ID
                )
                
                # Convert to list format
                for emb in batch_embeddings:
                    if hasattr(emb, 'tolist'):
                        embeddings.append(emb.tolist())
                    else:
                        embeddings.append(list(emb))
            
            logger.info(f"Generated {len(embeddings)} embeddings via HuggingFace API")
            return embeddings

        except Exception as e:
            logger.error(f"HuggingFace API error: {e}")
            return []


# Global instance
embedder = EmbedderAPI()
