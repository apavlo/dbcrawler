from __future__ import annotations

from pydantic import BaseModel, Field


class BlogCandidate(BaseModel):
    url: str
    anchor_text: str
    score: float
    score_breakdown: dict[str, float] = Field(default_factory=dict)


class KeywordMatch(BaseModel):
    term: str
    term_type: str  # "direct" | "semantic"
    context: str    # surrounding text window
    source_url: str


class VendorAnalysis(BaseModel):
    homepage_url: str
    vendor_name: str

    # Blog detection
    blog_url: str | None = None
    blog_confidence: float = 0.0
    blog_candidates: list[BlogCandidate] = Field(default_factory=list)

    # AI classification
    ai_marketing_detected: bool = False
    ai_classification: str = "NOT_AI_FOCUSED"
    ai_confidence: float = 0.0

    # Evidence
    matched_keywords: list[str] = Field(default_factory=list)
    keyword_matches: list[KeywordMatch] = Field(default_factory=list)
    evidence_phrases: list[str] = Field(default_factory=list)

    # LLM outputs
    llm_summary: str | None = None
    llm_blog_reasoning: str | None = None

    # Meta
    fetch_method: str = "static"  # "static" | "playwright"
    visible_text_length: int = 0
    error: str | None = None


class CrawlResult(BaseModel):
    url: str
    final_url: str
    html: str
    visible_text: str
    links: list[dict[str, str]]  # [{"url": ..., "text": ...}]
    fetch_method: str
    elapsed_seconds: float
    error: str | None = None
