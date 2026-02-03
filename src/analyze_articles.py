#!/usr/bin/env python3
"""Analyze and filter collected articles for AI digest."""

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import List, Dict, Tuple

def load_articles(filepath: str) -> List[Dict]:
    """Load articles from JSON file."""
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
        # Handle both list and dict formats
        if isinstance(data, dict) and 'articles' in data:
            return data['articles']
        return data

def is_recent(published: str, hours: int = 24) -> bool:
    """Check if article was published within the last N hours."""
    try:
        pub_date = datetime.fromisoformat(published.replace('Z', '+00:00'))
        cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
        return pub_date >= cutoff
    except:
        return False

def score_article(article: Dict) -> Tuple[int, str]:
    """
    Score article relevance to AI agents and agentic systems (0-100).
    Returns (score, reason).

    Prioritizes:
    - Production use cases and real-world implementations (highest)
    - Frameworks and tools
    - Developer resources
    - Industry trends
    - Research papers (limit arXiv, only breakthrough research)
    """
    title = article.get('title', '').lower()
    summary = article.get('summary', article.get('description', '')).lower()
    link = article.get('link', article.get('url', ''))
    content = f"{title} {summary}"

    # Check if it's an arXiv paper
    is_arxiv = 'arxiv.org' in link

    # High priority keywords - production use cases and real implementations
    production_keywords = [
        'production', 'deployment', 'case study', 'real-world', 'enterprise',
        'customer', 'implementation', 'using', 'how to', 'practical',
        'langsmith', 'langgraph', 'servicenow', 'company'
    ]

    # Agent-specific keywords
    agent_keywords = [
        'agent', 'agentic', 'autonomous', 'tool use', 'tool calling',
        'mcp', 'model context protocol', 'multi-agent', 'orchestration',
        'reasoning', 'planning', 'workflow'
    ]

    # Framework/tool keywords
    framework_keywords = [
        'framework', 'library', 'sdk', 'api', 'tool', 'platform',
        'langchain', 'autogen', 'crewai', 'anthropic', 'openai'
    ]

    # Calculate base score
    score = 0
    reasons = []

    # Check for agent relevance (required for any article)
    agent_matches = sum(1 for kw in agent_keywords if kw in content)
    if agent_matches == 0:
        return (0, "Not relevant to AI agents")

    score += min(agent_matches * 15, 40)
    reasons.append(f"agent keywords ({agent_matches})")

    # Boost for production use cases (highest priority)
    production_matches = sum(1 for kw in production_keywords if kw in content)
    if production_matches > 0:
        score += min(production_matches * 20, 50)
        reasons.append(f"production focus ({production_matches})")

    # Moderate boost for frameworks/tools
    framework_matches = sum(1 for kw in framework_keywords if kw in content)
    if framework_matches > 0:
        score += min(framework_matches * 10, 30)
        reasons.append(f"framework/tool ({framework_matches})")

    # Penalize arXiv papers heavily unless they have production/practical focus
    if is_arxiv:
        if production_matches == 0:
            score = min(score * 0.3, 40)  # Cap arXiv papers at 40 unless production-focused
            reasons.append("arXiv penalty (research paper)")
        else:
            reasons.append("arXiv with production relevance")

    return (min(score, 100), "; ".join(reasons))

def categorize_article(article: Dict, score: int) -> str:
    """Categorize article into one of the digest categories."""
    title = article.get('title', '').lower()
    summary = article.get('summary', article.get('description', '')).lower()
    link = article.get('link', article.get('url', ''))
    content = f"{title} {summary}"

    is_arxiv = 'arxiv.org' in link

    # Check category indicators (in priority order)
    production_indicators = ['production', 'deployment', 'case study', 'customer', 'enterprise', 'real-world', 'implementation']
    framework_indicators = ['framework', 'library', 'sdk', 'api', 'tool', 'release', 'version']
    resource_indicators = ['guide', 'tutorial', 'how to', 'documentation', 'learning']
    analysis_indicators = ['trend', 'analysis', 'survey', 'benchmark', 'comparison', 'review']

    if any(ind in content for ind in production_indicators):
        return "Production Use Cases"
    elif any(ind in content for ind in framework_indicators) and not is_arxiv:
        return "Frameworks & Tools"
    elif any(ind in content for ind in resource_indicators):
        return "Developer Resources"
    elif any(ind in content for ind in analysis_indicators):
        return "Trends & Analysis"
    else:
        return "Research & Breakthroughs"

def main():
    # Load articles
    data_dir = Path(__file__).parent.parent / 'data'
    articles = load_articles(data_dir / 'collected_articles.json')

    print(f"Total articles collected: {len(articles)}")

    # Filter by date (last 48 hours to account for timezone issues)
    recent_articles = [a for a in articles if is_recent(a.get('published', ''), hours=48)]
    print(f"Recent articles (48h): {len(recent_articles)}")

    # Score and filter articles
    scored_articles = []
    for article in recent_articles:
        score, reason = score_article(article)
        if score >= 60:
            category = categorize_article(article, score)
            scored_articles.append({
                'article': article,
                'score': score,
                'reason': reason,
                'category': category
            })

    # Sort by score (descending)
    scored_articles.sort(key=lambda x: x['score'], reverse=True)

    print(f"\nHigh-scoring articles (60+): {len(scored_articles)}")

    # Group by category and limit arXiv papers
    by_category = {}
    arxiv_count = 0
    arxiv_limit = 3

    filtered_articles = []
    for item in scored_articles:
        article = item['article']
        link = article.get('link', article.get('url', ''))
        is_arxiv = 'arxiv.org' in link

        # Apply arXiv limit
        if is_arxiv:
            if arxiv_count >= arxiv_limit:
                continue
            arxiv_count += 1

        category = item['category']
        if category not in by_category:
            by_category[category] = []
        by_category[category].append(item)
        filtered_articles.append(item)

    print(f"After arXiv limit ({arxiv_limit} max): {len(filtered_articles)}")

    # Print category breakdown
    print("\nCategory breakdown:")
    category_order = [
        "Production Use Cases",
        "Frameworks & Tools",
        "Developer Resources",
        "Trends & Analysis",
        "Research & Breakthroughs"
    ]

    for category in category_order:
        if category in by_category:
            count = len(by_category[category])
            print(f"  {category}: {count}")

    # Print top articles
    print("\n" + "="*80)
    print("TOP ARTICLES FOR DIGEST")
    print("="*80)

    for category in category_order:
        if category not in by_category:
            continue

        items = by_category[category]
        print(f"\n## {category} ({len(items)} articles)")
        print("-" * 80)

        for item in items[:5]:  # Show top 5 per category
            article = item['article']
            print(f"\n[{item['score']}] {article.get('title', 'No title')}")
            link = article.get('link', article.get('url', 'No link'))
            print(f"Source: {link}")
            print(f"Published: {article.get('published', 'No date')}")
            print(f"Reason: {item['reason']}")
            desc = article.get('summary', article.get('description', ''))
            if desc:
                summary = desc[:200] + "..." if len(desc) > 200 else desc
                print(f"Summary: {summary}")

    # Save filtered articles for digest generation
    output = {
        'metadata': {
            'generated_at': datetime.now(timezone.utc).isoformat(),
            'total_collected': len(articles),
            'recent_articles': len(recent_articles),
            'high_scoring': len(scored_articles),
            'after_arxiv_limit': len(filtered_articles),
            'arxiv_limit': arxiv_limit
        },
        'articles': filtered_articles
    }

    output_file = data_dir / 'filtered_articles.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"\n\nFiltered articles saved to: {output_file}")

if __name__ == '__main__':
    main()
