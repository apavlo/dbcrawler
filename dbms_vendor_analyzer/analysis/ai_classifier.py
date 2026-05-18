from __future__ import annotations

import logging
from pathlib import Path

from dbms_vendor_analyzer.analysis.llm_client import OllamaError, call_llm_json
from dbms_vendor_analyzer.config import PROMPTS_DIR
from dbms_vendor_analyzer.models.schema import KeywordMatch

logger = logging.getLogger(__name__)

# Classification labels (ordered by specificity)
LABELS = ["AI_NATIVE", "AGENTIC", "AI_ENABLED", "VECTOR_SEARCH_FOCUSED", "NOT_AI_FOCUSED"]

# Heuristic thresholds
DIRECT_THRESHOLD = 1   # any direct term → at least AI_ENABLED
DIRECT_NATIVE_THRESHOLD = 2  # 2+ direct terms → AI_NATIVE candidate
SEMANTIC_THRESHOLD = 3  # 3+ semantic terms → AI_ENABLED


def classify_heuristic(matches: list[KeywordMatch]) -> tuple[str, float, list[str]]:
    """
    Returns (label, confidence, matched_term_list).
    Runs without LLM.
    """
    direct = [m for m in matches if m.term_type == "direct"]
    semantic = [m for m in matches if m.term_type == "semantic"]

    direct_terms = [m.term for m in direct]
    semantic_terms = [m.term for m in semantic]

    # Quick agentic detection
    agentic_terms = {"agentic", "ai agents", "agent-native"}
    native_terms = {"ai-native", "ai native", "llm-native", "ai-first", "ai first"}

    if any(t in native_terms for t in direct_terms) and len(direct) >= 2:
        return "AI_NATIVE", min(0.95, 0.7 + 0.05 * len(direct)), direct_terms + semantic_terms

    if any(t in agentic_terms for t in direct_terms + semantic_terms):
        return "AGENTIC", 0.85, direct_terms + semantic_terms

    if any(t in native_terms for t in direct_terms):
        return "AI_NATIVE", 0.80, direct_terms + semantic_terms

    vector_terms = {"vector search", "vector database", "embeddings", "semantic search"}
    if any(t in vector_terms for t in semantic_terms) and not direct_terms:
        return "VECTOR_SEARCH_FOCUSED", 0.75, semantic_terms

    if direct_terms or len(semantic_terms) >= SEMANTIC_THRESHOLD:
        return "AI_ENABLED", 0.65 + 0.03 * len(semantic_terms), direct_terms + semantic_terms

    if semantic_terms:
        return "AI_ENABLED", 0.45, semantic_terms

    return "NOT_AI_FOCUSED", 0.90, []


async def classify_with_llm(
    homepage_url: str,
    matches: list[KeywordMatch],
    heuristic_label: str,
    heuristic_confidence: float,
) -> tuple[str, float, str]:
    """
    Returns (label, confidence, reasoning).
    Falls back to heuristic result on LLM error.
    """
    prompt_path = PROMPTS_DIR / "classify_ai.txt"
    template = _load_prompt(prompt_path)

    evidence_lines = "\n".join(
        f"- [{m.term_type}] \"{m.term}\": ...{m.context[:150]}..."
        for m in matches[:15]
    )

    prompt = template.format(
        homepage_url=homepage_url,
        heuristic_label=heuristic_label,
        evidence=evidence_lines or "(no keyword matches found)",
        labels=", ".join(LABELS),
    )

    try:
        result = await call_llm_json(prompt)
        label = result.get("classification", heuristic_label)
        if label not in LABELS:
            label = heuristic_label
        confidence = float(result.get("confidence", heuristic_confidence))
        reasoning = str(result.get("reasoning", ""))
        return label, confidence, reasoning
    except OllamaError as exc:
        logger.warning("LLM classification failed for %s: %s", homepage_url, exc)
        return heuristic_label, heuristic_confidence, ""


def _load_prompt(path: Path) -> str:
    try:
        return path.read_text()
    except FileNotFoundError:
        return _DEFAULT_CLASSIFY_PROMPT


_DEFAULT_CLASSIFY_PROMPT = """\
You are classifying a database vendor's homepage based on extracted keyword evidence.

Homepage: {homepage_url}
Heuristic pre-classification: {heuristic_label}

Evidence found on the page:
{evidence}

Choose ONE label from: {labels}

Respond ONLY with valid JSON, no explanation outside JSON:
{{
  "classification": "<label>",
  "confidence": <0.0-1.0>,
  "reasoning": "<one sentence>"
}}
"""
