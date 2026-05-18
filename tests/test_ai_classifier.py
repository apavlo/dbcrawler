from dbms_vendor_analyzer.analysis.ai_classifier import classify_heuristic
from dbms_vendor_analyzer.analysis.keyword_matcher import find_matches


def _matches(text: str):
    return find_matches(text, "https://vendor.com")


def test_ai_native_label():
    text = "The AI-native database. AI-first platform built for LLM-native workloads."
    label, confidence, _ = classify_heuristic(_matches(text))
    assert label == "AI_NATIVE"
    assert confidence > 0.7


def test_agentic_label():
    text = "The database for AI agents and agentic workflows."
    label, confidence, _ = classify_heuristic(_matches(text))
    assert label == "AGENTIC"


def test_vector_search_label():
    text = "Store and query vector embeddings for semantic search at scale."
    label, _, _ = classify_heuristic(_matches(text))
    assert label in ("VECTOR_SEARCH_FOCUSED", "AI_ENABLED")


def test_not_ai_focused():
    text = "Reliable ACID-compliant relational database with full SQL support."
    label, _, _ = classify_heuristic(_matches(text))
    assert label == "NOT_AI_FOCUSED"


def test_ai_enabled_with_generative_ai():
    text = "Now with generative AI integration and copilot features."
    label, _, _ = classify_heuristic(_matches(text))
    assert label in ("AI_ENABLED", "AI_NATIVE", "AGENTIC")
    assert label != "NOT_AI_FOCUSED"


def test_confidence_range():
    text = "vector search and embeddings."
    _, confidence, _ = classify_heuristic(_matches(text))
    assert 0.0 <= confidence <= 1.0
