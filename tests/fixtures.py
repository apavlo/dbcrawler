"""Static HTML fixtures for tests — no live network calls."""

SIMPLE_BLOG_HTML = """
<html><body>
  <nav>
    <a href="/blog">Blog</a>
    <a href="/docs">Docs</a>
    <a href="https://twitter.com/vendor">Twitter</a>
    <a href="https://linkedin.com/company/vendor">LinkedIn</a>
  </nav>
  <main>
    <h1>The fastest database for your AI applications</h1>
    <p>Build AI-native apps with our vector search and embeddings support.</p>
    <p>Use retrieval augmented generation and semantic search out of the box.</p>
  </main>
</body></html>
"""

ENGINEERING_BLOG_HTML = """
<html><body>
  <nav>
    <a href="https://engineering.vendor.com">Engineering Blog</a>
    <a href="/about">About</a>
  </nav>
  <main><p>A traditional relational database.</p></main>
</body></html>
"""

NO_BLOG_HTML = """
<html><body>
  <nav>
    <a href="/pricing">Pricing</a>
    <a href="/docs">Documentation</a>
    <a href="https://twitter.com/vendor">Twitter</a>
  </nav>
  <main><p>A simple key-value store with no AI focus.</p></main>
</body></html>
"""

AI_NATIVE_HTML = """
<html><body>
  <main>
    <h1>The AI-native database</h1>
    <p>We are AI-first and LLM-native, built for agentic workflows.</p>
    <p>Vector search, embeddings, and generative AI infrastructure.</p>
    <a href="/blog">Blog</a>
  </main>
</body></html>
"""

NOT_AI_HTML = """
<html><body>
  <main>
    <h1>Reliable relational database</h1>
    <p>ACID transactions, full SQL support, high availability.</p>
    <a href="/blog">Blog</a>
  </main>
</body></html>
"""
