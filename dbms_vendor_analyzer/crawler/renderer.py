from __future__ import annotations

import logging
import time

from dbms_vendor_analyzer.crawler.extractor import extract_links, extract_text
from dbms_vendor_analyzer.models.schema import CrawlResult

logger = logging.getLogger(__name__)


async def fetch_with_playwright(url: str) -> CrawlResult:
    t0 = time.monotonic()
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        logger.error("Playwright not installed. Run: uv run playwright install chromium")
        return CrawlResult(
            url=url, final_url=url, html="", visible_text="",
            links=[], fetch_method="playwright",
            elapsed_seconds=time.monotonic() - t0,
            error="playwright not installed",
        )

    try:
        async with async_playwright() as pw:
            browser = await pw.chromium.launch(headless=True)
            context = await browser.new_context(
                user_agent=(
                    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                    "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
                ),
                java_script_enabled=True,
            )
            page = await context.new_page()
            await page.goto(url, wait_until="networkidle", timeout=45_000)
            final_url = page.url
            html = await page.content()
            await browser.close()

        elapsed = time.monotonic() - t0
        visible_text = extract_text(html)
        links = extract_links(html, final_url)
        logger.info(
            "Playwright fetch OK %s → %s (%.1fs, %d chars)",
            url, final_url, elapsed, len(visible_text),
        )
        return CrawlResult(
            url=url, final_url=final_url, html=html, visible_text=visible_text,
            links=links, fetch_method="playwright", elapsed_seconds=elapsed,
        )

    except Exception as exc:
        elapsed = time.monotonic() - t0
        logger.warning("Playwright fetch failed for %s: %s", url, exc)
        return CrawlResult(
            url=url, final_url=url, html="", visible_text="",
            links=[], fetch_method="playwright",
            elapsed_seconds=elapsed, error=str(exc),
        )
