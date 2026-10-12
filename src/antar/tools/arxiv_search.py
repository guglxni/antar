"""arXiv search + abstract fetch with exponential backoff and jitter (MATH.md §7).

Public API, no auth. Parses Atom. Bounded results to cap downstream cost.
"""
from __future__ import annotations

import random
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from dataclasses import dataclass

ARXIV_API = "https://export.arxiv.org/api/query"
ATOM = "{http://www.w3.org/2005/Atom}"
_MAX_RESULTS = 8
_BACKOFF_BASE = 1.0
_BACKOFF_CAP = 30.0
_JITTER = 1.0
_MAX_ATTEMPTS = 3


@dataclass
class Paper:
    arxiv_id: str
    title: str
    abstract: str
    published: str
    relevance: float = 0.0


class ArxivError(Exception):
    pass


def _get(url: str) -> bytes:
    delay = _BACKOFF_BASE
    for attempt in range(_MAX_ATTEMPTS):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "antar-agent"})
            with urllib.request.urlopen(req, timeout=20) as r:
                return r.read()
        except Exception as e:  # transient / 429 / 5xx
            if attempt == _MAX_ATTEMPTS - 1:
                raise ArxivError(f"arXiv failed after {_MAX_ATTEMPTS} attempts: {e}") from e
            time.sleep(min(_BACKOFF_CAP, delay) + random.uniform(0, _JITTER))
            delay *= 2
    raise ArxivError("unreachable")


def search(query: str, max_results: int = _MAX_RESULTS) -> list[Paper]:
    q = urllib.parse.urlencode({
        "search_query": f"all:{query}",
        "start": 0,
        "max_results": max_results,
        "sortBy": "relevance",
    })
    root = ET.fromstring(_get(f"{ARXIV_API}?{q}"))
    papers: list[Paper] = []
    for entry in root.findall(f"{ATOM}entry"):
        id_url = entry.findtext(f"{ATOM}id", "")
        arxiv_id = id_url.rsplit("/abs/", 1)[-1].split("v")[0]
        title = " ".join((entry.findtext(f"{ATOM}title", "") or "").split())
        abstract = " ".join((entry.findtext(f"{ATOM}summary", "") or "").split())
        published = entry.findtext(f"{ATOM}published", "")[:10]
        if arxiv_id and title:
            papers.append(Paper(arxiv_id, title, abstract, published))
    return papers


def fetch_abstract(arxiv_id: str) -> Paper | None:
    q = urllib.parse.urlencode({"id_list": arxiv_id, "max_results": 1})
    root = ET.fromstring(_get(f"{ARXIV_API}?{q}"))
    entry = root.find(f"{ATOM}entry")
    if entry is None:
        return None
    title = " ".join((entry.findtext(f"{ATOM}title", "") or "").split())
    abstract = " ".join((entry.findtext(f"{ATOM}summary", "") or "").split())
    published = entry.findtext(f"{ATOM}published", "")[:10]
    if not title or "not found" in title.lower():
        return None
    return Paper(arxiv_id, title, abstract, published)
