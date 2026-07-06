#!/usr/bin/env python3
"""
Afghan Security Weekly Digest Generator
-----------------------------------------
Pulls a set of RSS feeds, filters entries down to the last 7 days that match
Afghan-security keywords, optionally summarizes each with the Claude API,
and renders a static HTML page (index.html) suitable for GitHub Pages or
any static host.

Run manually:
    pip install feedparser requests beautifulsoup4 anthropic python-dateutil --break-system-packages
    export ANTHROPIC_API_KEY=sk-...        # optional, enables AI summaries
    python generate_digest.py

In CI (see .github/workflows/weekly-digest.yml) this runs every Monday
07:00 GMT and commits the regenerated index.html.
"""

import os
import re
import json
import html
import time
from datetime import datetime, timedelta, timezone

import feedparser
import requests
from bs4 import BeautifulSoup
from dateutil import parser as dateparser

# Many sites (Cloudflare etc.) block requests with no/odd User-Agent, including
# feedparser's default one. A normal browser-like UA fixes most of these.
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    )
}
REQUEST_TIMEOUT = 15

# --------------------------------------------------------------------------
# 1. CONFIG — edit this list as your source list evolves (see sources.md)
# --------------------------------------------------------------------------

FEEDS = [
    {"name": "Khaama Press", "url": "https://www.khaama.com/feed/"},
    {"name": "Pajhwok Afghan News", "url": "https://pajhwok.com/feed/"},
    {"name": "Ariana News", "url": "https://ariananews.af/feed/"},
    {"name": "Long War Journal", "url": "https://www.longwarjournal.org/feed"},
    {"name": "International Crisis Group - Asia", "url": "https://www.crisisgroup.org/rss/asia.xml"},
    {"name": "RFE/RL Gandhara", "url": "https://gandhara.rferl.org/api/zrqiteuuir"},
    # Add more from sources.md as you confirm working feed URLs.
]

KEYWORDS = [
    "taliban", "iskp", "isis-k", "islamic state khorasan", "al-qaeda", "al qaeda",
    "ttp", "tehrik-i-taliban", "tehrik-e-taliban", "nrf", "national resistance front",
    "haqqani", "suicide bomb", "airstrike", "air strike", "insurgency", "insurgent",
    "border clash", "durand line", "panjshir", "terroris", "militant",
    "security force", "unama", "sanctions", "kunar", "kandahar security",
    "extremist", "jihadist", "attack", "explosion", "military",
]

DAYS_LOOKBACK = 7
OUTPUT_FILE = "index.html"
SITE_TITLE = "Afghan Security Weekly"

# --------------------------------------------------------------------------
# 2a. "NO CLEAN RSS" SOURCES — exiled Afghan outlets that keep minimal sites
# for safety reasons. Most turn out to run WordPress under the hood, so we
# try their /feed endpoint first and only fall back to scraping the article
# listing page if that fails or returns nothing.
# --------------------------------------------------------------------------

SCRAPE_SOURCES = [
    {
        "name": "8AM Media (Hasht-e Subh)",
        "feed_url": "https://8am.media/eng/feed",
        "listing_url": "https://8am.media/eng/category/afghanistan-news/",
        "base_url": "https://8am.media",
    },
    {
        "name": "KabulNow (Etilaatroz English)",
        "feed_url": "https://kabulnow.com/feed",
        "listing_url": "https://kabulnow.com/category/news/",
        "base_url": "https://kabulnow.com",
    },
    {
        "name": "Rukhshana Media",
        "feed_url": "https://rukhshana.com/en/feed",
        "listing_url": "https://rukhshana.com/en/",
        "base_url": "https://rukhshana.com",
    },
    {
        "name": "Zan Times",
        "feed_url": "https://zantimes.com/feed",
        "listing_url": "https://zantimes.com/",
        "base_url": "https://zantimes.com",
    },
    {
        "name": "Afghanistan Analysts Network",
        "feed_url": "https://www.afghanistan-analysts.org/en/feed/",
        "listing_url": "https://www.afghanistan-analysts.org/en/",
        "base_url": "https://www.afghanistan-analysts.org",
    },
]


# --------------------------------------------------------------------------
# 2b. FETCH + FILTER — standard RSS feeds
# --------------------------------------------------------------------------

