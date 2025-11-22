# composer.py
# Turns raw fandom data into a Swift Scroll email using OpenAI.

import os
import json
from dotenv import load_dotenv
from openai import OpenAI

from collector_reddit import collect_reddit_snippets, load_config
from collector_youtube import collect_youtube_snippets
from collector_site import collect_official_site_snippets
from collector_tumblr import collect_tumblr_snippets


def get_openai_client() -> OpenAI:
    """
    Create an OpenAI client using the API key from .env.
    """
    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY is missing in .env")
    client = OpenAI(api_key=api_key)
    return client


def load_text_file(path: str) -> str:
    """
    Read and return contents of a text file.
    """
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def compose_email_from_data(fandom_data: str) -> str:
    """
    Use OpenAI to turn raw fandom data into a Swift Scroll email body.
    """
    system_prompt = load_text_file("prompt_system.txt")
    user_template = load_text_file("prompt_user_template.txt")

    user_content = f"""{user_template}

=== START DATA ===
{fandom_data}
=== END DATA ===
"""

    client = get_openai_client()

    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content},
        ],
        temperature=0.8,
        max_tokens=1200,
    )

    message = response.choices[0].message.content
    return message.strip()


if __name__ == "__main__":
    """
    Test script:
    - Load config
    - Collect Reddit + YouTube + Official site + Tumblr data
    - Ask OpenAI to write a Swift Scroll email
    - Print the email to the terminal
    """
    print("Loading config...")
    config = load_config()
    subreddits = config.get("subreddits", [])
    max_posts = config.get("max_reddit_posts", 30)

    print("Collecting Reddit data...")
    reddit_data = collect_reddit_snippets(
        subreddits=subreddits,
        max_posts=max_posts,
        max_comments_per_post=3,
    )

    print("Collecting YouTube data...")
    youtube_data = collect_youtube_snippets()

    print("Collecting official site data...")
    official_data = collect_official_site_snippets()

    print("Collecting Tumblr data...")
    tumblr_data = collect_tumblr_snippets()

    # Combine all sources into one big fandom blob
    combined_parts = []

    if reddit_data.strip():
        combined_parts.append("=== REDDIT SNIPPETS ===\n" + reddit_data)

    if youtube_data.strip():
        combined_parts.append("=== YOUTUBE SNIPPETS ===\n" + youtube_data)

    if official_data.strip():
        combined_parts.append("=== OFFICIAL SITE SNIPPETS ===\n" + official_data)

    if tumblr_data.strip():
        combined_parts.append("=== TUMBLR SNIPPETS ===\n" + tumblr_data)

    combined_data = "\n\n".join(combined_parts)

    if not combined_data.strip():
        print("No fandom data collected. Check all source settings/credentials.")
        exit(1)

    print("Calling OpenAI to compose Swift Scroll email...")
    email_body = compose_email_from_data(combined_data)

    print("\n\n====== SWIFT SCROLL EMAIL DRAFT ======\n")
    print(email_body)
    print("\n====== END OF EMAIL ======\n")

