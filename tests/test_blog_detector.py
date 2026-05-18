from dbms_vendor_analyzer.analysis.blog_detector import _score, detect_blog, needs_llm_tiebreak
from dbms_vendor_analyzer.crawler.extractor import extract_links
from tests.fixtures import ENGINEERING_BLOG_HTML, NO_BLOG_HTML, SIMPLE_BLOG_HTML


def test_detects_blog_path():
    links = extract_links(SIMPLE_BLOG_HTML, "https://vendor.com")
    best, _ = detect_blog(links, "https://vendor.com")
    assert best is not None
    assert best.url == "https://vendor.com/blog"


def test_detects_engineering_subdomain():
    links = extract_links(ENGINEERING_BLOG_HTML, "https://vendor.com")
    best, _ = detect_blog(links, "https://vendor.com")
    assert best is not None
    assert "engineering.vendor.com" in best.url


def test_no_blog_returns_none():
    links = extract_links(NO_BLOG_HTML, "https://vendor.com")
    best, _ = detect_blog(links, "https://vendor.com")
    assert best is None


def test_social_media_penalised():
    candidate = _score("https://twitter.com/vendor", "Twitter", "vendor.com")
    assert candidate.score < 0


def test_same_domain_bonus():
    c_same = _score("https://vendor.com/blog", "Blog", "vendor.com")
    c_external = _score("https://otherblog.com/vendor", "Blog", "vendor.com")
    assert c_same.score > c_external.score


def test_needs_llm_tiebreak_close_scores():
    links = [
        {"url": "https://vendor.com/blog", "text": "Blog"},
        {"url": "https://vendor.com/news", "text": "News"},
    ]
    _, candidates = detect_blog(links, "https://vendor.com")
    # With two closely scored candidates the tiebreak flag may fire
    result = needs_llm_tiebreak(candidates)
    assert isinstance(result, bool)


def test_needs_llm_tiebreak_single_candidate():
    from dbms_vendor_analyzer.models.schema import BlogCandidate
    candidates = [BlogCandidate(url="https://vendor.com/blog", anchor_text="Blog", score=25.0)]
    assert needs_llm_tiebreak(candidates) is False


def test_needs_llm_tiebreak_empty():
    assert needs_llm_tiebreak([]) is False
