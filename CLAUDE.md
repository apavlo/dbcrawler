# DBMS Vendor Web Analyzer

## Overview

This project implements a focused semantic web crawler and classifier for
database management system (DBMS) vendor websites.

The program accepts a list of DBMS homepage URLs and extracts:

1. The official blog URL for the vendor.
2. Whether the homepage markets the product using concepts related to:
   - AI-native systems
   - agentic workflows
   - LLM-centric applications
   - vector search / embeddings
   - generative AI infrastructure

The system combines:
- deterministic heuristics
- lightweight crawling
- semantic classification via a local LLM through Ollama

This is NOT intended to be a general-purpose crawler or search engine.

The crawler should remain:
- shallow
- explainable
- reproducible
- debuggable

---

# Core Design Principles

## 1. Deterministic First

Always prefer:
- explicit heuristics
- URL pattern matching
- keyword scoring
- structured extraction

Use the LLM only for:
- semantic refinement
- ambiguity resolution
- classification
- fallback decision-making

Avoid asking the LLM to parse raw HTML directly.

---

## 2. Keep Crawling Shallow

The crawler should:
- always fetch the homepage
- optionally fetch 1-hop candidate pages
- avoid recursive traversal

Do NOT:
- spider entire domains
- index documentation
- crawl paginated archives
- follow arbitrary external links

Maximum crawl depth should generally be:

```python
MAX_DEPTH = 1
```

---

## 3. Preserve Evidence

All classifications must preserve evidence.

Every output record should include:
- matched phrases
- extracted context windows
- source URL
- confidence score
- LLM reasoning summary

The system should be auditable.

---

## 4. Snapshot Everything

For debugging and reproducibility, save:

```text
snapshots/
    vendor_name/
        homepage.html
        visible_text.txt
        links.json
        analysis.json
```

This is mandatory.

---

# Recommended Technology Stack

## HTTP

Use:

- httpx
- asyncio

Requirements:
- async support
- timeouts
- retries
- redirect handling

Avoid:
- requests (synchronous bottleneck)

---

## HTML Parsing

Preferred:
- selectolax

Fallback:
- BeautifulSoup

selectolax is significantly faster and sufficient for this project.

---

## Content Extraction

Use:
- trafilatura

Purpose:
- extract readable visible text
- remove boilerplate
- normalize whitespace

---

## Browser Rendering

Use:
- Playwright

Many DBMS vendor sites use:
- React
- Next.js
- client-side hydration

The crawler should:
1. attempt static fetch first
2. fall back to Playwright if insufficient text is extracted

Suggested heuristic:

```python
if len(visible_text) < 1000:
    render_with_playwright()
```

---

## Domain Normalization

Use:
- tldextract

Purpose:
- normalize subdomains
- compare ownership
- identify official blog domains

---

## LLM Integration

Use:
- Ollama local API

Recommended models:
- qwen3
- llama3.1
- mistral

Target size:
- 7B to 14B

This task does NOT require frontier reasoning models.

---

# System Architecture

```text
Input URLs
    ↓
Async Fetcher
    ↓
HTML + JS Rendering
    ↓
Text Extraction
    ↓
Link Extraction
    ↓
Blog URL Detection
    ↓
AI/Agentic Classification
    ↓
Structured Output
```

---

# Project Structure

```text
dbms_vendor_analyzer/
│
├── main.py
├── config.py
├── requirements.txt
│
├── crawler/
│   ├── fetcher.py
│   ├── renderer.py
│   ├── extractor.py
│   └── robots.py
│
├── analysis/
│   ├── blog_detector.py
│   ├── ai_classifier.py
│   ├── keyword_matcher.py
│   └── llm_client.py
│
├── models/
│   └── schema.py
│
├── storage/
│   ├── snapshots.py
│   └── output.py
│
├── prompts/
│   ├── classify_ai.txt
│   └── select_blog.txt
│
├── data/
│   ├── input_urls.txt
│   └── results.json
│
└── snapshots/
```

---

# Data Model

Use explicit typed schemas.

Preferred:
- pydantic

Example:

```python
class VendorAnalysis(BaseModel):
    homepage_url: str

    blog_url: str | None
    blog_confidence: float

    ai_marketing_detected: bool

    ai_classification: str
    ai_confidence: float

    matched_keywords: list[str]
    evidence_phrases: list[str]

    llm_summary: str | None
```

---

# Blog URL Detection Strategy

## Goal

Identify the official vendor blog.

---

## Candidate Extraction

Extract all anchor tags:

```python
<a href="...">anchor text</a>
```

Normalize:
- absolute URLs
- remove fragments
- lowercase hostname

---

