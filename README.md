# AI Agent Daily Digest

Automated daily digest of news about AI agents, agentic AI, and autonomous systems for software developers.

## Directory Structure

```doc
ai-digest/
├── src/
│   ├── collect_articles.py    # RSS feed collection script
│   └── feeds.json              # RSS feed configuration
├── data/
│   └── collected_articles.json # Collected articles (generated)
├── digests/
│   └── YYYY/
│       └── MM/
│           └── digest-YYYY-MM-DD.md  # Generated digests
└── requirements.txt            # Python dependencies
```

## Setup

1. Install dependencies:

   ```bash
   pip install -r ai-digest/requirements.txt
   ```

2. RSS feeds are configured in `src/feeds.json`

## Usage

### Using the Slash Command (Recommended)

Simply run:

```bash
/ai-digest
```

This will:

1. Collect articles from the last 24 hours
2. Filter and score for relevance
3. Generate a markdown digest in `digests/YYYY/MM/`

### Manual Collection

Collect articles from the last 24 hours:

```bash
python ai-digest/src/collect_articles.py --hours 24
```

This creates `ai-digest/data/collected_articles.json` with raw articles.

### Configuration

Edit `src/feeds.json` to add or remove RSS feeds.

## Workflow

1. **Collect**: Fetch articles from configured RSS feeds
2. **Review**: Manually verify publication dates
3. **Filter**: Score articles 0-100 for relevance (keep 60+)
4. **Summarize**: Write concise summaries with key insights
5. **Generate**: Create markdown digest organized by category

## Quality Standards

- Manually verify publication dates for all articles
- Exclude articles not from the specified time window
- Score based on relevance to AI agents and agentic systems
- Focus on practical insights for software developers
- Quality over quantity: Better to have fewer highly relevant articles
