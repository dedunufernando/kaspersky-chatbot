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

# Kaspersky KB seed URLs — section-level pages that link to many real articles
# The crawler follows links, so seeding section/product pages gives 100s of articles.
KB_SEED_URLS = [
    # ── Kaspersky Security Center 14 / 15 ────────────────────────────
    "https://support.kaspersky.com/KSC/14.2/en-US/3438.htm",       # What's new
    "https://support.kaspersky.com/KSC/14.2/en-US/175848.htm",     # Architecture
    "https://support.kaspersky.com/KSC/14.2/en-US/180025.htm",     # Deployment
    "https://support.kaspersky.com/KSC/14.2/en-US/199717.htm",     # Device control
    "https://support.kaspersky.com/KSC/14.2/en-US/158631.htm",     # Network Agent
    "https://support.kaspersky.com/KSC/14.2/en-US/204152.htm",     # Policy config
    "https://support.kaspersky.com/KSC/14.2/en-US/166716.htm",     # Troubleshooting
    "https://support.kaspersky.com/KSC/14.2/en-US/209017.htm",     # KSC Web Console
    "https://support.kaspersky.com/KSC/14.2/en-US/3479.htm",       # Reports & stats
    "https://support.kaspersky.com/KSC/14.2/en-US/189572.htm",     # Update issues

    # ── Kaspersky Endpoint Security 12 for Windows ───────────────────
    "https://support.kaspersky.com/KES12Windows/en-US/127971.htm",  # Main page
    "https://support.kaspersky.com/KES12Windows/en-US/176981.htm",  # Device Control
    "https://support.kaspersky.com/KES12Windows/en-US/131690.htm",  # Firewall
    "https://support.kaspersky.com/KES12Windows/en-US/128893.htm",  # App Control
    "https://support.kaspersky.com/KES12Windows/en-US/134892.htm",  # Encryption
    "https://support.kaspersky.com/KES12Windows/en-US/136947.htm",  # Troubleshoot
    "https://support.kaspersky.com/KES12Windows/en-US/173987.htm",  # Network
    "https://support.kaspersky.com/KES12Windows/en-US/130879.htm",  # Policies

    # ── KES for Linux ────────────────────────────────────────────────
    "https://support.kaspersky.com/KESLinux/12.1/en-US/197912.htm",
    "https://support.kaspersky.com/KESLinux/12.1/en-US/197929.htm",
    "https://support.kaspersky.com/KESLinux/12.1/en-US/197938.htm",

    # ── Kaspersky Standard / Plus / Premium (consumer) ───────────────
    "https://support.kaspersky.com/KAVWin/21.18/en-US/",
    "https://support.kaspersky.com/KSOS/21.18/en-US/",

    # ── Kaspersky VPN ────────────────────────────────────────────────
    "https://support.kaspersky.com/VPN/Win5.x/en-US/",

    # ── Kaspersky Safe Kids ───────────────────────────────────────────
    "https://support.kaspersky.com/SafeKids/2.x/en-US/",

    # ── General support search results (link-rich pages) ─────────────
    "https://support.kaspersky.com/us/search?query=network+agent&lang=en",
    "https://support.kaspersky.com/us/search?query=device+control&lang=en",
    "https://support.kaspersky.com/us/search?query=installation+error&lang=en",
    "https://support.kaspersky.com/us/search?query=update+failed&lang=en",
    "https://support.kaspersky.com/us/search?query=kaspersky+security+center&lang=en",
    "https://support.kaspersky.com/us/search?query=endpoint+security&lang=en",
    "https://support.kaspersky.com/us/search?query=policy+not+applied&lang=en",
    "https://support.kaspersky.com/us/search?query=klmover&lang=en",
    "https://support.kaspersky.com/us/search?query=activation+code&lang=en",
    "https://support.kaspersky.com/us/search?query=license+expired&lang=en",
]
