# collector_reddit.py
# This file collects recent Taylor Swift fandom data from Reddit.

import os
import json
from typing import List
from dotenv import load_dotenv
import praw


def load_config() -> dict:
    """
    Load settings from config.json (subreddits, limits, etc.).
    """
    with open("config.json", "r") as f:
        return json.load(f)


def get_reddit_client() -> praw.Reddit:
    """
    Create and return a Reddit API client using credentials from .env.
    """
    load_dotenv()  # load REDDIT_CLIENT_ID, etc. from .env

    client_id = os.getenv("REDDIT_CLIENT_ID")
    client_secret = os.getenv("REDDIT_CLIENT_SECRET")
    username = os.getenv("REDDIT_USERNAME")
    password = os.getenv("REDDIT_PASSWORD")

    if not all([client_id, client_secret, username, password]):
        raise ValueError("Missing one or more Reddit credentials in .env")

    reddit = praw.Reddit(
        client_id=client_id,
        client_secret=client_secret,
        username=username,
        password=password,
        user_agent="swift_scrolls_reddit_collector by u/{}".format(username),
    )
    return reddit


def collect_reddit_snippets(
    subreddits: List[str],
    max_posts: int = 30,
    max_comments_per_post: int = 3,
) -> str:
    """
    Collect posts and a few top-level comments from the given subreddits.
    Returns one big text string with all snippets, ready to feed the LLM.
    """
    reddit = get_reddit_client()
    snippets: List[str] = []

    if not subreddits:
        return ""

    # simple split of limit across subs
    posts_per_sub = max(1, max_posts // len(subreddits))

    for sub in subreddits:
        subreddit = reddit.subreddit(sub)

        # use "top this week" as a proxy for what mattered
        for post in subreddit.top(time_filter="week", limit=posts_per_sub):
            # Post title + first part of self-text
            post_text = (post.selftext or "").strip()
            if len(post_text) > 400:
                post_text = post_text[:400] + "..."

            snippets.append(
                f"[POST in r/{sub}] {post.title}\n{post_text}"
            )

            # Load a few top-level comments
            post.comments.replace_more(limit=0)
            for i, comment in enumerate(post.comments):
                if i >= max_comments_per_post:
                    break
                comment_body = (comment.body or "").strip()
                if len(comment_body) > 400:
                    comment_body = comment_body[:400] + "..."
                snippets.append(
                    f"[COMMENT in r/{sub}] {comment_body}"
                )

    # Join everything into one big text block
    return "\n\n".join(snippets)


if __name__ == "__main__":
    """
    If you run this file directly, it will:
    - Load config.json
    - Collect Reddit data
    - Print it wrapped in START/END markers
    This is to test that Reddit collection works before wiring the full agent.
    """
    config = load_config()
    subreddits = config.get("subreddits", [])
    max_posts = config.get("max_reddit_posts", 30)

    print("Collecting Reddit data...")
    data = collect_reddit_snippets(subreddits=subreddits, max_posts=max_posts)

    print("=== START DATA ===")
    print(data)
    print("=== END DATA ===")
