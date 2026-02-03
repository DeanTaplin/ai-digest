#!/usr/bin/env python3
"""
Analyze and filter today's collected articles for AI agent digest.
"""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List


def score_article(article: Dict[str, Any]) -> int:
    """Score article relevance (0-100) for AI agents and agentic systems."""
    title = article.get('title', '').lower()
    description = str(article.get('description', '')).lower()
    url = article.get('url', '').lower()
    combined = f"{title} {description}"

    score = 0

    # High-value agentic keywords - 40 points
    agentic_keywords = [
        'agent', 'agentic', 'autonomous', 'multi-agent', 'tool use',
        'function calling', 'mcp', 'model context protocol',
        'reasoning', 'planning', 'workflow', 'orchestration',
        'tool calling', 'langchain', 'langgraph', 'crewai'
    ]
    matches = sum(1 for kw in agentic_keywords if kw in combined)
    score += min(40, matches * 15)

    # Production/practical - 30 points
    production_keywords = [
        'production', 'deployment', 'real-world', 'implementation',
        'case study', 'benchmark', 'framework', 'sdk', 'api',
        'system', 'platform', 'enterprise', 'scale'
    ]
    if any(kw in combined for kw in production_keywords):
        score += 25

    # AI/LLM relevance - 20 points
    if any(kw in combined for kw in ['llm', 'large language', 'ai', 'gpt', 'claude', 'gemini']):
        score += 20

    # Developer focus - 10 points
    if any(kw in combined for kw in ['developer', 'code', 'programming', 'engineering']):
        score += 10

    # Prefer industry sources
    if 'arxiv.org' not in url:
        score += 10

    # Penalty for pure theory
    if 'arxiv.org' in url:
        if any(kw in combined for kw in ['theoretical', 'mathematical proof', 'convergence']):
            score -= 15

    return max(0, min(100, score))


def categorize_article(article: Dict[str, Any]) -> str:
    """Categorize article by focus area."""
    title = article.get('title', '').lower()
    description = str(article.get('description', '')).lower()
    combined = f"{title} {description}"

    if any(kw in combined for kw in ['production', 'deployment', 'real-world', 'case study']):
        return 'Production Use Cases'
    if any(kw in combined for kw in ['framework', 'sdk', 'tool', 'library', 'api']):
        return 'Frameworks & Tools'
    if any(kw in combined for kw in ['tutorial', 'guide', 'how to', 'example']):
        return 'Developer Resources'
    if any(kw in combined for kw in ['trend', 'analysis', 'survey', 'benchmark']):
        return 'Trends & Analysis'
    return 'Research & Breakthroughs'


def main():
    # Load today's collected articles
    input_path = Path('ai-digest/data/collected_articles.json')
    with open(input_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    articles = data.get('articles', [])
    print(f"Analyzing {len(articles)} collected articles...")

    # Score and filter
    scored = []
    for article in articles:
        score = score_article(article)
        if score >= 60:
            scored.append({
                'article': article,
                'score': score,
                'category': categorize_article(article)
            })

    # Sort by score
    scored.sort(key=lambda x: x['score'], reverse=True)

    print(f"Found {len(scored)} articles scoring 60+")

    # Select top articles with diversity
    selected = []
    arxiv_count = 0
    max_arxiv = 3

    for item in scored:
        if len(selected) >= 12:
            break

        url = item['article'].get('url', '')
        if 'arxiv.org' in url:
            if arxiv_count >= max_arxiv:
                continue
            arxiv_count += 1

        selected.append(item)

    # Show distribution
    category_counts = {}
    for item in selected:
        cat = item['category']
        category_counts[cat] = category_counts.get(cat, 0) + 1

    print(f"\nSelected {len(selected)} articles:")
    for cat, count in sorted(category_counts.items()):
        print(f"  {cat}: {count}")

    # Save results
    output = {
        'metadata': {
            'generated_at': datetime.now(timezone.utc).isoformat(),
            'total_collected': len(articles),
            'high_scoring': len(scored),
            'selected': len(selected),
            'arxiv_limit': max_arxiv
        },
        'articles': selected
    }

    output_path = Path('ai-digest/data/filtered_articles.json')
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"\nResults saved to: {output_path}")
    print("\nTop articles:")
    for i, item in enumerate(selected[:10], 1):
        art = item['article']
        print(f"\n{i}. [{item['score']}] {art['title'][:70]}...")
        print(f"   {item['category']}")
        print(f"   {art['url']}")


if __name__ == '__main__':
    main()
