"""
Lightweight embedder using HuggingFace Inference API.
Much lower memory footprint than loading models locally.
Uses the same all-MiniLM-L6-v2 model, just hosted remotely.
"""
import requests
from typing import List
from app.utils.logger import setup_logger
from app.utils.config import settings

logger = setup_logger("embedder_api")

# HuggingFace Inference API endpoint for the same model
HF_API_URL = "https://api-inference.huggingface.co/pipeline/feature-extraction/sentence-transformers/all-MiniLM-L6-v2"


class EmbedderAPI:
    def __init__(self):
        self.api_url = HF_API_URL
        self._token = None

    @property
    def token(self):
        """Lazy load the API token."""
        if self._token is None:
            self._token = getattr(settings, 'HF_API_TOKEN', None)
            if not self._token:
                logger.warning("HF_API_TOKEN not set - API calls may be rate limited")
        return self._token

    def embed(self, texts: List[str]) -> List[List[float]]:
        """
        Embeds a list of texts using HuggingFace Inference API.
        Returns a list of vectors (list of floats).
        """
        if not texts:
            return []

        try:
            headers = {}
            if self.token:
                headers["Authorization"] = f"Bearer {self.token}"

            # HF API accepts a list of texts and returns embeddings
            response = requests.post(
                self.api_url,
                headers=headers,
                json={"inputs": texts, "options": {"wait_for_model": True}},
                timeout=60
            )

            if response.status_code == 503:
                # Model is loading, retry with wait
                logger.info("Model loading on HuggingFace, waiting...")
                response = requests.post(
                    self.api_url,
                    headers=headers,
                    json={"inputs": texts, "options": {"wait_for_model": True}},
                    timeout=120
                )

            response.raise_for_status()
            embeddings = response.json()

            # Validate response format
            if isinstance(embeddings, list) and len(embeddings) > 0:
                # HF returns [[384 floats], [384 floats], ...]
                if isinstance(embeddings[0], list) and isinstance(embeddings[0][0], float):
                    logger.info(f"Generated {len(embeddings)} embeddings via HuggingFace API")
                    return embeddings

            logger.error(f"Unexpected response format: {type(embeddings)}")
            return []

        except requests.exceptions.Timeout:
            logger.error("HuggingFace API timeout")
            return []
        except requests.exceptions.RequestException as e:
            logger.error(f"HuggingFace API error: {e}")
            return []
        except Exception as e:
            logger.error(f"Error generating embeddings: {e}")
            return []


# Global instance
embedder = EmbedderAPI()
