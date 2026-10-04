"""Tiny deterministic embedder for tests (hashed bag of words). NOT for production: real score tuning needs the real model."""
import re
import zlib
import numpy as np

STOP = {"the", "and", "for", "that", "with", "this", "from", "are", "was", "what", "which", "how", "who",
        "can", "may", "any", "not", "you", "your", "does", "did", "has", "have", "will", "shall", "must", "does"}


class HashEmbedder:
    dim = 512

    def _vec(self, text):
        v = np.zeros(self.dim, dtype="float32")
        for t in re.findall(r"[a-z]+", text.lower()):
            if t in STOP or len(t) < 3:
                continue
            v[zlib.crc32(t.encode()) % self.dim] += 1
        n = np.linalg.norm(v)
        return v / n if n else v

    def encode_passages(self, texts, show_progress=False):
        return np.stack([self._vec(t) for t in texts])

    def encode_query(self, text):
        return np.stack([self._vec(text)])
