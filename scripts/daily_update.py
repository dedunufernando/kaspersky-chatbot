"""
Daily update script — runs crawler + news fetcher + re-ingests everything.
Run manually: python scripts/daily_update.py
Scheduled:    runs automatically via Windows Task Scheduler
"""
import sys
import subprocess
from pathlib import Path
from datetime import datetime
from rich.console import Console

sys.path.insert(0, str(Path(__file__).parent.parent))

console = Console()
ROOT = Path(__file__).parent.parent
LOG_FILE = ROOT / "data" / "update_log.txt"
LOG_FILE.parent.mkdir(parents=True, exist_ok=True)


def log(msg: str):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{timestamp}] {msg}"
    console.print(line)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def run(script: str, *args):
    cmd = [sys.executable, str(ROOT / script)] + list(args)
    log(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=str(ROOT))
    if result.returncode != 0:
        log(f"WARNING: {script} exited with code {result.returncode}")
    return result.returncode == 0


def main():
    log("=" * 60)
    log("Daily Kaspersky KB Update Started")
    log("=" * 60)

    # Step 1 — Crawl KB articles
    log("Step 1/3: Crawling Kaspersky support & help pages...")
    run("crawler/kaspersky_crawler.py")

    # Step 2 — Fetch latest news
    log("Step 2/3: Fetching latest news from RSS feeds...")
    try:
        from crawler.news_fetcher import fetch_all_news
        count = fetch_all_news(max_per_feed=20)
        log(f"  News fetched: {count} articles")
    except Exception as e:
        log(f"  News fetch error: {e}")

    # Step 3 — Re-ingest everything into the vector DB
    log("Step 3/3: Re-embedding and updating database...")
    run("rag/ingest.py", "--force")

    log("Daily update COMPLETE!")
    log("=" * 60)


if __name__ == "__main__":
    main()
