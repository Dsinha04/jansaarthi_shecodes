"""Embedding wrapper. E5 models need 'query: ' / 'passage: ' prefixes; other models do not."""
import config


class E5Embedder:
    def __init__(self, name=None):
        from sentence_transformers import SentenceTransformer
        self.name = name or config.EMBED_MODEL
        self.model = SentenceTransformer(self.name)
        self.use_prefix = "e5" in self.name.lower()

    def _enc(self, texts, show_progress=False):
        return self.model.encode(texts, normalize_embeddings=True,
                                 show_progress_bar=show_progress).astype("float32")

    def encode_passages(self, texts, show_progress=False):
        return self._enc([("passage: " + t) if self.use_prefix else t for t in texts], show_progress)

    def encode_query(self, text):
        return self._enc([("query: " + text) if self.use_prefix else text])
