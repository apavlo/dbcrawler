from __future__ import annotations

import logging
from urllib.parse import urlparse

import tldextract

from dbms_vendor_analyzer.config import (
    BLOG_ANCHOR_KEYWORDS,
    BLOG_SCORE_THRESHOLD,
    BLOG_SIMILARITY_RATIO,
    BLOG_SUBDOMAIN_SCORE,
    BLOG_URL_SCORE,
    SOCIAL_MEDIA_DOMAINS,
)
from dbms_vendor_analyzer.models.schema import BlogCandidate

logger = logging.getLogger(__name__)


def detect_blog(
    links: list[dict[str, str]],
    homepage_url: str,
) -> tuple[BlogCandidate | None, list[BlogCandidate]]:
    """
    Returns (best_candidate, all_candidates_sorted).
    best_candidate is None if no candidate clears the threshold.
    """
    home_ext = tldextract.extract(homepage_url)
    home_registered = f"{home_ext.domain}.{home_ext.suffix}"

    scored: list[BlogCandidate] = []
    for link in links:
        candidate = _score(link["url"], link["text"], home_registered)
        if candidate.score > 0:
            scored.append(candidate)

    # Deduplicate by URL, keep highest score
    by_url: dict[str, BlogCandidate] = {}
    for c in scored:
        key = c.url.rstrip("/").lower()
        if key not in by_url or c.score > by_url[key].score:
            by_url[key] = c

    ranked = sorted(by_url.values(), key=lambda c: c.score, reverse=True)

    if not ranked:
        return None, []

    best = ranked[0]
    if best.score < BLOG_SCORE_THRESHOLD:
        logger.debug("Best blog candidate %s score %.1f below threshold", best.url, best.score)
        return None, ranked

    return best, ranked


def needs_llm_tiebreak(candidates: list[BlogCandidate]) -> bool:
    if len(candidates) < 2:
        return False
    top, second = candidates[0].score, candidates[1].score
    if top == 0:
        return False
    return (top - second) / top <= BLOG_SIMILARITY_RATIO


def _score(url: str, anchor_text: str, home_registered: str) -> BlogCandidate:
    breakdown: dict[str, float] = {}
    parsed = urlparse(url)
    hostname = parsed.hostname or ""
    path = parsed.path.lower()
    anchor_lower = anchor_text.lower().strip()

    link_ext = tldextract.extract(url)
    link_registered = f"{link_ext.domain}.{link_ext.suffix}"

    # Penalise social media / off-domain entirely
    for social in SOCIAL_MEDIA_DOMAINS:
        if social in hostname:
            breakdown["social_penalty"] = -50.0
            return BlogCandidate(
                url=url, anchor_text=anchor_text, score=-50.0, score_breakdown=breakdown
            )

    # Same registered domain bonus
    if link_registered == home_registered:
        breakdown["same_domain"] = 5.0
    else:
        breakdown["external_domain"] = -3.0

    # URL path signals
    for path_fragment, weight in BLOG_URL_SCORE.items():
        if path.startswith(path_fragment) or f"{path_fragment}/" in path:
            breakdown[f"url:{path_fragment}"] = weight
            break  # only award the best matching path

    # Subdomain signals
    subdomain = link_ext.subdomain.lower()
    for sub, weight in BLOG_SUBDOMAIN_SCORE.items():
        if sub == subdomain:
            breakdown[f"subdomain:{sub}"] = weight
            break

    # Anchor text signals
    for keyword, weight in BLOG_ANCHOR_KEYWORDS.items():
        if keyword in anchor_lower:
            breakdown[f"anchor:{keyword}"] = weight
            break  # one anchor match

    total = sum(breakdown.values())
    return BlogCandidate(url=url, anchor_text=anchor_text, score=total, score_breakdown=breakdown)
