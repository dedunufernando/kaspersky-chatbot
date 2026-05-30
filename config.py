from dotenv import load_dotenv
import os

load_dotenv()

GROQ_API_KEY = os.environ["GROQ_API_KEY"]
DATABASE_URL = os.environ["DATABASE_URL"]

# Crawler
CRAWL_DELAY = float(os.getenv("CRAWL_DELAY_SECONDS", "2"))
MAX_PAGES = int(os.getenv("MAX_PAGES", "500"))

# RAG
RETRIEVAL_TOP_K = int(os.getenv("RETRIEVAL_TOP_K", "8"))
CONFIDENCE_THRESHOLD = float(os.getenv("CONFIDENCE_THRESHOLD", "0.25"))

# Models
LLM_MODEL = "deepseek-r1-distill-llama-70b"  # reasoning model — free via Groq
EMBEDDING_MODEL = "all-mpnet-base-v2"
EMBEDDING_DIMENSIONS = 768

# Chunking
CHUNK_SIZE = 400
CHUNK_OVERLAP = 50

# Kaspersky KB seed URLs — consumer + enterprise
KB_SEED_URLS = [
    # ── Kaspersky Security Center KB articles ─────────────────────────
    "https://support.kaspersky.com/KSC/14.2/en-US/3438.htm",
    "https://support.kaspersky.com/KSC/14.2/en-US/175848.htm",
    "https://support.kaspersky.com/KSC/14.2/en-US/180025.htm",
    "https://support.kaspersky.com/KSC/14.2/en-US/199717.htm",
    "https://support.kaspersky.com/KSC/14.2/en-US/158631.htm",

    # ── KES Windows KB articles ───────────────────────────────────────
    "https://support.kaspersky.com/KES12Windows/en-US/127971.htm",
    "https://support.kaspersky.com/KES12Windows/en-US/176981.htm",
    "https://support.kaspersky.com/KES12Windows/en-US/131690.htm",

    # ── General KB articles (work reliably) ───────────────────────────
    "https://support.kaspersky.com/us/13697",
    "https://support.kaspersky.com/us/14459",
    "https://support.kaspersky.com/us/15820",
    "https://support.kaspersky.com/us/15908",
    "https://support.kaspersky.com/us/16025",
    "https://support.kaspersky.com/us/14411",
    "https://support.kaspersky.com/us/13232",
    "https://support.kaspersky.com/us/14448",
    "https://support.kaspersky.com/us/15824",
    "https://support.kaspersky.com/us/13520",
    "https://support.kaspersky.com/us/14612",
    "https://support.kaspersky.com/us/15661",
    "https://support.kaspersky.com/us/13697",
    "https://support.kaspersky.com/us/14556",
    "https://support.kaspersky.com/us/16093",
    "https://support.kaspersky.com/us/14362",
    "https://support.kaspersky.com/us/15887",
    "https://support.kaspersky.com/us/15912",
    "https://support.kaspersky.com/us/16212",
    "https://support.kaspersky.com/us/13741",
    "https://support.kaspersky.com/us/15736",
    "https://support.kaspersky.com/us/14560",
    "https://support.kaspersky.com/us/16111",
    "https://support.kaspersky.com/us/15964",
    "https://support.kaspersky.com/us/16313",

    # ── Consumer product KB ───────────────────────────────────────────
    "https://support.kaspersky.com/us/consumer/17005",
    "https://support.kaspersky.com/us/consumer/16998",
]
