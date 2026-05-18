from pathlib import Path

BASE_DIR = Path(__file__).parent.parent

# Crawl limits
MAX_DEPTH = 1
MAX_CONCURRENT_REQUESTS = 10
MIN_TEXT_LENGTH = 1000  # characters; below this triggers Playwright fallback
CONTEXT_WINDOW_SIZE = 250  # chars around a keyword match

# HTTP
REQUEST_TIMEOUT = 30.0  # seconds
MAX_RETRIES = 3

# Blog detection
BLOG_SCORE_THRESHOLD = 15.0
BLOG_SIMILARITY_RATIO = 0.20  # top two candidates within 20% → invoke LLM

# Ollama
OLLAMA_BASE_URL = "http://localhost:11434"
OLLAMA_MODEL = "qwen3"
OLLAMA_TIMEOUT = 60.0

# Paths
SNAPSHOTS_DIR = BASE_DIR / "snapshots"
DATA_DIR = BASE_DIR / "data"
PROMPTS_DIR = BASE_DIR / "prompts"
RESULTS_JSON = DATA_DIR / "results.json"
RESULTS_CSV = DATA_DIR / "results.csv"
INPUT_URLS_FILE = DATA_DIR / "input_urls.txt"

# Keyword lists
DIRECT_TERMS: list[str] = [
    "ai-native",
    "ai native",
    "agentic",
    "llm-native",
    "ai-first",
    "ai first",
    "agent-native",
]

SEMANTIC_TERMS: list[str] = [
    "vector search",
    "vector database",
    "embeddings",
    "rag",
    "retrieval augmented generation",
    "retrieval-augmented generation",
    "generative ai",
    "gen ai",
    "copilot",
    "ai agents",
    "ai applications",
    "semantic search",
    "llm applications",
    "large language model",
    "foundation model",
    "multimodal",
    "natural language query",
    "natural language interface",
]

# Blog scoring weights
BLOG_URL_SCORE: dict[str, float] = {
    "/blog": 10.0,
    "/blogs": 10.0,
    "/news": 7.0,
    "/articles": 7.0,
    "/resources/blog": 9.0,
    "/engineering": 8.0,
    "/updates": 5.0,
    "/insights": 5.0,
    "/posts": 6.0,
}

BLOG_SUBDOMAIN_SCORE: dict[str, float] = {
    "blog": 10.0,
    "engineering": 9.0,
    "news": 7.0,
    "developers": 5.0,
}

BLOG_ANCHOR_KEYWORDS: dict[str, float] = {
    "blog": 8.0,
    "engineering blog": 9.0,
    "news": 6.0,
    "articles": 6.0,
    "updates": 5.0,
    "resources": 4.0,
    "insights": 5.0,
    "posts": 5.0,
    "developer blog": 9.0,
    "tech blog": 8.0,
}

SOCIAL_MEDIA_DOMAINS: set[str] = {
    "twitter.com",
    "x.com",
    "linkedin.com",
    "facebook.com",
    "youtube.com",
    "instagram.com",
    "tiktok.com",
    "medium.com",
    "reddit.com",
    "github.com",
    "slack.com",
    "discord.com",
}
