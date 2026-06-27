import logging
import time

import httpx

from app.core.config import Settings
from app.services.exceptions import EmbeddingProviderError

logger = logging.getLogger(__name__)

GOOGLE_EMBED_BASE_URL = "https://generativelanguage.googleapis.com/v1beta"
GOOGLE_DEFAULT_MODEL = "gemini-embedding-001"
GOOGLE_LEGACY_MODELS = frozenset({"text-embedding-004", "embedding-001", "BAAI/bge-small-en-v1.5"})
GOOGLE_MAX_BATCH_SIZE = 100
GOOGLE_MAX_RETRIES = 3


class GoogleEmbeddingBackend:
    def __init__(self, settings: Settings) -> None:
        if not settings.google_api_key:
            raise EmbeddingProviderError("GOOGLE_API_KEY is not configured")
        self.settings = settings

    def _resolve_model_name(self) -> str:
        model_name = self.settings.embedding_model_name
        if model_name in GOOGLE_LEGACY_MODELS:
            return GOOGLE_DEFAULT_MODEL
        if model_name.startswith("models/"):
            return model_name.removeprefix("models/")
        return model_name

    def _model_resource(self) -> str:
        return f"models/{self._resolve_model_name()}"

    def embed_passages(self, texts: list[str]) -> list[list[float]]:
        return self._embed_texts(texts, task_type="RETRIEVAL_DOCUMENT")

    def embed_query(self, text: str) -> list[float]:
        return self._embed_texts([text], task_type="RETRIEVAL_QUERY")[0]

    def _embed_texts(self, texts: list[str], *, task_type: str) -> list[list[float]]:
        if not texts:
            return []

        batch_size = min(self.settings.effective_embedding_batch_size, GOOGLE_MAX_BATCH_SIZE)
        results: list[list[float]] = []

        for start in range(0, len(texts), batch_size):
            batch = texts[start : start + batch_size]
            results.extend(self._batch_embed(batch, task_type=task_type))

        return results

    def _batch_embed(self, texts: list[str], *, task_type: str) -> list[list[float]]:
        model = self._model_resource()
        model_id = model.removeprefix("models/")
        url = f"{GOOGLE_EMBED_BASE_URL}/models/{model_id}:batchEmbedContents"

        payload = {
            "requests": [
                {
                    "model": model,
                    "content": {"parts": [{"text": text}]},
                    "embedContentConfig": {
                        "taskType": task_type,
                        "outputDimensionality": self.settings.embedding_dimension,
                    },
                }
                for text in texts
            ]
        }

        response_data = self._post_with_retries(url, payload)
        embeddings = response_data.get("embeddings")
        if not embeddings or len(embeddings) != len(texts):
            raise EmbeddingProviderError(
                "Google embedding API returned an unexpected number of vectors"
            )

        vectors: list[list[float]] = []
        for item in embeddings:
            values = item.get("values")
            if not isinstance(values, list):
                raise EmbeddingProviderError("Google embedding API response missing values")
            vectors.append([float(value) for value in values])

        return vectors

    def _post_with_retries(self, url: str, payload: dict) -> dict:
        last_error: Exception | None = None

        for attempt in range(GOOGLE_MAX_RETRIES):
            try:
                with httpx.Client(timeout=60.0) as client:
                    response = client.post(
                        url,
                        headers={
                            "Content-Type": "application/json",
                            "x-goog-api-key": self.settings.google_api_key or "",
                        },
                        json=payload,
                    )
                if response.status_code == 429 and attempt < GOOGLE_MAX_RETRIES - 1:
                    delay = 2**attempt
                    logger.warning(
                        "Google embedding rate limit, retrying in %ss (attempt %d)",
                        delay,
                        attempt + 1,
                    )
                    time.sleep(delay)
                    continue
                response.raise_for_status()
                data = response.json()
                if not isinstance(data, dict):
                    raise EmbeddingProviderError("Google embedding API returned invalid JSON")
                return data
            except httpx.HTTPStatusError as exc:
                last_error = exc
                detail = exc.response.text
                raise EmbeddingProviderError(
                    f"Google embedding API failed ({exc.response.status_code}): {detail}"
                ) from exc
            except httpx.HTTPError as exc:
                last_error = exc
                if attempt < GOOGLE_MAX_RETRIES - 1:
                    time.sleep(2**attempt)
                    continue
                raise EmbeddingProviderError(f"Google embedding API request failed: {exc}") from exc

        raise EmbeddingProviderError(f"Google embedding API failed after retries: {last_error}")
