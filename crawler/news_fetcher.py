"""
Fetches latest Kaspersky news from RSS feeds and saves as KB chunks.
Sources: Kaspersky Blog, Securelist, Google News
"""
import json
import re
import sys
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

import feedparser
import requests
from bs4 import BeautifulSoup
from rich.console import Console

sys.path.insert(0, str(Path(__file__).parent.parent))

console = Console()
DATA_DIR = Path(__file__).parent.parent / "data" / "raw"
DATA_DIR.mkdir(parents=True, exist_ok=True)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    )
}

RSS_FEEDS = [
    {
        "name": "Kaspersky Official Blog",
        "url": "https://www.kaspersky.com/blog/feed/",
        "category": "blog",
    },
    {
        "name": "Securelist – Threat Intelligence",
        "url": "https://securelist.com/feed/",
        "category": "threat_intel",
    },
    {
        "name": "Google News – Kaspersky",
        "url": "https://news.google.com/rss/search?q=kaspersky+security&hl=en-US&gl=US&ceid=US:en",
        "category": "news",
    },
    {
        "name": "Google News – Kaspersky Products",
        "url": "https://news.google.com/rss/search?q=kaspersky+endpoint+security+center&hl=en-US&gl=US&ceid=US:en",
        "category": "news",
    },
]


def _fetch_full_article(url: str) -> str:
    """Fetch and extract full article text from a URL."""
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        if resp.status_code != 200:
            return ""
        soup = BeautifulSoup(resp.text, "lxml")

        # Remove noise
        for tag in soup.find_all(["nav", "header", "footer", "aside",
                                   "script", "style", "noscript"]):
            tag.decompose()

        # Try article body
        main = (
            soup.find("article")
            or soup.find(class_=re.compile(r"post|article|content|entry", re.I))
            or soup.find("main")
            or soup.body
        )
        if not main:
            return ""

        lines = []
        for elem in main.find_all(["p", "li", "h1", "h2", "h3", "h4"]):
            text = elem.get_text(" ", strip=True)
            if text and len(text) > 20:
                lines.append(text)
        return "\n".join(lines)
    except Exception:
        return ""


def fetch_all_news(max_per_feed: int = 30) -> int:
    """Fetch news from all RSS feeds. Returns total articles saved."""
    total = 0

    for feed_info in RSS_FEEDS:
        console.print(f"\n[cyan]📡 Fetching: {feed_info['name']}[/cyan]")
        try:
            feed = feedparser.parse(feed_info["url"])
            entries = feed.entries[:max_per_feed]
            console.print(f"  Found {len(entries)} articles")
        except Exception as e:
            console.print(f"  [red]Failed: {e}[/red]")
            continue

        for entry in entries:
            try:
                url = entry.get("link", "")
                title = entry.get("title", "No title")
                summary = entry.get("summary", "")
                published = entry.get("published", datetime.now().isoformat())

                # Clean summary HTML
                if summary:
                    soup = BeautifulSoup(summary, "lxml")
                    summary = soup.get_text(" ", strip=True)

                # Try to get full article content
                full_content = _fetch_full_article(url) if url else ""
                content = full_content if len(full_content) > len(summary) else summary

                if len(content) < 50:
                    continue

                article = {
                    "url": url,
                    "title": title,
                    "applies_to": [feed_info["category"]],
                    "last_modified": published,
                    "content": f"{title}\n\n{content}",
                    "source": feed_info["name"],
                    "category": feed_info["category"],
                }

                # Save with news_ prefix to distinguish from KB articles
                slug = re.sub(r"[^\w]", "_", urlparse(url).path)[:70]
                out_path = DATA_DIR / f"news_{feed_info['category']}_{slug}.json"
                out_path.write_text(
                    json.dumps(article, ensure_ascii=False, indent=2),
                    encoding="utf-8",
                )
                total += 1
                console.print(f"  [green]✓[/green] {title[:70]}")

            except Exception as e:
                console.print(f"  [yellow]Skip: {e}[/yellow]")
                continue

    console.print(f"\n[bold green]News fetch complete — {total} articles saved.[/bold green]")
    return total


if __name__ == "__main__":
    fetch_all_news()
