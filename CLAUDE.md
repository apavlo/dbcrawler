# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

DBMS vendor web analyzer: given a list of DBMS homepage URLs, find each vendor's official blog URL and classify whether the homepage markets the product as AI-native/agentic/LLM-focused. Uses deterministic heuristics first; LLM (via Ollama) only as fallback.

## Commands

This project uses `uv` with Python 3.11+.

```bash
# Install dependencies
uv sync

# Run the analyzer
uv run python -m dbms_vendor_analyzer.main --input data/input_urls.txt

# Lint
uv run ruff check .

# Type check
uv run mypy .

# Run tests
uv run pytest

# Run a single test
uv run pytest tests/test_blog_detector.py::test_score_blog_url -v
```

Playwright browsers must be installed separately:
```bash
uv run playwright install chromium
```

Ollama must be running locally (`ollama serve`) with a model pulled (e.g., `ollama pull qwen3`).

## Architecture

The pipeline is: fetch homepage → extract text → extract links → score blog candidates → match AI keywords → LLM classification (fallback only) → snapshot + output.

**Key modules:**
- `crawler/fetcher.py` — async httpx fetcher; always tries static first
- `crawler/renderer.py` — Playwright fallback, triggered when `len(visible_text) < 1000`
- `crawler/extractor.py` — trafilatura for readable text, selectolax for link/DOM parsing
- `analysis/blog_detector.py` — weighted URL+anchor scoring; calls LLM only when top candidates are within 20% of each other or none exceed threshold
- `analysis/keyword_matcher.py` — deterministic DIRECT_TERMS / SEMANTIC_TERMS matching with 250-char context windows
- `analysis/ai_classifier.py` — maps keyword evidence to `AI_NATIVE | AGENTIC | AI_ENABLED | VECTOR_SEARCH_FOCUSED | NOT_AI_FOCUSED`
- `analysis/llm_client.py` — Ollama HTTP client; always sends extracted evidence, never raw HTML; always requests JSON output
- `models/schema.py` — Pydantic `VendorAnalysis` model; source of truth for all data shapes
- `storage/snapshots.py` — writes `snapshots/<vendor>/` (homepage.html, visible_text.txt, links.json, analysis.json); mandatory for every run
- `storage/output.py` — writes `data/results.json` and `data/results.csv`

**Concurrency:** `asyncio` with `asyncio.Semaphore(MAX_CONCURRENT_REQUESTS)` around all network calls. `MAX_CONCURRENT_REQUESTS = 10`, `MAX_DEPTH = 1`.

## Key Constraints

- **LLM is fallback only.** Heuristic/keyword logic runs first. LLM receives structured evidence (URL, anchor text, keyword matches, scores), never HTML.
- **Shallow crawl only.** Fetch homepage + at most the top blog candidate page. No recursive crawling.
- **Never crash on bad input.** All network/parse failures must produce a structured error record in the output, not an exception.
- **Snapshots are mandatory.** Every vendor processed must write its snapshot directory, even on partial failure.
- **tldextract** for all domain comparison (not string matching on hostnames).
