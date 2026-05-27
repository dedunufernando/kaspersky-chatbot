"""
Crawls support.kaspersky.com and help.kaspersky.com and saves articles as JSON.
Handles Kaspersky's iframe-based help system.
"""
import asyncio
import json
import re
from pathlib import Path
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup
from playwright.async_api import async_playwright
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

console = Console()
DATA_DIR = Path(__file__).parent.parent / "data" / "raw"
DATA_DIR.mkdir(parents=True, exist_ok=True)

ALLOWED_DOMAINS = {"support.kaspersky.com", "help.kaspersky.com"}
SKIP_PATTERNS = [
    "/forum/", "/community/", "/download/", "/news/",
    ".pdf", ".zip", ".exe", ".msi",
]

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36"
)


def _is_allowed(url: str) -> bool:
    parsed = urlparse(url)
    if parsed.netloc not in ALLOWED_DOMAINS:
        return False
    return not any(p in url for p in SKIP_PATTERNS)


def _extract_metadata(soup: BeautifulSoup, url: str) -> dict:
    title = soup.find("h1") or soup.find("title")
    title_text = title.get_text(strip=True) if title else ""

    applies_to = []
    for tag in soup.find_all(string=re.compile(r"applies to|for product", re.I)):
        parent = tag.parent
        if parent:
            applies_to.append(parent.get_text(" ", strip=True))

    last_modified = ""
    meta = soup.find("meta", attrs={"name": "last-modified"}) or \
           soup.find("meta", attrs={"property": "article:modified_time"})
    if meta:
        last_modified = meta.get("content", "")

    return {
        "url": url,
        "title": title_text,
        "applies_to": applies_to[:5],
        "last_modified": last_modified,
    }


def _extract_content(soup: BeautifulSoup) -> str:
    # Remove noise elements
    for tag in soup.find_all(["nav", "header", "footer", "aside", "script",
                               "style", "noscript", "svg"]):
        tag.decompose()

    # Try to find the main article body
    main = (
        soup.find("article")
        or soup.find(id=re.compile(r"content|main|article|body", re.I))
        or soup.find(class_=re.compile(r"content|article|main|topic", re.I))
        or soup.find("main")
        or soup.body
    )
    if not main:
        return ""

    lines = []
    for elem in main.find_all(["p", "li", "h1", "h2", "h3", "h4", "td", "dt", "dd"]):
        text = elem.get_text(" ", strip=True)
        if text and len(text) > 15:
            lines.append(text)

    return "\n".join(lines)


async def _get_page_content(page, url: str, delay: float) -> str | None:
    """Navigate to URL, handle iframes, return HTML content."""
    try:
        await page.goto(url, wait_until="networkidle", timeout=30000)
        await asyncio.sleep(delay)

        # Check for iframes — Kaspersky help loads content in iframes
        frames = page.frames
        best_html = ""
        best_len = 0

        for frame in frames:
            try:
                html = await frame.content()
                soup = BeautifulSoup(html, "lxml")
                content = _extract_content(soup)
                if len(content) > best_len:
                    best_len = len(content)
                    best_html = html
            except Exception:
                continue

        return best_html if best_len > 0 else await page.content()

    except Exception as e:
        short = str(e).split("\n")[0]
        console.print(f"[red]Skip:[/red] {short[:100]}")
        return None


async def crawl(seed_urls: list[str], max_pages: int, delay: float) -> None:
    visited: set[str] = set()
    queue: list[str] = list(seed_urls)
    saved = 0

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-blink-features=AutomationControlled",
                "--disable-dev-shm-usage",
            ],
        )
        context = await browser.new_context(
            user_agent=USER_AGENT,
            locale="en-US",
            viewport={"width": 1280, "height": 800},
            extra_http_headers={"Accept-Language": "en-US,en;q=0.9"},
        )
        await context.add_init_script(
            "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
        )
        page = await context.new_page()

        with Progress(SpinnerColumn(), TextColumn("{task.description}"), console=console) as progress:
            task = progress.add_task("Crawling...", total=max_pages)

            while queue and saved < max_pages:
                url = queue.pop(0)
                if url in visited or not _is_allowed(url):
                    continue
                visited.add(url)

                console.print(f"[dim]Fetching: {url[:90]}[/dim]")
                html = await _get_page_content(page, url, delay)
                if not html:
                    continue

                soup = BeautifulSoup(html, "lxml")
                content = _extract_content(soup)
                console.print(f"[dim]  → {len(content)} chars extracted[/dim]")

                if len(content) < 150:
                    console.print("[yellow]  Too short, skipping[/yellow]")
                    continue

                meta = _extract_metadata(soup, url)
                # Use the original URL for reference even if content came from iframe
                meta["url"] = url
                article = {**meta, "content": content}

                slug = re.sub(r"[^\w]", "_", urlparse(url).path)[:80]
                out_path = DATA_DIR / f"{slug}.json"
                out_path.write_text(
                    json.dumps(article, ensure_ascii=False, indent=2),
                    encoding="utf-8",
                )
                saved += 1
                progress.advance(task)
                console.print(f"[green]✓ [{saved}][/green] {meta['title'][:70]}")

                # Collect links from all frames
                for frame in page.frames:
                    try:
                        frame_html = await frame.content()
                        frame_soup = BeautifulSoup(frame_html, "lxml")
                        for a in frame_soup.find_all("a", href=True):
                            href = urljoin(url, a["href"]).split("#")[0]
                            if href not in visited and _is_allowed(href):
                                queue.append(href)
                    except Exception:
                        continue

        await context.close()
        await browser.close()

    console.print(f"\n[bold green]Done — {saved} articles saved to {DATA_DIR}[/bold green]")


if __name__ == "__main__":
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from config import KB_SEED_URLS, MAX_PAGES, CRAWL_DELAY

    asyncio.run(crawl(KB_SEED_URLS, MAX_PAGES, CRAWL_DELAY))
