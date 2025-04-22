#!/usr/bin/env python3
"""
Generic single‑level scraper → Markdown

Usage examples
--------------

# Scrape every link on example.com’s home page that stays on the same sub‑domain
uv run grab_posts.py https://example.com

# Scrape the URLs listed in links.txt and ignore the start URL argument
uv run grab_posts.py -f links.txt

# Change output folder and request delay
uv run grab_posts.py https://example.com -o articles_md --delay 0.3
"""
# pip install 'lxml[html_clean]' requests readability-lxml markdownify python-slugify bs4

import argparse
import datetime
import pathlib
import sys
import time
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup
from readability import Document
from slugify import slugify
from markdownify import markdownify as md


###############################################################################
# CLI
###############################################################################


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Scrape a page or a list of URLs, convert each article "
        "to Markdown with YAML front‑matter."
    )
    p.add_argument(
        "start_url",
        nargs="?",
        help="Page whose same‑subdomain links will be scraped "
        "(ignored if --file has URLs).",
    )
    p.add_argument(
        "-f",
        "--file",
        default="urls.txt",
        help="Text file with one URL per line (default: urls.txt). "
        "If the file exists and is non‑empty, its URLs are used instead "
        "of the start URL crawl.",
    )
    p.add_argument(
        "-o",
        "--out",
        default="posts_md",
        help="Output directory for Markdown files (default: posts_md)",
    )
    p.add_argument(
        "--delay",
        type=float,
        default=1.0,
        help="Delay (in seconds) between HTTP requests (default: 1.0)",
    )
    p.add_argument(
        "-a",
        "--author",
        help="Author name to put in the YAML front‑matter (omit to skip the line)",
    )
    return p.parse_args()


###############################################################################
# Helpers
###############################################################################


def extract_date(html: str) -> str:
    """Return publication date YYYY‑MM‑DD if it can be detected, else today."""
    soup = BeautifulSoup(html, "lxml")
    meta = soup.find(
        "meta", {"property": "article:published_time"}
    ) or soup.find("meta", {"name": "date"})
    if meta and meta.get("content"):
        return meta["content"][:10]
    t = soup.find("time", attrs={"datetime": True})
    if t:
        return t["datetime"][:10]
    return datetime.date.today().isoformat()


def collect_urls(start_url: str | None, urls_file: pathlib.Path) -> list[str]:
    """
    1. If *urls_file* exists and is non‑empty → return those URLs.
    2. Otherwise crawl *start_url* once and return every anchor that:
       * resolves to a full URL on the same sub‑domain
       * is not a fragment link
    """
    if urls_file.exists() and urls_file.stat().st_size:
        return [
            u.strip()
            for u in urls_file.read_text().splitlines()
            if u.strip() and not u.strip().startswith("#")
        ]

    if not start_url:
        print("❌ No URLs to scrape. Provide a start_url or a non‑empty file.", file=sys.stderr)
        return []

    parsed_home = urlparse(start_url)
    base = f"{parsed_home.scheme}://{parsed_home.netloc}"

    try:
        html = requests.get(start_url, timeout=30).text
    except Exception as e:
        print(f"❌ Failed to fetch {start_url} – {e}", file=sys.stderr)
        return []

    soup = BeautifulSoup(html, "lxml")
    urls: list[str] = []
    for a in soup.find_all("a", href=True):
        href = urljoin(base, a["href"])
        if urlparse(href).netloc != parsed_home.netloc:
            continue  # skip external
        href = href.split("#")[0].rstrip("/")
        urls.append(href)

    deduped = list(dict.fromkeys(urls))
    print(f"ℹ️  collected {len(deduped)} links from {start_url}", file=sys.stderr)
    return deduped


def make_front_matter(title: str, date: str, source: str, author: str | None) -> str:
    """Return YAML front‑matter as a single string."""
    safe_title = title.replace('"', '\\"')
    lines = [
        "---",
        f'title: "{safe_title}"',
        f"date: {date}",
    ]
    if author:
        lines.append(f"author: {author}")
    lines.append(f"source: {source}")
    lines.append("---")
    lines.append("")  # blank line after front‑matter
    return "\n".join(lines)


###############################################################################
# Main
###############################################################################


def main() -> None:
    args = parse_args()
    output_dir = pathlib.Path(args.out)
    output_dir.mkdir(exist_ok=True)

    urls = collect_urls(args.start_url, pathlib.Path(args.file))
    if not urls:
        return

    for url in urls:
        try:
            html = requests.get(url, timeout=30).text
            doc = Document(html)
            title = doc.short_title() or "untitled"
            body_html = doc.summary()
            date_str = extract_date(html)
            front_matter = make_front_matter(title, date_str, url, args.author)
            md_text = front_matter + md(body_html, strip=["script", "style"])
            slug = slugify(title)
            out_path = output_dir / f"{date_str}-{slug}.md"
            out_path.write_text(md_text, encoding="utf-8")
            print(f"✓ {out_path}")
            time.sleep(args.delay)
        except Exception as e:
            print(f"✗ {url} – {e}", file=sys.stderr)


if __name__ == "__main__":
    main()