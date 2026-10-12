"""RAG hybrid-retrieval tests (BM25 path runs offline; dense path degrades gracefully)."""
from __future__ import annotations

from antar.tools import rag
from antar.tools.arxiv_search import Paper


def _papers():
    return [
        Paper("2310.01848", "Gradient Clipping Revisited", "We study gradient clipping for stability.", "2023-10-02"),
        Paper("1706.03762", "Attention Is All You Need", "The transformer architecture.", "2017-06-12"),
        Paper("2001.00001", "AdamW and Warmup", "Decoupled weight decay and warmup schedules.", "2020-01-01"),
    ]


def test_rerank_reorders_by_relevance():
    out = rag.rerank("gradient clipping", _papers(), top_k=3)
    assert out and out[0].title == "Gradient Clipping Revisited"
    assert all(0.0 <= p.relevance for p in out)


def test_rerank_empty():
    assert rag.rerank("x", []) == []


def test_rerank_respects_top_k():
    out = rag.rerank("optimizer", _papers(), top_k=2)
    assert len(out) == 2


def test_rrf_math():
    # item 0 ranks 1st in both lists → strictly highest fused score
    fused = rag._rrf([[0, 1, 2], [0, 2, 1]])
    assert fused[0] > fused[1] and fused[0] > fused[2]
    # an item absent from one list scores lower than one present in both
    fused2 = rag._rrf([[0, 1], [0, 1, 2]])
    assert fused2[0] >= fused2[2]
