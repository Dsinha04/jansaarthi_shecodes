import pathlib
import sys
import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tests"))

import ingest   # noqa: E402
import rag      # noqa: E402
from fake_embedder import HashEmbedder   # noqa: E402
from llm import LLMError                 # noqa: E402


class StubLLM:
    def __init__(self, reply="Complain in writing to the Secretary first [1]."):
        self.reply, self.calls = reply, 0

    def generate(self, messages):
        self.calls += 1
        return self.reply


class DownLLM:
    def generate(self, messages):
        raise LLMError("service down")


@pytest.fixture(scope="session")
def built():
    index, meta, _ = ingest.build_index([ROOT / "tests/test_corpus/dummy_act.txt"], HashEmbedder(), size=40, overlap=8)
    return index, meta


@pytest.fixture
def make_engine(built):
    def _mk(llm=None, min_score=0.2):
        return rag.RAGEngine(embedder=HashEmbedder(), index=built[0], meta=built[1], llm=llm, min_score=min_score)
    return _mk
