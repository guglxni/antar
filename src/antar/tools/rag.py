"""Hybrid RAG retrieval over arXiv — the Researcher's discovery engine.

FOSS pattern (rag-lens / vstash / local-semantic-search): dense embeddings + BM25,
fused with Reciprocal Rank Fusion (no score calibration needed), plus a recency prior
for "state of the art". Fully local — embeddings via sentence-transformers (bge-small,
384-dim), NO API key. Gracefully degrades to BM25-only if the embedding model is
unavailable (offline).

Pipeline:  arXiv candidates ─▶ BM25 rank ─┐
                          ─▶ dense rank ──┴─▶ RRF fuse ─▶ recency boost ─▶ ranked papers

Math: RRF score = Σ 1/(k + rank_i),  k=60 (Cormack et al. 2009). See MATH.md §3/§8.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

import neatlogs

from .arxiv_search import Paper

_RRF_K = 60
_LAMBDA = math.log(2) / 365.0   # recency half-life = 1 year (MATH.md §3)

_embedder = None
_embedder_tried = False


def _get_embedder():
    """Lazy-load the local embedder once; None if unavailable (offline fallback)."""
    global _embedder, _embedder_tried
    if _embedder_tried:
        return _embedder
    _embedder_tried = True
    try:
        from sentence_transformers import SentenceTransformer
        _embedder = SentenceTransformer("BAAI/bge-small-en-v1.5")
    except Exception as e:  # offline / no torch / model not cached
        neatlogs.log("local embedder unavailable — BM25-only retrieval",
                     level="warning", error=str(e))
        _embedder = None
    return _embedder


def _tokenize(text: str) -> list[str]:
    return [t.strip(".,():;\"'").lower() for t in text.split() if len(t) > 2]


def _bm25_rank(query: str, docs: list[str]) -> list[int]:
    """Return doc indices ordered by BM25 score (best first)."""
    from rank_bm25 import BM25Okapi
    tokenized = [_tokenize(d) for d in docs]
    if not any(tokenized):
        return list(range(len(docs)))
    bm25 = BM25Okapi(tokenized)
    scores = bm25.get_scores(_tokenize(query))
    return sorted(range(len(docs)), key=lambda i: scores[i], reverse=True)


def _dense_rank(query: str, docs: list[str]) -> list[int] | None:
    """Return doc indices ordered by cosine similarity, or None if no embedder."""
    emb = _get_embedder()
    if emb is None:
        return None
    import numpy as np
    q = emb.encode([query], normalize_embeddings=True)[0]
    D = emb.encode(docs, normalize_embeddings=True)
    sims = (D @ q)
    return sorted(range(len(docs)), key=lambda i: float(sims[i]), reverse=True)


def _rrf(rank_lists: list[list[int]]) -> dict[int, float]:
    """Reciprocal Rank Fusion over multiple ranked index lists."""
    score: dict[int, float] = {}
    for ranks in rank_lists:
        for r, idx in enumerate(ranks):
            score[idx] = score.get(idx, 0.0) + 1.0 / (_RRF_K + r + 1)
    return score


def _recency(published: str) -> float:
    """Exponential recency prior e^{-λ Δdays} (MATH.md §3)."""
    try:
        from datetime import date
        y, m, d = (int(x) for x in published.split("-")[:3])
        age_days = max(0, (date.today() - date(y, m, d)).days)
        return math.exp(-_LAMBDA * age_days)
    except Exception:
        return 0.5


@neatlogs.span(kind="RETRIEVER", name="hybrid_retrieve")
def rerank(query: str, papers: list[Paper], top_k: int = 8,
           alpha: float = 0.85) -> list[Paper]:
    """Rank arXiv candidates by hybrid BM25+dense RRF fused with recency.

    relevance(p) = alpha * RRF_rank_score + (1-alpha) * recency(published)
    Returns papers sorted best-first with .relevance set. Never raises — on any
    failure returns the input order (research must not abort the pipeline).
    """
    if not papers:
        return papers
    try:
        docs = [f"{p.title}. {p.abstract}" for p in papers]
        rank_lists = [_bm25_rank(query, docs)]
        dense = _dense_rank(query, docs)
        if dense is not None:
            rank_lists.append(dense)
        fused = _rrf(rank_lists)
        # normalise RRF to [0,1] then blend with recency prior
        mx = max(fused.values()) or 1.0
        for i, p in enumerate(papers):
            rrf_norm = fused.get(i, 0.0) / mx
            p.relevance = alpha * rrf_norm + (1 - alpha) * _recency(p.published)
        ranked = sorted(papers, key=lambda p: p.relevance, reverse=True)
        return ranked[:top_k]
    except Exception as e:
        neatlogs.log("hybrid rerank failed — returning input order",
                     level="warning", error=str(e))
        return papers[:top_k]