## Strong URL Signals

Positive indicators:

```text
/blog
/blogs
/news
/articles
/resources/blog
/engineering
```

Subdomain indicators:

```text
blog.company.com
engineering.company.com
```

---

## Anchor Text Signals

Positive indicators:

```text
blog
engineering blog
news
articles
updates
resources
```

---

## Negative Signals

Reduce score for:
- social media
- Medium mirrors
- LinkedIn
- generic documentation

Examples:

```text
twitter.com
linkedin.com
facebook.com
youtube.com
```

---

## Scoring

Implement a weighted scoring system.

Example:

```python
score += 10 if "/blog" in url
score += 8 if "blog" in anchor_text
score += 5 if same_registered_domain
score -= 5 if external_social_media
```

The detector should return:
- selected URL
- confidence score
- scoring explanation

---

## LLM Fallback

Only invoke the LLM if:
- multiple candidates have similar scores
- no candidate exceeds threshold

The LLM should receive:
- homepage URL
- candidate URLs
- anchor text
- scores

Do NOT provide raw HTML.

---

# AI / Agentic Detection

## Goal

Determine whether the homepage markets the DBMS as:
- AI-native
- agentic
- LLM-centric
- vector-search centric
- generative AI infrastructure

---

# Phase 1: Keyword Detection

Use deterministic matching first.

---

## Direct Terms

```python
DIRECT_TERMS = [
    "ai-native",
    "ai native",
    "agentic",
    "llm-native",
    "ai-first",
]
```

---

## Semantic Terms

```python
SEMANTIC_TERMS = [
    "vector search",
    "embeddings",
    "rag",
    "retrieval augmented generation",
    "generative ai",
    "copilot",
    "agents",
    "ai applications",
    "semantic search",
    "llm applications",
]
```

---

# Context Extraction

When a keyword is found:
- extract surrounding text window
- preserve sentence boundaries if possible

Suggested window:

```python
WINDOW_SIZE = 250
```

---

# LLM Classification

The LLM should classify the vendor into categories:

```text
AI_NATIVE
AGENTIC
AI_ENABLED
VECTOR_SEARCH_FOCUSED
NOT_AI_FOCUSED
```

The LLM must return structured JSON.

---

## Prompting Rules

NEVER:
- send raw HTML
- send entire pages
- ask open-ended questions

ALWAYS:
- constrain outputs
- request JSON
- provide extracted evidence only

---

# Fetching Strategy

## Static Fetch First

Always attempt:
- normal HTTP GET
- HTML parsing
- text extraction

---

## Browser Fallback

If:
- text is too small
- page appears shell-rendered
- content missing

Then:
- render with Playwright

---

# Async Concurrency

The crawler should use asyncio throughout.

Recommended concurrency:

```python
MAX_CONCURRENT_REQUESTS = 10
```

Use semaphores to avoid overwhelming sites.

---

# Error Handling

The system must never crash due to:
- invalid HTML
- timeouts
- SSL issues
- malformed URLs
- JavaScript failures

All failures should produce:
- structured error records
- partial output if possible

---

# Logging

Use structured logging.

Each major stage should log:
- URL
- elapsed time
- fetch method
- classification outcome
- confidence

---

# Output Formats

Generate:
- JSON
- CSV

Suggested CSV columns:

```text
homepage_url
blog_url
ai_marketing_detected
ai_classification
ai_confidence
matched_keywords
```

---

# Recommended Development Order

Implement in this order:

1. async homepage fetcher
2. HTML parsing
3. text extraction
4. link extraction
5. blog URL scoring
6. keyword matching
7. snapshot persistence
8. Ollama integration
9. semantic classification
10. CSV/JSON export
11. Playwright fallback

---

# Non-Goals

This project should NOT:
- crawl entire websites
- scrape documentation
- build a search index
- summarize products
- benchmark DBMSs
- classify technical architecture

Stay focused on:
- blog detection
- AI/agentic marketing analysis

---

# Performance Expectations

Expected scale:
- tens to hundreds of vendors

Not intended for:
- internet-scale crawling

Optimization priorities:
1. reliability
2. explainability
3. reproducibility
4. maintainability

NOT:
- maximum throughput

---

# Testing Recommendations

Create fixtures for:
- static sites
- React sites
- broken HTML
- no-blog vendors
- vendors with external blogs
- AI-heavy marketing pages
- non-AI vendors

Avoid relying solely on live websites during testing.

---

# Future Extensions

Potential future additions:
- monitor homepage changes over time
- trend analysis
- vendor clustering
- marketing language evolution
- documentation crawling
- release-note extraction
- vector database detection

These should remain separate modules.
