from __future__ import annotations

import logging
import re
from urllib.parse import urldefrag, urljoin, urlparse

import trafilatura
from selectolax.parser import HTMLParser

logger = logging.getLogger(__name__)


def extract_text(html: str) -> str:
    if not html:
        return ""

    text = trafilatura.extract(
        html,
        include_comments=False,
        include_tables=True,
        no_fallback=False,
        favor_precision=False,
    )
    if text:
        return _normalize_whitespace(text)

    # Fallback: strip tags with selectolax
    try:
        tree = HTMLParser(html)
        for tag in tree.css("script, style, noscript, head"):
            tag.decompose()
        raw = tree.body.text(separator=" ") if tree.body else ""
        return _normalize_whitespace(raw)
    except Exception as exc:
        logger.debug("selectolax text fallback failed: %s", exc)
        return ""


def extract_links(html: str, base_url: str) -> list[dict[str, str]]:
    if not html:
        return []

    try:
        tree = HTMLParser(html)
    except Exception as exc:
        logger.debug("selectolax link parse failed: %s", exc)
        return []

    links: list[dict[str, str]] = []
    seen: set[str] = set()

    for node in tree.css("a[href]"):
        href = node.attributes.get("href", "") or ""
        text = _normalize_whitespace(node.text())

        # Skip anchors, mailto, javascript
        if not href or href.startswith(("#", "mailto:", "javascript:", "tel:")):
            continue

        # Remove fragment and make absolute
        href, _ = urldefrag(href)
        absolute = _safe_urljoin(base_url, href)
        if not absolute:
            continue

        # Only http/https
        parsed = urlparse(absolute)
        if parsed.scheme not in ("http", "https"):
            continue

        key = absolute.lower()
        if key in seen:
            continue
        seen.add(key)

        links.append({"url": absolute, "text": text[:200]})

    return links


def _safe_urljoin(base: str, url: str) -> str:
    try:
        return urljoin(base, url)
    except Exception:
        return ""


def _normalize_whitespace(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()
