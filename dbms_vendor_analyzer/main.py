from __future__ import annotations

import argparse
import asyncio
import logging
import sys
from pathlib import Path
from urllib.parse import urlparse

import httpx

from dbms_vendor_analyzer.analysis.ai_classifier import classify_heuristic, classify_with_llm
from dbms_vendor_analyzer.analysis.blog_detector import detect_blog, needs_llm_tiebreak
from dbms_vendor_analyzer.analysis.keyword_matcher import find_matches
from dbms_vendor_analyzer.analysis.llm_client import OllamaError, call_llm_json
from dbms_vendor_analyzer.config import INPUT_URLS_FILE, MIN_TEXT_LENGTH
from dbms_vendor_analyzer.crawler.fetcher import build_client, fetch_static, make_semaphore
from dbms_vendor_analyzer.crawler.renderer import fetch_with_playwright
from dbms_vendor_analyzer.models.schema import BlogCandidate, VendorAnalysis
from dbms_vendor_analyzer.prompts import load_prompt
from dbms_vendor_analyzer.storage.output import load_urls, write_results
from dbms_vendor_analyzer.storage.snapshots import save_analysis, save_crawl

logger = logging.getLogger(__name__)


def _vendor_name(url: str) -> str:
    host = urlparse(url).hostname or url
    parts = host.lstrip("www.").split(".")
    return parts[0] if parts else host


async def _analyze_one(
    url: str,
    client: httpx.AsyncClient,
    sem: asyncio.Semaphore,
    use_llm: bool,
) -> VendorAnalysis:
    vendor = _vendor_name(url)
    analysis = VendorAnalysis(homepage_url=url, vendor_name=vendor)

    async with sem:
        result = await fetch_static(url, client)

    # Playwright fallback
    if result.error or len(result.visible_text) < MIN_TEXT_LENGTH:
        logger.info("%s: falling back to Playwright (text=%d)", vendor, len(result.visible_text))
        async with sem:
            result = await fetch_with_playwright(url)

    analysis.fetch_method = result.fetch_method
    analysis.visible_text_length = len(result.visible_text)

    if result.error and not result.visible_text:
        analysis.error = result.error
        await _snapshot(result, analysis, vendor)
        return analysis

    # Blog detection
    best_candidate, all_candidates = detect_blog(result.links, result.final_url)
    analysis.blog_candidates = all_candidates[:10]

    if best_candidate:
        analysis.blog_url = best_candidate.url
        analysis.blog_confidence = min(1.0, best_candidate.score / 30.0)

    if use_llm and needs_llm_tiebreak(all_candidates):
        logger.info("%s: invoking LLM for blog tiebreak", vendor)
        try:
            blog_url, blog_conf, reasoning = await _llm_blog_select(url, all_candidates[:5])
            analysis.blog_url = blog_url
            analysis.blog_confidence = blog_conf
            analysis.llm_blog_reasoning = reasoning
        except OllamaError as exc:
            logger.warning("%s: LLM blog tiebreak failed: %s", vendor, exc)

    # Keyword matching
    matches = find_matches(result.visible_text, result.final_url)
    analysis.keyword_matches = matches
    analysis.matched_keywords = list({m.term for m in matches})
    analysis.evidence_phrases = [m.context[:200] for m in matches[:5]]

    # AI classification
    label, confidence, all_terms = classify_heuristic(matches)
    analysis.ai_classification = label
    analysis.ai_confidence = confidence
    analysis.ai_marketing_detected = label != "NOT_AI_FOCUSED"

    if use_llm and matches:
        label, confidence, summary = await classify_with_llm(url, matches, label, confidence)
        analysis.ai_classification = label
        analysis.ai_confidence = confidence
        analysis.ai_marketing_detected = label != "NOT_AI_FOCUSED"
        analysis.llm_summary = summary

    await _snapshot(result, analysis, vendor)
    return analysis


async def _llm_blog_select(
    homepage_url: str,
    candidates: list[BlogCandidate],
) -> tuple[str | None, float, str]:
    from dbms_vendor_analyzer.config import PROMPTS_DIR
    template = load_prompt(PROMPTS_DIR / "select_blog.txt")
    lines = "\n".join(
        f"  score={c.score:.1f}  url={c.url}  anchor=\"{c.anchor_text}\""
        for c in candidates
    )
    prompt = template.format(homepage_url=homepage_url, candidates=lines)
    result = await call_llm_json(prompt)
    blog_url = result.get("blog_url") or None
    confidence = float(result.get("confidence", 0.5))
    reasoning = str(result.get("reasoning", ""))
    return blog_url, confidence, reasoning


async def _snapshot(result, analysis: VendorAnalysis, vendor: str) -> None:  # type: ignore[no-untyped-def]
    try:
        await save_crawl(result, vendor)
        await save_analysis(analysis, vendor)
    except Exception as exc:
        logger.error("Snapshot failed for %s: %s", vendor, exc)


async def run(urls: list[str], use_llm: bool) -> list[VendorAnalysis]:
    sem = make_semaphore()
    results: list[VendorAnalysis] = []

    async with build_client() as client:
        tasks = [_analyze_one(url, client, sem, use_llm) for url in urls]
        for coro in asyncio.as_completed(tasks):
            analysis = await coro
            results.append(analysis)
            status = "✓" if not analysis.error else "✗"
            print(
                f"{status} {analysis.vendor_name:20s}  "
                f"blog={analysis.blog_url or '—':50s}  "
                f"{analysis.ai_classification}"
            )

    return results


def main() -> None:
    parser = argparse.ArgumentParser(description="DBMS vendor web analyzer")
    parser.add_argument("--input", type=Path, default=INPUT_URLS_FILE)
    parser.add_argument("--no-llm", action="store_true", help="Skip all LLM calls")
    parser.add_argument("--verbose", "-v", action="store_true")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    if not args.input.exists():
        print(f"Input file not found: {args.input}", file=sys.stderr)
        sys.exit(1)

    urls = load_urls(args.input)
    if not urls:
        print("No URLs found in input file.", file=sys.stderr)
        sys.exit(1)

    print(f"Analyzing {len(urls)} vendors (LLM={'off' if args.no_llm else 'on'})…\n")
    analyses = asyncio.run(run(urls, use_llm=not args.no_llm))

    asyncio.run(write_results(analyses))

    ai_count = sum(1 for a in analyses if a.ai_marketing_detected)
    print(f"\nDone. {ai_count}/{len(analyses)} vendors have AI marketing.")
    print("Results: data/results.json  data/results.csv")


if __name__ == "__main__":
    main()
