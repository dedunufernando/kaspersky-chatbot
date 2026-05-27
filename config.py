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
    # ── Kaspersky Security Center (KSC) ──────────────────────────────
    "https://help.kaspersky.com/KSC/14.2/en-US/3438.htm",
    "https://help.kaspersky.com/KSC/14.2/en-US/175848.htm",
    "https://help.kaspersky.com/KSC/14.2/en-US/180025.htm",
    "https://help.kaspersky.com/KSC/14.2/en-US/198653.htm",
    "https://help.kaspersky.com/KSC/14.2/en-US/199717.htm",

    # ── KES for Windows 12 ───────────────────────────────────────────
    "https://help.kaspersky.com/KES12/en-US/176981.htm",
    "https://help.kaspersky.com/KES12/en-US/127971.htm",
    "https://help.kaspersky.com/KES12/en-US/176997.htm",
    "https://help.kaspersky.com/KES12/en-US/131690.htm",
    "https://help.kaspersky.com/KES12/en-US/176998.htm",

    # ── KES for Linux ────────────────────────────────────────────────
    "https://help.kaspersky.com/KES4Linux/12/en-US/197739.htm",
    "https://help.kaspersky.com/KES4Linux/12/en-US/197745.htm",
    "https://help.kaspersky.com/KES4Linux/12/en-US/206503.htm",
    "https://help.kaspersky.com/KES4Linux/12/en-US/199285.htm",

    # ── Network Agent ────────────────────────────────────────────────
    "https://help.kaspersky.com/KSC/14.2/en-US/158631.htm",
    "https://help.kaspersky.com/KSC/14.2/en-US/158634.htm",

    # ── Device Control / USB Block ───────────────────────────────────
    "https://help.kaspersky.com/KES12/en-US/131690.htm",
    "https://help.kaspersky.com/KES4Linux/12/en-US/199289.htm",

    # ── Consumer products ────────────────────────────────────────────
    "https://help.kaspersky.com/KasperskyStandardPlusPremium/en-US/195909.htm",
    "https://help.kaspersky.com/KasperskyStandardPlusPremium/en-US/196283.htm",
    "https://help.kaspersky.com/VPN/Win/en-US/what-is-kaspersky-vpn.htm",
    "https://help.kaspersky.com/KSAndroid/en-US/153139.htm",

    # ── KB / support articles ────────────────────────────────────────
    "https://support.kaspersky.com/us/14459",
    "https://support.kaspersky.com/us/13697",
    "https://support.kaspersky.com/us/15820",
    "https://support.kaspersky.com/KSC/14.2/en-US/",
]