def matches_keywords(text: str) -> bool:
    text = text.lower()
    return any(kw in text for kw in KEYWORDS)


def parse_pub_date(published):
    try:
        pub_dt = dateparser.parse(published) if published else None
        if pub_dt and pub_dt.tzinfo is None:
            pub_dt = pub_dt.replace(tzinfo=timezone.utc)
        return pub_dt
    except Exception:
        return None


def fetch_feed_entries(name, url, cutoff):
    """Fetch and filter one RSS/Atom feed. Returns a list of entry dicts,
    and a bool for whether the fetch itself succeeded (so callers can decide
    whether to fall back to scraping)."""
    try:
        raw = requests.get(url, headers=HEADERS, timeout=REQUEST_TIMEOUT)
        raw.raise_for_status()
        parsed = feedparser.parse(raw.content)
    except Exception as e:
        print(f"[warn] feed fetch failed for {name} ({url}): {e}")
        return [], False

    if not parsed.entries:
        return [], False

    results = []
    for entry in parsed.entries:
        published = entry.get("published") or entry.get("updated")
        pub_dt = parse_pub_date(published)

        if pub_dt and pub_dt < cutoff:
            continue

        title = entry.get("title", "").strip()
        summary = re.sub("<[^<]+?>", "", entry.get("summary", "")).strip()
        combined = f"{title} {summary}"

        if not matches_keywords(combined):
            continue

        results.append({
            "source": name,
            "title": title,
            "link": entry.get("link", ""),
            "summary": summary,
            "published": pub_dt.isoformat() if pub_dt else "unknown",
        })

    return results, True


# --------------------------------------------------------------------------
# 2c. FALLBACK SCRAPER — generic WordPress-style article listing parser
# --------------------------------------------------------------------------

def scrape_listing_page(name, listing_url, base_url, cutoff):
    """Generic scraper for WordPress-style news listing/category pages.
    Tries a few common markup patterns since every theme differs slightly.
    Dates are unreliable to parse generically, so this returns everything
    found on the page (usually the most recent 10-20 posts) rather than
    strictly filtering by DAYS_LOOKBACK — recency is approximated by 'this
    is the current listing page', which is good enough for a weekly digest.
    """
    try:
        resp = requests.get(listing_url, headers=HEADERS, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
    except Exception as e:
        print(f"[warn] scrape failed for {name} ({listing_url}): {e}")
        return []

    soup = BeautifulSoup(resp.text, "html.parser")
    candidates = []

    # Pattern 1: <article> wrapper with a heading link inside (most common
    # WordPress theme structure, incl. the JNews theme used by 8am.media)
    for article in soup.find_all("article"):
        link_tag = article.find(["h1", "h2", "h3"])
        link_tag = link_tag.find("a") if link_tag else None
        if not link_tag:
            link_tag = article.find("a", href=True)
        if link_tag and link_tag.get("href"):
            candidates.append((link_tag.get_text(strip=True), link_tag["href"]))

    # Pattern 2: bare heading links outside <article> tags (fallback for
    # simpler themes) — only used if pattern 1 found nothing
    if not candidates:
        for heading in soup.find_all(["h2", "h3"]):
            link_tag = heading.find("a", href=True)
            if link_tag:
                candidates.append((link_tag.get_text(strip=True), link_tag["href"]))

    results = []
    seen_links = set()
    for title, link in candidates:
        if not title or link in seen_links:
            continue
        if link.startswith("/"):
            link = base_url.rstrip("/") + link
        if base_url.split("//")[-1] not in link:
            continue  # skip nav/social links to other domains
        seen_links.add(link)

        if not matches_keywords(title):
            continue

        results.append({
            "source": name + " (scraped)",
            "title": title,
            "link": link,
            "summary": "",  # no reliable excerpt from listing-page scraping
            "published": "unknown (scraped listing page)",
        })

    return results


def fetch_recent_entries():
    cutoff = datetime.now(timezone.utc) - timedelta(days=DAYS_LOOKBACK)
    results = []

    # Standard, known-good RSS feeds
    for feed in FEEDS:
        entries, _ = fetch_feed_entries(feed["name"], feed["url"], cutoff)
        results.extend(entries)

    # Exiled outlets: try their feed first, fall back to scraping
    for src in SCRAPE_SOURCES:
        entries, feed_ok = fetch_feed_entries(src["name"], src["feed_url"], cutoff)
        if feed_ok and entries:
            print(f"[info] {src['name']}: used RSS feed")
            results.extend(entries)
        else:
            print(f"[info] {src['name']}: feed unavailable, falling back to scraping")
            results.extend(scrape_listing_page(
                src["name"], src["listing_url"], src["base_url"], cutoff
            ))
        time.sleep(1)  # be polite — these are small, often under-resourced sites

    return results


# --------------------------------------------------------------------------
# 3. SUMMARIZE (optional — uses Claude API if ANTHROPIC_API_KEY is set)
# --------------------------------------------------------------------------

def summarize_with_claude(entries):
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key or not entries:
        return entries  # fall back to raw feed summaries

    try:
        import anthropic
    except ImportError:
        print("[warn] anthropic package not installed; skipping AI summarization")
        return entries

    client = anthropic.Anthropic(api_key=api_key)

    for e in entries:
        prompt = (
            "Summarize this news item about Afghan security in 2 concise, "
            "neutral sentences. Do not add opinion or speculation.\n\n"
            f"Title: {e['title']}\nSource text: {e['summary'][:1500]}"
        )
        try:
            resp = client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=200,
                messages=[{"role": "user", "content": prompt}],
            )
            e["summary"] = "".join(
                block.text for block in resp.content if block.type == "text"
            ).strip()
        except Exception as ex:
            print(f"[warn] summarization failed for '{e['title']}': {ex}")

    return entries


