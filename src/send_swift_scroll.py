# send_swift_scroll.py
# Full pipeline: collect data -> compose Swift Scroll -> send email.

from collector_reddit import collect_reddit_snippets, load_config
from collector_youtube import collect_youtube_snippets
from collector_site import collect_official_site_snippets
from collector_tumblr import collect_tumblr_snippets
from composer import compose_email_from_data
from gmail_sender import send_swift_scroll_via_gmail



def split_subject_and_body(full_text: str):
    """
    Given the full email text (including a 'Subject: ...' line at the top),
    split it into (subject, body).
    If no explicit Subject line found, use a default.
    """
    lines = full_text.strip().splitlines()
    subject = "✨ Your Weekly Swift Scroll ✨"
    body_lines = []

    for i, line in enumerate(lines):
        if line.lower().startswith("subject:"):
            # Remove 'Subject:' and strip
            subject = line.split(":", 1)[1].strip()
            # Body is everything after this line
            body_lines = lines[i + 1 :]
            break
    else:
        # No Subject: line found; whole thing is body
        body_lines = lines

    body = "\n".join(body_lines).strip()
    return subject, body


def build_fandom_data() -> str:
    """
    Collect data from all sources and combine into one big text block.
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

    combined_parts = []

    if reddit_data.strip():
        combined_parts.append("=== REDDIT SNIPPETS ===\n" + reddit_data)

    if youtube_data.strip():
        combined_parts.append("=== YOUTUBE SNIPPETS ===\n" + youtube_data)

    if official_data.strip():
        combined_parts.append("=== OFFICIAL SITE SNIPPETS ===\n" + official_data)

    if tumblr_data.strip():
        combined_parts.append("=== TUMBLR SNIPPETS ===\n" + tumblr_data)

    combined = "\n\n".join(combined_parts)

    if not combined.strip():
        raise ValueError("No fandom data collected from any source.")

    return combined


if __name__ == "__main__":
    print("Building fandom data blob...")
    fandom_data = build_fandom_data()

    print("Calling OpenAI to compose Swift Scroll email...")
    full_email_text = compose_email_from_data(fandom_data)

    # Split subject + body
    subject, body = split_subject_and_body(full_email_text)

    print("\n\n====== SWIFT SCROLL EMAIL TO BE SENT ======\n")
    print("SUBJECT:", subject)
    print("\n" + body)
    print("\n====== END OF EMAIL ======\n")

    print("Sending email via Gmail API...")
send_swift_scroll_via_gmail(subject, body)
print("Email sent via Gmail API!")

