#!/usr/bin/env python3
"""
Filter collected articles and generate daily digest.
Focuses on AI agents, agentic AI, and autonomous systems for developers.
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any


def score_article(article: Dict[str, Any]) -> int:
    """
    Score article relevance (0-100) based on AI agent/agentic system focus.
    Prioritizes production use cases over academic research.
    """
    title = article.get('title', '').lower()
    description = article.get('description', '').lower()
    url = article.get('url', '').lower()
    combined = f"{title} {description}"

    score = 0

    # High-value keywords (agentic AI focus) - 40 points
    high_value = [
        'agent', 'agentic', 'autonomous', 'multi-agent', 'tool use',
        'function calling', 'mcp', 'model context protocol',
        'reasoning', 'planning', 'workflow', 'orchestration'
    ]
    for keyword in high_value:
        if keyword in combined:
            score += 20
            break

    # Production/practical keywords - 30 points
    production_keywords = [
        'production', 'deployment', 'real-world', 'implementation',
        'case study', 'benchmark', 'framework', 'sdk', 'api',
        'tool', 'application', 'system', 'platform'
    ]
    for keyword in production_keywords:
        if keyword in combined:
            score += 15
            break

    # AI/LLM relevance - 20 points
    ai_keywords = [
        'llm', 'large language model', 'gpt', 'claude', 'gemini',
        'ai', 'artificial intelligence', 'neural', 'transformer'
    ]
    for keyword in ai_keywords:
        if keyword in combined:
            score += 20
            break

    # Developer-focused - 10 points
    dev_keywords = [
        'developer', 'coding', 'programming', 'software',
        'engineering', 'code', 'github'
    ]
    for keyword in dev_keywords:
        if keyword in combined:
            score += 10
            break

    # Bonus for non-arXiv sources (prefer industry news)
    if 'arxiv.org' not in url:
        score += 10

    # Penalty for pure theory/academic without practical focus
    if 'arxiv.org' in url:
        theory_only = [
            'theoretical', 'mathematical proof', 'convergence analysis',
            'formal verification', 'complexity bounds'
        ]
        if any(keyword in combined for keyword in theory_only):
            score -= 20

    # Bonus for breakthrough/novel research (if from arXiv)
    if 'arxiv.org' in url:
        breakthrough_keywords = [
            'breakthrough', 'novel', 'first', 'new benchmark',
            'state-of-the-art', 'sota', 'outperforms'
        ]
        if any(keyword in combined for keyword in breakthrough_keywords):
            score += 15

    return max(0, min(100, score))


def categorize_article(article: Dict[str, Any]) -> str:
    """Categorize article by primary focus."""
    title = article.get('title', '').lower()
    description = article.get('description', '').lower()
    url = article.get('url', '').lower()
    combined = f"{title} {description}"

    # Priority order matters!
    if any(k in combined for k in ['production', 'deployment', 'real-world', 'case study', 'implementation']):
        return 'Production Use Cases'

    if any(k in combined for k in ['framework', 'sdk', 'tool', 'library', 'api', 'platform']):
        return 'Frameworks & Tools'

    if any(k in combined for k in ['tutorial', 'guide', 'how to', 'documentation', 'example']):
        return 'Developer Resources'

    if any(k in combined for k in ['trend', 'analysis', 'survey', 'benchmark', 'evaluation']):
        return 'Trends & Analysis'

    # Default to research (lowest priority)
    return 'Research & Breakthroughs'


def generate_summary(article: Dict[str, Any]) -> Dict[str, str]:
    """Generate article summary components (to be filled manually or by LLM)."""
    return {
        'title': article.get('title', ''),
        'url': article.get('url', ''),
        'summary': '',  # To be filled
        'key_insight': '',  # To be filled
        'why_matters': ''  # To be filled
    }


def main():
    # Load collected articles
    with open('ai-digest/data/collected_articles.json', 'r', encoding='utf-8') as f:
        data = json.load(f)

    articles = data.get('articles', [])
    print(f"Total collected articles: {len(articles)}")

    # Score and filter articles
    scored_articles = []
    for article in articles:
        score = score_article(article)
        if score >= 60:  # Only keep high-scoring articles
            article['relevance_score'] = score
            article['category'] = categorize_article(article)
            scored_articles.append(article)

    # Sort by score (descending)
    scored_articles.sort(key=lambda x: x['relevance_score'], reverse=True)

    print(f"Articles scoring 60+: {len(scored_articles)}")

    # Limit to top articles with category distribution
    category_counts = {}
    selected_articles = []
    max_arxiv = 3  # Limit arXiv papers
    arxiv_count = 0

    for article in scored_articles:
        if len(selected_articles) >= 15:
            break

        # Limit arXiv papers
        if 'arxiv.org' in article.get('url', ''):
            if arxiv_count >= max_arxiv:
                continue
            arxiv_count += 1

        selected_articles.append(article)
        category = article['category']
        category_counts[category] = category_counts.get(category, 0) + 1

    print(f"\nSelected {len(selected_articles)} articles:")
    for cat, count in sorted(category_counts.items()):
        print(f"  {cat}: {count}")

    # Save filtered articles for review
    output = {
        'date': datetime.now().isoformat(),
        'total_scored': len(scored_articles),
        'selected_count': len(selected_articles),
        'category_distribution': category_counts,
        'articles': selected_articles
    }

    with open('ai-digest/data/filtered_articles.json', 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"\nFiltered articles saved to: ai-digest/data/filtered_articles.json")
    print("\nTop 10 articles by score:")
    for i, article in enumerate(selected_articles[:10], 1):
        print(f"{i}. [{article['relevance_score']}] {article['title'][:80]}...")
        print(f"   Category: {article['category']}")
        print(f"   URL: {article['url']}")
        print()


if __name__ == '__main__':
    main()
