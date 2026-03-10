# DEAD DROP

**The Stories That Fell Through the Cracks**

AI-Powered Intelligence & Geopolitics Media Platform — Newsletter + YouTube + Multi-Channel Content Engine.

## Overview

Dead Drop is an automated media platform that discovers, verifies, and publishes intelligence stories hiding in plain sight — buried in UN reports, declassified documents, court filings, and FOIA releases.

## Tech Stack

| Component      | Technology                                       |
| -------------- | ------------------------------------------------ |
| Pipeline       | Python 3.12+ (feedparser, Scrapy, BeautifulSoup) |
| Web            | Next.js 14+ (App Router, TypeScript)             |
| Database       | PostgreSQL 16                                    |
| Cache/Queue    | Redis 7                                          |
| Orchestration  | n8n (self-hosted)                                |
| AI Content     | Claude API (Sonnet + Opus)                       |
| AI Narration   | ElevenLabs API                                   |
| Video Assembly | MoviePy + FFmpeg                                 |
| Maps           | Mapbox GL JS / Folium                            |
| Newsletter     | beehiiv (Scale plan)                             |

## Quick Start

```bash
# Clone the repo
git clone https://github.com/compubear/dead-drop.git
cd dead-drop

# Copy environment variables
cp config/.env.example .env

# Start all services
make dev

# Run tests
make test

# Run linters
make lint
```

## Project Structure

```
dead-drop/
├── pipeline/          # Python — source monitoring, gap detection, content gen
├── video/             # Python — automated video production
├── web/               # Next.js — landing page, archive, subscriber capture
├── n8n/               # Workflow JSON exports & configs
├── scripts/           # deploy.sh, rollback.sh, backup scripts
├── config/            # .env.example, feeds.yaml, prompt templates
├── tests/             # Unit, integration, smoke, E2E tests
├── docs/              # PRD, architecture diagrams, editorial guidelines
├── docker-compose.yml
├── Makefile
└── README.md
```

## Commands

```bash
make dev              # Start local Docker environment
make test             # Run full test suite
make lint             # Run all linters
make deploy           # Production deploy
make rollback         # Emergency rollback
make pipeline-run     # Run full pipeline cycle
make pipeline-score   # Run gap detection scoring only
make video-generate   # Generate video (STORY_ID=xxx)
make db-migrate       # Run pending migrations
make db-backup        # Backup PostgreSQL
```

## License

CONFIDENTIAL — WebXL Digital Solutions
