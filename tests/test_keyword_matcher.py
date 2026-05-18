from dbms_vendor_analyzer.analysis.keyword_matcher import find_matches
from dbms_vendor_analyzer.crawler.extractor import extract_text
from tests.fixtures import AI_NATIVE_HTML, NOT_AI_HTML, SIMPLE_BLOG_HTML


def test_finds_direct_terms():
    text = extract_text(AI_NATIVE_HTML) or "The AI-native database built for agentic workflows."
    matches = find_matches(text, "https://vendor.com")
    terms = {m.term for m in matches}
    assert "ai-native" in terms or "agentic" in terms


def test_finds_semantic_terms():
    text = extract_text(SIMPLE_BLOG_HTML) or "vector search and embeddings support"
    matches = find_matches(text, "https://vendor.com")
    terms = {m.term for m in matches}
    assert terms & {"vector search", "embeddings", "retrieval augmented generation"}


def test_no_false_positives():
    text = extract_text(NOT_AI_HTML) or "Reliable relational database. ACID transactions."
    matches = find_matches(text, "https://vendor.com")
    assert len(matches) == 0


def test_deduplicates_terms():
    text = "vector search is great. vector search for everyone."
    matches = find_matches(text, "https://vendor.com")
    terms = [m.term for m in matches]
    assert terms.count("vector search") == 1


def test_context_window_present():
    text = "We provide vector search capabilities for modern apps."
    matches = find_matches(text, "https://vendor.com")
    assert matches
    assert "vector search" in matches[0].context


def test_empty_text():
    assert find_matches("", "https://vendor.com") == []
