from __future__ import annotations

import json
import logging
import re
from pathlib import Path

import aiofiles

from dbms_vendor_analyzer.config import SNAPSHOTS_DIR
from dbms_vendor_analyzer.models.schema import CrawlResult, VendorAnalysis

logger = logging.getLogger(__name__)


def vendor_dir(vendor_name: str) -> Path:
    safe = re.sub(r"[^\w\-]", "_", vendor_name.lower())
    return SNAPSHOTS_DIR / safe


async def save_crawl(result: CrawlResult, vendor_name: str) -> Path:
    d = vendor_dir(vendor_name)
    d.mkdir(parents=True, exist_ok=True)

    await _write(d / "homepage.html", result.html)
    await _write(d / "visible_text.txt", result.visible_text)
    await _write_json(d / "links.json", result.links)

    logger.debug("Saved crawl snapshot for %s → %s", vendor_name, d)
    return d


async def save_analysis(analysis: VendorAnalysis, vendor_name: str) -> None:
    d = vendor_dir(vendor_name)
    d.mkdir(parents=True, exist_ok=True)
    await _write_json(d / "analysis.json", analysis.model_dump())
    logger.debug("Saved analysis snapshot for %s", vendor_name)


async def _write(path: Path, content: str) -> None:
    async with aiofiles.open(path, "w", encoding="utf-8", errors="replace") as f:
        await f.write(content)


async def _write_json(path: Path, data: object) -> None:
    async with aiofiles.open(path, "w", encoding="utf-8") as f:
        await f.write(json.dumps(data, indent=2, ensure_ascii=False))
