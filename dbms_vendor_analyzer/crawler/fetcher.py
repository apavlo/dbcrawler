from __future__ import annotations

import asyncio
import logging
import time

import httpx
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from dbms_vendor_analyzer.config import MAX_CONCURRENT_REQUESTS, MAX_RETRIES, REQUEST_TIMEOUT
from dbms_vendor_analyzer.crawler.extractor import extract_links, extract_text
from dbms_vendor_analyzer.models.schema import CrawlResult

logger = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
}

_RETRYABLE = (httpx.TimeoutException, httpx.NetworkError, httpx.RemoteProtocolError)


def _make_retry(url: str):  # type: ignore[return]
    return retry(
        reraise=True,
        stop=stop_after_attempt(MAX_RETRIES),
        wait=wait_exponential(multiplier=1, min=1, max=8),
        retry=retry_if_exception_type(_RETRYABLE),
        before_sleep=lambda rs: logger.debug(
            "Retrying %s (attempt %d)", url, rs.attempt_number
        ),
    )


async def fetch_static(url: str, client: httpx.AsyncClient) -> CrawlResult:
    t0 = time.monotonic()

    @_make_retry(url)
    async def _get() -> httpx.Response:
        return await client.get(
            url, headers=HEADERS, follow_redirects=True, timeout=REQUEST_TIMEOUT
        )

    try:
        resp = await _get()
        resp.raise_for_status()
    except Exception as exc:
        elapsed = time.monotonic() - t0
        logger.warning("Static fetch failed for %s: %s", url, exc)
        return CrawlResult(
            url=url, final_url=url, html="", visible_text="",
            links=[], fetch_method="static", elapsed_seconds=elapsed,
            error=str(exc),
        )

    elapsed = time.monotonic() - t0
    html = resp.text
    final_url = str(resp.url)
    visible_text = extract_text(html)
    links = extract_links(html, final_url)

    logger.info(
        "Static fetch OK %s → %s (%.1fs, %d chars)", url, final_url, elapsed, len(visible_text)
    )
    return CrawlResult(
        url=url, final_url=final_url, html=html, visible_text=visible_text,
        links=links, fetch_method="static", elapsed_seconds=elapsed,
    )


def build_client() -> httpx.AsyncClient:
    return httpx.AsyncClient(
        http2=True,
        timeout=httpx.Timeout(REQUEST_TIMEOUT),
        limits=httpx.Limits(max_connections=MAX_CONCURRENT_REQUESTS, max_keepalive_connections=10),
    )


def make_semaphore() -> asyncio.Semaphore:
    return asyncio.Semaphore(MAX_CONCURRENT_REQUESTS)
