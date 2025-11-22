# collector_site.py
# Collects recent Taylor Swift official site snippets.

import json
from typing import List
import requests
from bs4 import BeautifulSoup

from collector_reddit import load_config  # reuse existing function


def fetch_page(url: str) -> str:
    """
    Fetch a page and return its HTML text.
    """
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()
    return resp.text


def extract_snippets_from_html(html: str, label: str) -> List[str]:
    """
    Extract headings and paragraphs from HTML and turn them into short text snippets.
    """
    soup = BeautifulSoup(html, "html.parser")
    snippets: List[str] = []

    # Grab headings
    for tag in soup.find_all(["h1", "h2", "h3"]):
        text = (tag.get_text(separator=" ", strip=True) or "").strip()
        if text and len(text) > 5:
            if len(text) > 200:
                text = text[:200] + "..."
            snippets.append(f"[{label} HEADING] {text}")

    # Grab paragraphs
    for p in soup.find_all("p"):
        text = (p.get_text(separator=" ", strip=True) or "").strip()
        if not text or len(text) < 40:
            continue  # skip super tiny stuff
        if len(text) > 400:
            text = text[:400] + "..."
        snippets.append(f"[{label} TEXT] {text}")

        # avoid going infinite
        if len(snippets) > 40:
            break

    return snippets


def collect_official_site_snippets() -> str:
    """
    Collect snippets from Taylor's official website and The Life of a Showgirl page.
    Returns one big text block.
    """
    config = load_config()
    taylor_site = config.get("taylor_official_site")
    showgirl_site = config.get("showgirl_site")

    all_snippets: List[str] = []

    if taylor_site:
        try:
            html = fetch_page(taylor_site)
            all_snippets.extend(extract_snippets_from_html(html, "OFFICIAL SITE"))
        except Exception as e:
            all_snippets.append(f"[OFFICIAL SITE ERROR] Could not fetch {taylor_site}: {e}")

    if showgirl_site:
        try:
            html = fetch_page(showgirl_site)
            all_snippets.extend(extract_snippets_from_html(html, "SHOWGIRL"))
        except Exception as e:
            all_snippets.append(f"[SHOWGIRL ERROR] Could not fetch {showgirl_site}: {e}")

    return "\n\n".join(all_snippets)


if __name__ == "__main__":
    """
    Test script:
    - Collect official site snippets
    - Print them wrapped in markers
    """
    print("Collecting official site data...")
    data = collect_official_site_snippets()
    print("=== START OFFICIAL SITE DATA ===")
    print(data)
    print("=== END OFFICIAL SITE DATA ===")
