#!/usr/bin/env python3
"""
RSS Feed Article Collector for AI Agent Daily Digest
Fetches articles from configured RSS feeds within a specified time window.
"""

import argparse
import json
import sys
import io
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import List, Dict, Any
import feedparser
from dateutil import parser as date_parser

# Ensure UTF-8 encoding for stdout on Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')


def load_feed_config(config_path: Path) -> List[str]:
    """Load RSS feed URLs from configuration file."""
    if not config_path.exists():
        print(f"Error: Configuration file not found at {config_path}", file=sys.stderr)
        sys.exit(1)

    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)

    return config.get('feeds', [])


def parse_published_date(entry: Dict[str, Any]) -> datetime:
    """Extract and parse publication date from feed entry."""
    # Try different date fields that might be present
    date_fields = ['published', 'updated', 'created']

    for field in date_fields:
        if field in entry:
            try:
                # feedparser provides parsed dates in published_parsed, updated_parsed, etc.
                parsed_field = f"{field}_parsed"
                if parsed_field in entry and entry[parsed_field]:
                    # Convert struct_time to datetime
                    from time import struct_time
                    import time
                    dt = datetime.fromtimestamp(time.mktime(entry[parsed_field]), tz=timezone.utc)
                    return dt

                # Fallback to string parsing
                dt = date_parser.parse(entry[field])
                # Ensure timezone awareness
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                return dt
            except Exception as e:
                print(f"Warning: Failed to parse date from {field}: {e}", file=sys.stderr)
                continue

    # If no date found, return None
    return None


def fetch_articles(feed_url: str, cutoff_time: datetime) -> List[Dict[str, Any]]:
    """Fetch articles from a single RSS feed published after cutoff_time."""
    articles = []

    try:
        print(f"Fetching feed: {feed_url}")
        feed = feedparser.parse(feed_url)

        if feed.bozo:
            print(f"Warning: Feed parsing issues for {feed_url}: {feed.bozo_exception}", file=sys.stderr)

        for entry in feed.entries:
            # Parse publication date
            pub_date = parse_published_date(entry)

            if pub_date is None:
                print(f"Warning: No date found for entry '{entry.get('title', 'Unknown')}' from {feed_url}", file=sys.stderr)
                # Still include it, but flag it
                date_verified = False
                pub_date_str = "Unknown"
            elif pub_date < cutoff_time:
                # Skip articles older than cutoff
                continue
            else:
                date_verified = True
                pub_date_str = pub_date.isoformat()

            # Extract article data
            article = {
                'title': entry.get('title', 'No Title'),
                'url': entry.get('link', ''),
                'published': pub_date_str,
                'date_verified': date_verified,
                'description': entry.get('summary', entry.get('description', '')),
                'source': feed.get('feed', {}).get('title', feed_url),
                'source_url': feed_url,
                'author': entry.get('author', ''),
                'tags': [tag.term for tag in entry.get('tags', [])]
            }

            articles.append(article)
            print(f"  ✓ {article['title'][:60]}... ({pub_date_str})")

    except Exception as e:
        print(f"Error fetching feed {feed_url}: {e}", file=sys.stderr)

    return articles


def collect_articles(hours: int, config_path: Path, output_path: Path) -> None:
    """Main collection function."""
    # Calculate cutoff time
    cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours)
    print(f"\nCollecting articles published after: {cutoff_time.isoformat()}")
    print(f"(Last {hours} hours)\n")

    # Load feed configuration
    feed_urls = load_feed_config(config_path)
    print(f"Loaded {len(feed_urls)} RSS feeds from configuration\n")

    # Collect articles from all feeds
    all_articles = []
    for feed_url in feed_urls:
        articles = fetch_articles(feed_url, cutoff_time)
        all_articles.extend(articles)

    # Sort by publication date (most recent first)
    all_articles.sort(
        key=lambda x: x['published'] if x['published'] != "Unknown" else "",
        reverse=True
    )

    # Save to JSON
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump({
            'collected_at': datetime.now(timezone.utc).isoformat(),
            'cutoff_time': cutoff_time.isoformat(),
            'hours': hours,
            'total_articles': len(all_articles),
            'articles': all_articles
        }, f, indent=2, ensure_ascii=False)

    print(f"\n{'='*60}")
    print(f"✓ Collected {len(all_articles)} articles")
    print(f"✓ Saved to: {output_path}")

    # Print summary statistics
    verified_count = sum(1 for a in all_articles if a.get('date_verified', False))
    unverified_count = len(all_articles) - verified_count

    if unverified_count > 0:
        print(f"\n⚠ Warning: {unverified_count} articles have unverified dates")
        print("  Please manually review these articles in the digest generation step")

    print(f"{'='*60}\n")


def main():
    parser = argparse.ArgumentParser(
        description='Collect articles from RSS feeds for AI agent digest'
    )
    parser.add_argument(
        '--hours',
        type=int,
        default=24,
        help='Number of hours to look back for articles (default: 24)'
    )
    parser.add_argument(
        '--config',
        type=Path,
        default=Path('ai-digest/src/feeds.json'),
        help='Path to RSS feeds configuration file'
    )
    parser.add_argument(
        '--output',
        type=Path,
        default=Path('ai-digest/data/collected_articles.json'),
        help='Output path for collected articles JSON'
    )

    args = parser.parse_args()

    collect_articles(args.hours, args.config, args.output)


if __name__ == '__main__':
    main()
