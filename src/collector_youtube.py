# collector_youtube.py
# Collects recent Taylor Swift fandom data from YouTube.

import os
import json
from typing import List
from dotenv import load_dotenv
import requests

from collector_reddit import load_config  # reuse the same config loader


def get_youtube_api_key() -> str:
    """
    Load YOUTUBE_API_KEY from .env.
    """
    load_dotenv()
    api_key = os.getenv("YOUTUBE_API_KEY")
    if not api_key:
        raise ValueError("YOUTUBE_API_KEY is missing in .env")
    return api_key


def fetch_channel_videos(api_key: str, channel_id: str, max_results: int = 5) -> List[dict]:
    """
    Fetch the most recent videos from a YouTube channel.
    Returns a list of search result items with videoId and snippet.
    """
    url = "https://www.googleapis.com/youtube/v3/search"
    params = {
        "key": api_key,
        "channelId": channel_id,
        "part": "snippet",
        "order": "date",
        "maxResults": max_results,
        "type": "video",
    }

    resp = requests.get(url, params=params, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    return data.get("items", [])


def fetch_video_comments(api_key: str, video_id: str, max_results: int = 5) -> List[str]:
    """
    Fetch top-level comments for a given video.
    Returns a list of comment text strings.
    """
    url = "https://www.googleapis.com/youtube/v3/commentThreads"
    params = {
        "key": api_key,
        "videoId": video_id,
        "part": "snippet",
        "maxResults": max_results,
        "order": "relevance",
        "textFormat": "plainText",
    }

    resp = requests.get(url, params=params, timeout=30)
    # Some videos may have comments disabled or restricted; handle errors gracefully.
    if resp.status_code != 200:
        return []

    data = resp.json()
    comments: List[str] = []

    for item in data.get("items", []):
        snippet = item.get("snippet", {})
        top = snippet.get("topLevelComment", {})
        top_snip = top.get("snippet", {})
        text = (top_snip.get("textDisplay") or "").strip()
        if text:
            if len(text) > 400:
                text = text[:400] + "..."
            comments.append(text)

    return comments


def collect_youtube_snippets() -> str:
    """
    Collect recent YouTube video titles, descriptions, and top comments
    from Taylor's official channel as specified in config.json.
    Returns one big text string suitable for feeding into the LLM.
    """
    config = load_config()
    api_key = get_youtube_api_key()

    channel_id = config.get("youtube_channel_id")
    if not channel_id:
        return ""

    max_videos = config.get("max_youtube_videos", 5)
    max_comments = config.get("max_comments_per_source", 10)

    items = fetch_channel_videos(api_key, channel_id, max_results=max_videos)

    snippets: List[str] = []

    for item in items:
        snippet = item.get("snippet", {})
        video_id = item.get("id", {}).get("videoId")
        if not video_id:
            continue

        title = snippet.get("title", "").strip()
        description = (snippet.get("description", "") or "").strip()
        if len(description) > 500:
            description = description[:500] + "..."

        snippets.append(f"[YOUTUBE VIDEO] {title}\n{description}")

        comments = fetch_video_comments(api_key, video_id, max_results=max_comments)
        for c in comments:
            snippets.append(f"[YOUTUBE COMMENT] {c}")

    return "\n\n".join(snippets)


if __name__ == "__main__":
    """
    Test script:
    - Load config
    - Collect YouTube snippets
    - Print them wrapped in START/END markers
    """
    print("Collecting YouTube data...")
    try:
        data = collect_youtube_snippets()
    except Exception as e:
        print(f"Error while collecting YouTube data: {e}")
        raise

    print("=== START YOUTUBE DATA ===")
    print(data)
    print("=== END YOUTUBE DATA ===")