# --------------------------------------------------------------------------
# 4. RENDER HTML
# --------------------------------------------------------------------------

def render_html(entries):
    today = datetime.now(timezone.utc).strftime("%d %B %Y")
    by_source = {}
    for e in entries:
        by_source.setdefault(e["source"], []).append(e)

    sections = ""
    for source, items in by_source.items():
        cards = ""
        for item in items:
            cards += f"""
            <article class="card">
              <h3><a href="{html.escape(item['link'])}" target="_blank" rel="noopener">{html.escape(item['title'])}</a></h3>
              <p>{html.escape(item['summary'][:500])}</p>
              <div class="meta">{html.escape(item['published'][:10])}</div>
            </article>"""
        sections += f"""
        <section>
          <h2>{html.escape(source)}</h2>
          {cards}
        </section>"""

    if not entries:
        sections = "<p class='empty'>No matching security stories found in the last 7 days.</p>"

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>{SITE_TITLE} — {today}</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
  body {{ font-family: -apple-system, Georgia, serif; max-width: 800px; margin: 40px auto; padding: 0 20px; background: #fafaf8; color: #1a1a1a; }}
  h1 {{ font-size: 1.8rem; border-bottom: 3px solid #b23; padding-bottom: 10px; }}
  h2 {{ font-size: 1.1rem; text-transform: uppercase; letter-spacing: .05em; color: #b23; margin-top: 40px; }}
  .card {{ margin: 18px 0; padding-bottom: 14px; border-bottom: 1px solid #ddd; }}
  .card h3 {{ margin: 0 0 6px 0; font-size: 1.05rem; }}
  .card a {{ color: #1a1a1a; text-decoration: none; }}
  .card a:hover {{ text-decoration: underline; }}
  .meta {{ font-size: .8rem; color: #888; margin-top: 4px; }}
  .subtitle {{ color: #555; }}
  .empty {{ color: #888; font-style: italic; }}
  footer {{ margin-top: 60px; font-size: .8rem; color: #999; }}
</style>
</head>
<body>
  <h1>{SITE_TITLE}</h1>
  <p class="subtitle">Weekly summary of Afghan security news — generated {today}</p>
  {sections}
  <footer>Auto-generated from RSS sources. See sources.md in the repo for the full source list. Not a substitute for reading original reporting.</footer>
</body>
</html>"""


# --------------------------------------------------------------------------
# 5. MAIN
# --------------------------------------------------------------------------

def main():
    entries = fetch_recent_entries()
    print(f"[info] {len(entries)} matching entries found")
    entries = summarize_with_claude(entries)
    html_out = render_html(entries)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(html_out)
    print(f"[info] wrote {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
