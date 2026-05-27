from dotenv import load_dotenv
import os

load_dotenv()

GROQ_API_KEY = os.environ["GROQ_API_KEY"]
DATABASE_URL = os.environ["DATABASE_URL"]

# Crawler
CRAWL_DELAY = float(os.getenv("CRAWL_DELAY_SECONDS", "2"))
MAX_PAGES = int(os.getenv("MAX_PAGES", "200"))

# RAG
RETRIEVAL_TOP_K = int(os.getenv("RETRIEVAL_TOP_K", "5"))
CONFIDENCE_THRESHOLD = float(os.getenv("CONFIDENCE_THRESHOLD", "0.75"))

# Models
LLM_MODEL = "llama-3.3-70b-versatile"   # free via Groq
EMBEDDING_MODEL = "all-mpnet-base-v2"   # free local model via sentence-transformers
EMBEDDING_DIMENSIONS = 768

# Chunking
CHUNK_SIZE = 400        # tokens
CHUNK_OVERLAP = 50      # tokens

# Kaspersky base URLs to crawl
KB_SEED_URLS = [
    # Direct help.kaspersky.com articles (bypasses iframe shell)
    "https://help.kaspersky.com/KasperskyStandardPlusPremium/en-US/195909.htm",
    "https://help.kaspersky.com/KasperskyStandardPlusPremium/en-US/196283.htm",
    "https://help.kaspersky.com/KasperskyStandardPlusPremium/en-US/198643.htm",
    # Endpoint Security
    "https://help.kaspersky.com/KES12/en-US/176981.htm",
    "https://help.kaspersky.com/KES12/en-US/127971.htm",
    # VPN
    "https://help.kaspersky.com/VPN/Win/en-US/what-is-kaspersky-vpn.htm",
    # Mobile
    "https://help.kaspersky.com/KSAndroid/en-US/153139.htm",
    # KB articles on support.kaspersky.com
    "https://support.kaspersky.com/us/14459",
    "https://support.kaspersky.com/us/13697",
    "https://support.kaspersky.com/us/15820",
]
