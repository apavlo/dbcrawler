from dbms_vendor_analyzer.crawler.extractor import extract_links, extract_text
from tests.fixtures import SIMPLE_BLOG_HTML


def test_extract_links_absolute():
    links = extract_links(SIMPLE_BLOG_HTML, "https://vendor.com")
    urls = [lnk["url"] for lnk in links]
    assert "https://vendor.com/blog" in urls
    assert "https://vendor.com/docs" in urls


def test_extract_links_filters_anchors():
    html = '<html><body><a href="#top">Top</a><a href="/page">Page</a></body></html>'
    links = extract_links(html, "https://vendor.com")
    urls = [lnk["url"] for lnk in links]
    assert "https://vendor.com/page" in urls
    assert not any("#top" in u for u in urls)


def test_extract_links_deduplicates():
    html = '<html><body><a href="/blog">Blog</a><a href="/blog">Blog again</a></body></html>'
    links = extract_links(html, "https://vendor.com")
    blog_links = [lnk for lnk in links if lnk["url"] == "https://vendor.com/blog"]
    assert len(blog_links) == 1


def test_extract_links_skips_social():
    links = extract_links(SIMPLE_BLOG_HTML, "https://vendor.com")
    urls = [lnk["url"] for lnk in links]
    # Social links are still extracted (filtering is blog_detector's job)
    assert any("twitter.com" in u for u in urls)


def test_extract_text_returns_string():
    text = extract_text(SIMPLE_BLOG_HTML)
    assert isinstance(text, str)


def test_extract_text_empty_html():
    assert extract_text("") == ""


def test_extract_text_contains_content():
    text = extract_text(SIMPLE_BLOG_HTML)
    assert "AI" in text or "vector" in text or "embeddings" in text
