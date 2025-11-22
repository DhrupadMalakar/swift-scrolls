# collector_tumblr.py
# Collects aesthetic / text snippets from Taylor's Tumblr.

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
    Extract headings and paragraphs from Tumblr HTML and turn them into short text snippets.
    We keep it simple: grab text-y bits that look like posts or captions.
    """
    soup = BeautifulSoup(html, "html.parser")
    snippets: List[str] = []

    # Many Tumblr themes use article/post containers, but we still fall back to paragraphs.
    post_containers = soup.find_all(["article", "section", "div"], class_=lambda c: c and "post" in c.lower()) or []

    # First, try post containers if found
    for post in post_containers:
        text = (post.get_text(separator=" ", strip=True) or "").strip()
        if not text or len(text) < 40:
            continue
        if len(text) > 500:
            text = text[:500] + "..."
        snippets.append(f"[{label} POST] {text}")
        if len(snippets) > 30:
            break

    # If we didn't find enough via post containers, fall back to generic paragraphs
    if len(snippets) < 10:
        for p in soup.find_all("p"):
            text = (p.get_text(separator=" ", strip=True) or "").strip()
            if not text or len(text) < 40:
                continue
            if len(text) > 400:
                text = text[:400] + "..."
            snippets.append(f"[{label} TEXT] {text}")
            if len(snippets) > 30:
                break

    return snippets


def collect_tumblr_snippets() -> str:
    """
    Collect snippets from Taylor's Tumblr as configured in config.json.
    Returns one big text block.
    """
    config = load_config()
    tumblr_url = config.get("tumblr_url")

    if not tumblr_url:
        return ""

    all_snippets: List[str] = []

    try:
        html = fetch_page(tumblr_url)
        all_snippets.extend(extract_snippets_from_html(html, "TUMBLR"))
    except Exception as e:
        all_snippets.append(f"[TUMBLR ERROR] Could not fetch {tumblr_url}: {e}")

    return "\n\n".join(all_snippets)


if __name__ == "__main__":
    """
    Test script:
    - Collect Tumblr snippets
    - Print them wrapped in markers
    """
    print("Collecting Tumblr data...")
    data = collect_tumblr_snippets()
    print("=== START TUMBLR DATA ===")
    print(data)
    print("=== END TUMBLR DATA ===")
