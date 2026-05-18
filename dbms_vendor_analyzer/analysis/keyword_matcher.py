from __future__ import annotations

import re

from dbms_vendor_analyzer.config import CONTEXT_WINDOW_SIZE, DIRECT_TERMS, SEMANTIC_TERMS
from dbms_vendor_analyzer.models.schema import KeywordMatch


def find_matches(text: str, source_url: str) -> list[KeywordMatch]:
    if not text:
        return []

    text_lower = text.lower()
    matches: list[KeywordMatch] = []
    seen_terms: set[str] = set()

    for term in DIRECT_TERMS:
        _collect(text, text_lower, term, "direct", source_url, matches, seen_terms)

    for term in SEMANTIC_TERMS:
        _collect(text, text_lower, term, "semantic", source_url, matches, seen_terms)

    return matches


def _collect(
    text: str,
    text_lower: str,
    term: str,
    term_type: str,
    source_url: str,
    out: list[KeywordMatch],
    seen: set[str],
) -> None:
    if term in seen:
        return

    pattern = r"\b" + re.escape(term) + r"\b"
    m = re.search(pattern, text_lower)
    if not m:
        return

    seen.add(term)
    start = max(0, m.start() - CONTEXT_WINDOW_SIZE)
    end = min(len(text), m.end() + CONTEXT_WINDOW_SIZE)
    context = text[start:end].strip()

    out.append(KeywordMatch(
        term=term,
        term_type=term_type,
        context=context,
        source_url=source_url,
    ))
