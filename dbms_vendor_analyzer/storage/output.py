from __future__ import annotations

import csv
import json
import logging
from pathlib import Path

import aiofiles

from dbms_vendor_analyzer.config import RESULTS_CSV, RESULTS_JSON
from dbms_vendor_analyzer.models.schema import VendorAnalysis

logger = logging.getLogger(__name__)

CSV_COLUMNS = [
    "homepage_url",
    "vendor_name",
    "blog_url",
    "blog_confidence",
    "ai_marketing_detected",
    "ai_classification",
    "ai_confidence",
    "matched_keywords",
    "fetch_method",
    "error",
]


async def write_results(analyses: list[VendorAnalysis]) -> None:
    RESULTS_JSON.parent.mkdir(parents=True, exist_ok=True)

    records = [a.model_dump() for a in analyses]
    async with aiofiles.open(RESULTS_JSON, "w", encoding="utf-8") as f:
        await f.write(json.dumps(records, indent=2, ensure_ascii=False))
    logger.info("Wrote %d records to %s", len(analyses), RESULTS_JSON)

    _write_csv(analyses)


def _write_csv(analyses: list[VendorAnalysis]) -> None:
    RESULTS_CSV.parent.mkdir(parents=True, exist_ok=True)
    with open(RESULTS_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS, extrasaction="ignore")
        writer.writeheader()
        for a in analyses:
            row = a.model_dump()
            row["matched_keywords"] = "|".join(a.matched_keywords)
            writer.writerow(row)
    logger.info("Wrote CSV to %s", RESULTS_CSV)


def load_urls(path: Path) -> list[str]:
    urls: list[str] = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                urls.append(line)
    return urls
