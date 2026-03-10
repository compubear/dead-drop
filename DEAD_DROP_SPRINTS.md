# DEAD DROP — Sprint Plan & Development Roadmap

**Project:** Dead Drop — AI-Powered Intelligence & Geopolitics Media Platform
**Version:** 1.0 | March 2026
**Owner:** Yogev (WebXL Digital Solutions)
**Repo:** `github.com/compubear/dead-drop`
**Infrastructure:** ab-prod (Hetzner)
**IDE:** Google Antigravity

---

## Project Structure

```
dead-drop/
├── pipeline/                  # Python — source monitoring, gap detection, content gen
│   ├── sources/               # RSS fetchers, scrapers, document monitors
│   ├── gap_detection/         # Significance vs Coverage scoring engine
│   ├── content_gen/           # Claude API content generation (newsletter, video, social)
│   ├── verification/          # Fact-checking & bias detection module
│   └── publishers/            # Auto-publish to beehiiv, YouTube, Twitter, Reddit, Telegram
├── video/                     # Python — automated video production
│   ├── narration/             # ElevenLabs API integration
│   ├── assembly/              # MoviePy + FFmpeg video assembly
│   ├── maps/                  # Mapbox/Folium map generation
│   ├── thumbnails/            # DALL-E / Midjourney thumbnail gen
│   └── templates/             # Video format templates (Buried Report, Forgotten War, Declassified)
├── web/                       # Next.js — landing page, archive, subscriber capture
│   ├── app/                   # App router pages
│   ├── components/            # UI components
│   └── lib/                   # Utilities, API helpers
├── n8n/                       # Workflow JSON exports & configs
├── scripts/                   # deploy.sh, rollback.sh, backup, migration scripts
├── config/                    # .env.example, feeds.yaml, prompts/, scoring_config.yaml
├── tests/                     # Unit, integration, smoke, E2E tests
│   ├── unit/
│   ├── integration/
│   ├── smoke/
│   └── e2e/
├── docs/                      # PRD, architecture diagrams, editorial guidelines
├── docker-compose.yml
├── Makefile
├── .github/workflows/         # CI/CD GitHub Actions
└── README.md
```

---

## Tech Stack Reference

| Component | Tech | Version / Plan |
|-----------|------|----------------|
| Pipeline | Python 3.12+ | ruff, mypy, black |
| Web | Next.js 14+ (App Router) | TypeScript strict, Prettier + ESLint |
| Database | PostgreSQL 16 | On ab-prod, Docker |
| Cache/Queue | Redis 7 | On ab-prod, Docker |
| Orchestration | n8n (self-hosted) | Latest stable |
| AI Content | Claude API | Sonnet (scoring), Opus (writing) |
| AI Narration | ElevenLabs API | Pro plan |
| Video Assembly | MoviePy + FFmpeg | Python |
| Maps | Mapbox GL JS / Folium | Free tier |
| Newsletter | beehiiv | Scale plan |
| Social APIs | Twitter API, YouTube Data API, Reddit API | Basic/free tiers |
| Thumbnails | DALL-E API | Per-image pricing |
| Deployment | Docker Compose on ab-prod | GitHub Actions CI/CD |
| Monitoring | Uptime Kuma + Grafana | Self-hosted |

---

## Sprint Overview

| Sprint | Name | Duration | Focus |
|--------|------|----------|-------|
| 0 | Foundation | 3 days | Repo, infra, Docker, CI/CD |
| 1 | Source Monitoring Engine | 5 days | RSS ingestion, scrapers, DB schema |
| 2 | Gap Detection Engine | 5 days | Significance/Coverage scoring, Claude API |
| 3 | Content Generation Pipeline | 5 days | Newsletter drafts, video scripts, social posts |
| 4 | Verification Module | 3 days | Fact-check protocol, bias detection |
| 5 | Newsletter System | 4 days | beehiiv integration, templates, auto-publish |
| 6 | Video Production Pipeline | 7 days | ElevenLabs, MoviePy, assembly, templates |
| 7 | Social Distribution Engine | 4 days | Twitter, Reddit, Telegram, YouTube auto-publish |
| 8 | Web (Landing + Archive) | 4 days | Next.js site, SEO, subscriber capture |
| 9 | Content Stockpile | 5 days | Pre-launch content: 15 newsletters, 6 videos, 10 threads |
| 10 | Launch & Growth Infra | 3 days | Analytics, referral program, ad network setup |

**Total estimated: ~48 working days (~10 weeks)**

---

## Sprint 0 — Foundation

**Duration:** 3 days
**Goal:** Repo structure, Docker infrastructure, CI/CD pipeline, development environment ready.

### Tasks

#### S0-T1: Repository Setup
- [ ] Create `compubear/dead-drop` repo on GitHub
- [ ] Initialize with README.md, .gitignore (Python + Node), LICENSE
- [ ] Create branch protection rules on `main` (require PR, require CI pass)
- [ ] Set up project structure per the tree above (empty directories with `.gitkeep`)
- [ ] Create `.env.example` with all required environment variables:
  ```
  # Database
  POSTGRES_HOST=localhost
  POSTGRES_PORT=5432
  POSTGRES_DB=deaddrop
  POSTGRES_USER=deaddrop
  POSTGRES_PASSWORD=

  # Redis
  REDIS_URL=redis://localhost:6379/0

  # APIs
  CLAUDE_API_KEY=
  ELEVENLABS_API_KEY=
  TWITTER_BEARER_TOKEN=
  TWITTER_API_KEY=
  TWITTER_API_SECRET=
  TWITTER_ACCESS_TOKEN=
  TWITTER_ACCESS_SECRET=
  YOUTUBE_API_KEY=
  REDDIT_CLIENT_ID=
  REDDIT_CLIENT_SECRET=
  REDDIT_USERNAME=
  REDDIT_PASSWORD=
  DALLE_API_KEY=
  MAPBOX_TOKEN=

  # beehiiv
  BEEHIIV_API_KEY=
  BEEHIIV_PUBLICATION_ID=

  # Telegram
  TELEGRAM_BOT_TOKEN=
  TELEGRAM_CHANNEL_ID=

  # App
  APP_ENV=production
  LOG_LEVEL=INFO
  PIPELINE_SCHEDULE_CRON=0 6 * * *
  ```

#### S0-T2: Docker Compose Setup
- [ ] Create `docker-compose.yml` with services:
  - `postgres` (PostgreSQL 16, persistent volume, NOT exposed to host — internal only)
  - `redis` (Redis 7, internal only)
  - `n8n` (self-hosted, persistent volume, exposed on internal port)
  - `pipeline` (Python 3.12, custom Dockerfile)
  - `web` (Next.js, custom Dockerfile)
  - `monitoring` (Uptime Kuma)
- [ ] Create `pipeline/Dockerfile`:
  ```dockerfile
  FROM python:3.12-slim
  RUN apt-get update && apt-get install -y ffmpeg libmagic1 && rm -rf /var/lib/apt/lists/*
  WORKDIR /app
  COPY requirements.txt .
  RUN pip install --no-cache-dir -r requirements.txt
  COPY . .
  CMD ["python", "-m", "pipeline.main"]
  ```
- [ ] Create `web/Dockerfile` (multi-stage Next.js build)
- [ ] Create `docker-compose.override.yml` for local development (port mappings, volume mounts)
- [ ] Verify all services start cleanly: `docker compose up -d`

#### S0-T3: CI/CD Pipeline
- [ ] Create `.github/workflows/ci.yml`:
  ```yaml
  name: CI
  on: [pull_request]
  jobs:
    lint-python:
      runs-on: ubuntu-latest
      steps:
        - uses: actions/checkout@v4
        - uses: actions/setup-python@v5
          with: { python-version: "3.12" }
        - run: pip install ruff mypy
        - run: ruff check pipeline/ video/
        - run: mypy pipeline/ video/ --ignore-missing-imports

    lint-web:
      runs-on: ubuntu-latest
      steps:
        - uses: actions/checkout@v4
        - uses: actions/setup-node@v4
          with: { node-version: "20" }
        - run: cd web && npm ci && npm run lint

    test:
      runs-on: ubuntu-latest
      services:
        postgres:
          image: postgres:16
          env: { POSTGRES_DB: deaddrop_test, POSTGRES_USER: test, POSTGRES_PASSWORD: test }
          ports: ["5432:5432"]
        redis:
          image: redis:7
          ports: ["6379:6379"]
      steps:
        - uses: actions/checkout@v4
        - uses: actions/setup-python@v5
          with: { python-version: "3.12" }
        - run: pip install -r pipeline/requirements.txt -r tests/requirements.txt
        - run: pytest tests/ -v --cov=pipeline --cov-report=term-missing
  ```
- [ ] Create `.github/workflows/deploy.yml` (on merge to main → SSH deploy to ab-prod)

#### S0-T4: Makefile
- [ ] Create `Makefile`:
  ```makefile
  .PHONY: dev test lint deploy rollback pipeline-run video-generate

  dev:
  	docker compose -f docker-compose.yml -f docker-compose.override.yml up -d

  test:
  	pytest tests/ -v --cov=pipeline

  lint:
  	ruff check pipeline/ video/
  	mypy pipeline/ video/ --ignore-missing-imports
  	cd web && npm run lint

  deploy:
  	bash scripts/deploy.sh

  rollback:
  	bash scripts/rollback.sh

  pipeline-run:
  	docker compose exec pipeline python -m pipeline.main --run-once

  pipeline-score:
  	docker compose exec pipeline python -m pipeline.gap_detection.score --today

  video-generate:
  	docker compose exec pipeline python -m video.generate --story-id=$(STORY_ID)

  db-migrate:
  	docker compose exec pipeline python -m pipeline.db.migrate

  db-backup:
  	bash scripts/backup_db.sh
  ```

#### S0-T5: Deploy & Rollback Scripts
- [ ] Create `scripts/deploy.sh`:
  ```bash
  #!/bin/bash
  set -euo pipefail
  echo "=== Dead Drop Deploy ==="

  # 1. Backup
  echo "[1/7] Backing up database..."
  bash scripts/backup_db.sh

  # 2. Pull latest
  echo "[2/7] Pulling latest code..."
  cd /opt/dead-drop && git pull origin main

  # 3. Build
  echo "[3/7] Building containers..."
  docker compose build --no-cache

  # 4. Migrate
  echo "[4/7] Running migrations..."
  docker compose run --rm pipeline python -m pipeline.db.migrate

  # 5. Restart
  echo "[5/7] Restarting services..."
  docker compose up -d

  # 6. Health check
  echo "[6/7] Health check..."
  sleep 10
  curl -sf http://localhost:3000/api/health || { echo "HEALTH CHECK FAILED"; bash scripts/rollback.sh; exit 1; }

  # 7. Smoke test
  echo "[7/7] Smoke test..."
  docker compose exec pipeline python -m tests.smoke || { echo "SMOKE TEST FAILED"; bash scripts/rollback.sh; exit 1; }

  # Notify
  curl -s "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage" \
    -d "chat_id=${TELEGRAM_CHANNEL_ID}" \
    -d "text=✅ Dead Drop deployed successfully at $(date)"

  echo "=== Deploy Complete ==="
  ```
- [ ] Create `scripts/rollback.sh` (git revert + rebuild + restart)
- [ ] Create `scripts/backup_db.sh` (pg_dump to timestamped file + keep last 7)

#### S0-T6: Python Project Setup
- [ ] Create `pipeline/requirements.txt`:
  ```
  anthropic>=0.40.0
  feedparser>=6.0
  beautifulsoup4>=4.12
  scrapy>=2.11
  httpx>=0.27
  psycopg[binary]>=3.2
  redis>=5.0
  pydantic>=2.9
  pydantic-settings>=2.5
  python-dotenv>=1.0
  structlog>=24.0
  tenacity>=9.0
  schedule>=1.2
  ```
- [ ] Create `video/requirements.txt`:
  ```
  moviepy>=1.0
  Pillow>=10.0
  elevenlabs>=1.0
  folium>=0.17
  selenium>=4.25
  ```
- [ ] Create `tests/requirements.txt`:
  ```
  pytest>=8.0
  pytest-cov>=5.0
  pytest-asyncio>=0.24
  responses>=0.25
  factory-boy>=3.3
  ```
- [ ] Create `pipeline/__init__.py`, `pipeline/main.py` (entry point with CLI)
- [ ] Create `pipeline/config.py` (Pydantic Settings from .env)
- [ ] Set up structlog with JSON formatting

**Acceptance Criteria:**
- `docker compose up -d` starts all services without errors
- `make test` runs (even if no real tests yet — just verifies setup)
- `make lint` passes on empty project
- CI runs on GitHub on PR creation
- deploy.sh runs end-to-end on ab-prod (manual test)

---

## Sprint 1 — Source Monitoring Engine

**Duration:** 5 days
**Goal:** Automated ingestion of 100+ sources, stored in PostgreSQL, deduplicated.

### Tasks

#### S1-T1: Database Schema
- [ ] Create migration `001_initial_schema.sql`:
  ```sql
  -- Sources: registered feeds and monitors
  CREATE TABLE sources (
      id SERIAL PRIMARY KEY,
      name VARCHAR(255) NOT NULL,
      url TEXT NOT NULL,
      source_type VARCHAR(50) NOT NULL,  -- rss, scraper, api, document_monitor
      pillar VARCHAR(50) NOT NULL,       -- intelligence, conflicts, ai, cyber, historical
      enabled BOOLEAN DEFAULT true,
      fetch_interval_minutes INT DEFAULT 60,
      last_fetched_at TIMESTAMPTZ,
      created_at TIMESTAMPTZ DEFAULT NOW()
  );

  -- Raw ingested items before scoring
  CREATE TABLE raw_items (
      id SERIAL PRIMARY KEY,
      source_id INT REFERENCES sources(id),
      external_id VARCHAR(512),          -- unique ID from source (URL hash, guid, etc.)
      title TEXT NOT NULL,
      content TEXT,
      url TEXT,
      published_at TIMESTAMPTZ,
      ingested_at TIMESTAMPTZ DEFAULT NOW(),
      content_hash VARCHAR(64),          -- SHA-256 for dedup
      metadata JSONB DEFAULT '{}',       -- flexible: author, tags, document_type, etc.
      UNIQUE(source_id, external_id)
  );

  -- Scored stories (after gap detection)
  CREATE TABLE stories (
      id SERIAL PRIMARY KEY,
      raw_item_ids INT[] NOT NULL,       -- can combine multiple raw items
      title TEXT NOT NULL,
      summary TEXT,
      pillar VARCHAR(50) NOT NULL,
      significance_score FLOAT,          -- 1-10
      coverage_score FLOAT,              -- 1-10
      gap_score FLOAT GENERATED ALWAYS AS (significance_score - coverage_score) STORED,
      scoring_reasoning TEXT,            -- Claude's explanation
      status VARCHAR(30) DEFAULT 'scored', -- scored, selected, in_progress, verified, published, rejected
      assigned_at TIMESTAMPTZ,
      published_at TIMESTAMPTZ,
      metadata JSONB DEFAULT '{}',
      created_at TIMESTAMPTZ DEFAULT NOW()
  );

  -- Generated content outputs
  CREATE TABLE content_outputs (
      id SERIAL PRIMARY KEY,
      story_id INT REFERENCES stories(id),
      output_type VARCHAR(50) NOT NULL,  -- newsletter, video_script, twitter_thread, reddit_post, shorts_script, telegram
      content TEXT NOT NULL,
      status VARCHAR(30) DEFAULT 'draft', -- draft, reviewed, approved, published
      published_url TEXT,
      metadata JSONB DEFAULT '{}',
      created_at TIMESTAMPTZ DEFAULT NOW(),
      published_at TIMESTAMPTZ
  );

  -- Verification checklist per story
  CREATE TABLE verifications (
      id SERIAL PRIMARY KEY,
      story_id INT REFERENCES stories(id),
      primary_source_verified BOOLEAN DEFAULT false,
      primary_source_url TEXT,
      claims_cross_referenced BOOLEAN DEFAULT false,
      cross_reference_notes TEXT,
      uncertainty_labeled BOOLEAN DEFAULT false,
      bias_check_passed BOOLEAN DEFAULT false,
      bias_check_notes TEXT,
      human_approved BOOLEAN DEFAULT false,
      human_approved_at TIMESTAMPTZ,
      notes TEXT,
      created_at TIMESTAMPTZ DEFAULT NOW()
  );

  -- Indexes
  CREATE INDEX idx_raw_items_content_hash ON raw_items(content_hash);
  CREATE INDEX idx_raw_items_ingested_at ON raw_items(ingested_at DESC);
  CREATE INDEX idx_stories_gap_score ON stories(gap_score DESC);
  CREATE INDEX idx_stories_status ON stories(status);
  CREATE INDEX idx_stories_pillar ON stories(pillar);
  ```
- [ ] Create migration runner in `pipeline/db/migrate.py`
- [ ] Run migration on ab-prod

#### S1-T2: Source Configuration
- [ ] Create `config/feeds.yaml`:
  ```yaml
  sources:
    # === INTELLIGENCE ===
    - name: CIA FOIA Reading Room
      url: https://www.cia.gov/readingroom/collection
      type: scraper
      pillar: intelligence
      interval: 1440  # daily

    - name: The Black Vault RSS
      url: https://www.theblackvault.com/documentarchive/feed/
      type: rss
      pillar: intelligence
      interval: 60

    - name: SpyTalk Substack
      url: https://spytalk.substack.com/feed
      type: rss
      pillar: intelligence
      interval: 120

    - name: The Intercept
      url: https://theintercept.com/feed/?rss
      type: rss
      pillar: intelligence
      interval: 60

    # === CONFLICTS ===
    - name: ACLED Data
      url: https://acleddata.com/feed/
      type: rss
      pillar: conflicts
      interval: 360

    - name: War on the Rocks
      url: https://warontherocks.com/feed/
      type: rss
      pillar: conflicts
      interval: 120

    - name: Defense One
      url: https://www.defenseone.com/rss/
      type: rss
      pillar: conflicts
      interval: 60

    - name: The War Zone
      url: https://www.thedrive.com/the-war-zone/feed
      type: rss
      pillar: conflicts
      interval: 60

    - name: SIPRI Publications
      url: https://www.sipri.org/rss.xml
      type: rss
      pillar: conflicts
      interval: 1440

    - name: Congressional Research Service
      url: https://crsreports.congress.gov/rss/reports
      type: rss
      pillar: conflicts
      interval: 360

    # === AI ===
    - name: ArXiv cs.AI
      url: http://export.arxiv.org/rss/cs.AI
      type: rss
      pillar: ai
      interval: 360

    - name: ArXiv cs.CR (Crypto & Security)
      url: http://export.arxiv.org/rss/cs.CR
      type: rss
      pillar: ai
      interval: 360

    - name: NIST AI
      url: https://www.nist.gov/artificial-intelligence/rss.xml
      type: rss
      pillar: ai
      interval: 1440

    - name: AI Incident Database
      url: https://incidentdatabase.ai/rss.xml
      type: rss
      pillar: ai
      interval: 360

    # === CYBER ===
    - name: CISA Advisories
      url: https://www.cisa.gov/cybersecurity-advisories/all.xml
      type: rss
      pillar: cyber
      interval: 120

    - name: Krebs on Security
      url: https://krebsonsecurity.com/feed/
      type: rss
      pillar: cyber
      interval: 120

    - name: The Record
      url: https://therecord.media/feed
      type: rss
      pillar: cyber
      interval: 60

    - name: BleepingComputer
      url: https://www.bleepingcomputer.com/feed/
      type: rss
      pillar: cyber
      interval: 60

    - name: Citizen Lab
      url: https://citizenlab.ca/feed/
      type: rss
      pillar: cyber
      interval: 360

    # === HISTORICAL ===
    - name: NARA Latest Releases
      url: https://www.archives.gov/rss/new-items.xml
      type: rss
      pillar: historical
      interval: 1440

    - name: Wilson Center Digital Archive
      url: https://digitalarchive.wilsoncenter.org/rss
      type: rss
      pillar: historical
      interval: 1440

    # ... expand to 100+ sources in production
  ```
- [ ] Create `pipeline/sources/config_loader.py` — loads YAML, validates, syncs to DB

#### S1-T3: RSS Fetcher
- [ ] Create `pipeline/sources/rss_fetcher.py`:
  - Uses `feedparser` + `httpx` for async fetching
  - Parses feed entries → extracts title, content, url, published date
  - Computes `content_hash` (SHA-256 of title + url) for dedup
  - Checks Redis before DB insert (`SISMEMBER deaddrop:seen_hashes {hash}`)
  - Inserts new items to `raw_items` table
  - Updates `sources.last_fetched_at`
  - Handles: timeouts, malformed feeds, encoding issues, rate limiting
  - Structured logging for every fetch operation
- [ ] Unit tests: parse sample feeds, dedup logic, error handling

#### S1-T4: Web Scraper Module
- [ ] Create `pipeline/sources/scraper.py`:
  - Base scraper class with `httpx` + `BeautifulSoup`
  - Per-source scraper configs (CSS selectors, pagination)
  - Initial scrapers for: CIA FOIA Reading Room, NARA document releases, UN document repository
  - Polite scraping: respect robots.txt, 2-5 sec delays, proper User-Agent
  - Output → same `raw_items` table
- [ ] Unit tests with mocked HTML responses

#### S1-T5: Document Monitor
- [ ] Create `pipeline/sources/document_monitor.py`:
  - Monitors specific pages for new document uploads (PDF, reports)
  - Compares page snapshot hashes to detect changes
  - Downloads and extracts text from new PDFs (using `pymupdf` or `pdfplumber`)
  - Stores extracted text in `raw_items.content`
- [ ] Initial monitors: CIA FOIA, ICC/ICJ filings, SIPRI data releases

#### S1-T6: Orchestration
- [ ] Create `pipeline/sources/scheduler.py`:
  - Reads source configs with their `fetch_interval_minutes`
  - Runs fetchers on schedule using Python `schedule` library
  - Parallel execution with `asyncio` / thread pool for multiple sources
  - Graceful shutdown, retry logic with `tenacity`
- [ ] Create n8n workflow as alternative/backup trigger (HTTP webhook → pipeline)
- [ ] Integration test: full fetch cycle from config → DB

**Acceptance Criteria:**
- `make pipeline-run` fetches from 20+ RSS sources and stores items
- Deduplication works (running twice doesn't create duplicates)
- Source config is hot-reloadable (edit YAML → next cycle picks up changes)
- Structured logs show fetch results per source
- 95%+ unit test coverage on fetcher modules

---

## Sprint 2 — Gap Detection Engine

**Duration:** 5 days
**Goal:** AI-powered scoring system that measures significance vs. media coverage for each ingested item.

### Tasks

#### S2-T1: Significance Scorer
- [ ] Create `pipeline/gap_detection/significance.py`:
  - Takes a `raw_item` (title + content + metadata)
  - Sends to Claude Sonnet API with scoring prompt:
    ```
    You are an intelligence analyst scoring the significance of a news item.
    Score from 1-10 on these dimensions:
    - Impact scope: How many people does this affect? (1=few, 10=global)
    - Novelty: Does this reveal genuinely new information? (1=rehash, 10=breakthrough)
    - Power dynamics: Does this expose hidden actions by governments/corporations? (1=routine, 10=major exposure)
    - Historical weight: Will this matter in 5 years? (1=ephemeral, 10=historic)

    Provide an overall significance score (1-10) and a 2-sentence reasoning.
    Respond in JSON: {"score": float, "dimensions": {...}, "reasoning": "..."}
    ```
  - Batch processing: score up to 20 items per API call using system prompt
  - Cache scores in Redis (24h TTL) to avoid re-scoring
  - Cost optimization: only score items from last 48 hours that haven't been scored
- [ ] Unit tests with mocked Claude responses

#### S2-T2: Coverage Scorer
- [ ] Create `pipeline/gap_detection/coverage.py`:
  - For each `raw_item`, measures how much mainstream media coverage it received
  - Methods (in order of reliability):
    1. Google News API search for the topic → count results in last 7 days
    2. GDELT API query for related events/articles
    3. Fallback: Claude Sonnet estimates coverage based on its training data
  - Normalize to 1-10 scale:
    - 1-2: Almost zero coverage (only original source)
    - 3-4: Niche coverage (trade publications only)
    - 5-6: Moderate (some mainstream mentions)
    - 7-8: Well-covered (major outlets)
    - 9-10: Saturated (everyone is talking about it)
  - Output: `{"coverage_score": float, "method": "gdelt|google|claude", "sources_found": int}`
- [ ] Unit tests with mocked API responses

#### S2-T3: Gap Score Calculator
- [ ] Create `pipeline/gap_detection/gap_calculator.py`:
  - `gap_score = significance_score - coverage_score`
  - Filters: only items with `gap_score >= 4.0` are candidates
  - Additional boost factors:
    - +1.0 if primary source is a government document or court filing
    - +0.5 if topic relates to an active conflict
    - +0.5 if historical document was recently declassified
  - Ranking: sort all candidates by `gap_score` descending
  - Output: daily ranked list of top 20 gap stories
  - Store scores in `stories` table with `status = 'scored'`
- [ ] Unit tests for scoring logic and edge cases

#### S2-T4: Daily Scoring Pipeline
- [ ] Create `pipeline/gap_detection/daily_run.py`:
  - Orchestrates the full daily scoring:
    1. Fetch all unscored `raw_items` from last 48 hours
    2. Run significance scorer (batched, with rate limiting)
    3. Run coverage scorer (parallel, with rate limiting)
    4. Calculate gap scores
    5. Insert/update `stories` table
    6. Generate daily report (top 20 stories + reasoning)
    7. Send daily report to Telegram for founder review
  - Scheduled via cron: `0 6 * * *` (6 AM UTC daily)
  - Error handling: if Claude API fails, retry 3x then skip and log
- [ ] Integration test: feed sample data → get scored output

#### S2-T5: Founder Review Interface
- [ ] Create simple CLI tool `pipeline/gap_detection/review_cli.py`:
  - Shows today's top 20 scored stories with gap scores and reasoning
  - Founder can: `select` (move to `status = 'selected'`), `reject`, `defer`
  - Selected stories move to the content generation queue
  - Alternative: send interactive Telegram messages with inline buttons for approve/reject
- [ ] Create Telegram bot integration for story approval workflow

**Acceptance Criteria:**
- Daily pipeline scores 50+ items and surfaces top 20 gap stories
- Gap score correlates with editorial quality (manual review of top 10 matches founder's judgment >80% of the time)
- Full scoring run completes in <15 minutes
- Claude API costs for scoring stay under $5/day
- Telegram notification arrives daily with actionable story list

---

## Sprint 3 — Content Generation Pipeline

**Duration:** 5 days
**Goal:** From a selected story, auto-generate all content formats (newsletter article, video script, Twitter thread, Reddit post, Shorts script, Telegram drop).

### Tasks

#### S3-T1: Newsletter Article Generator
- [ ] Create `pipeline/content_gen/newsletter.py`:
  - Input: `story` record (with raw items, scores, reasoning)
  - Prompt engineering for Claude Opus:
    ```
    You are the editor of "Dead Drop" — a premium intelligence newsletter.
    Write a newsletter article about this story. Follow these rules:
    - Tone: Authoritative, accessible, occasionally dry wit. Never conspiratorial.
    - Structure: Hook (1 para) → Context (2-3 para) → The Revelation (3-5 para) → Historical Parallel (1-2 para) → Why It Matters Now (1 para)
    - Length: 800-1,200 words
    - ALWAYS cite primary sources with [Source: description](url)
    - NEVER say "they are hiding" — say "published with minimal coverage" or "buried on page X of Y"
    - NEVER make unverified claims without labeling them as "alleged" or "unconfirmed"
    - End with a thought-provoking question, not a CTA
    ```
  - Output → `content_outputs` table with `output_type = 'newsletter'`
- [ ] Quality check: Claude self-review pass for tone, sourcing, accuracy
- [ ] Unit test with sample story data

#### S3-T2: Video Script Generator
- [ ] Create `pipeline/content_gen/video_script.py`:
  - Input: same `story` record
  - Generates script with embedded visual cues:
    ```
    [HOOK - 15 sec]
    NARRATOR: "In 2024, the United Nations published a 400-page report on..."
    [FOOTAGE: UN headquarters exterior]
    [TEXT ON SCREEN: "Report No. A/HRC/55/73"]

    [CONTEXT - 2 min]
    NARRATOR: "To understand why this matters, we need to go back to..."
    [MAP: zoom into region, highlight conflict zone]
    [FOOTAGE: archival footage of related historical event]
    ...
    ```
  - Three template modes: `buried_report`, `forgotten_war`, `declassified`
  - Includes timing estimates per section
  - Output → `content_outputs` with `output_type = 'video_script'`
- [ ] Unit test per template

#### S3-T3: Twitter Thread Generator
- [ ] Create `pipeline/content_gen/twitter_thread.py`:
  - Input: `story` record + newsletter article (for consistency)
  - Generates 8-12 tweet thread:
    - Tweet 1: Hook — most shocking/surprising fact (max engagement)
    - Tweets 2-8: Progressive revelation with sources
    - Tweet 9: "So what" — why this matters today
    - Tweet 10: CTA — "I publish 5 stories like this every week → link in bio"
  - Character count validation (≤280 per tweet)
  - Emoji usage: minimal, strategic (🔍 for sources, 🧵 for thread indicator)
  - Output → `content_outputs` with `output_type = 'twitter_thread'`
- [ ] Unit test for character limits and format compliance

#### S3-T4: Reddit Post Generator
- [ ] Create `pipeline/content_gen/reddit_post.py`:
  - Input: `story` record
  - Generates long-form post optimized for target subreddits:
    - r/CredibleDefense style: academic tone, extensive sourcing, balanced analysis
    - r/geopolitics style: analytical, question-provoking
    - r/OSINT style: methodology-focused, tools mentioned
  - Includes subreddit-specific compliance (e.g., r/AskHistorians requires 20-year rule)
  - Output → `content_outputs` with `output_type = 'reddit_post'`

#### S3-T5: Shorts/TikTok Script & Telegram Drop
- [ ] Create `pipeline/content_gen/shorts_script.py`:
  - 60-90 second script with visual cues
  - Hook-first format optimized for retention
  - Output → `content_outputs` with `output_type = 'shorts_script'`
- [ ] Create `pipeline/content_gen/telegram_drop.py`:
  - One-paragraph summary (150 words max) with link to newsletter
  - Includes 2-3 relevant emoji/icons for Telegram styling
  - Output → `content_outputs` with `output_type = 'telegram'`

#### S3-T6: Content Generation Orchestrator
- [ ] Create `pipeline/content_gen/orchestrator.py`:
  - Takes a story with `status = 'selected'`
  - Runs all generators in parallel
  - Stores all outputs in `content_outputs`
  - Updates story `status = 'in_progress'`
  - Sends notification to Telegram with links to review all generated content
  - Cost tracking: log Claude API usage per story (target: <$0.50/story for all formats)

**Acceptance Criteria:**
- From one selected story, all 6 content formats generated in <3 minutes
- Newsletter article passes quality check (proper sourcing, tone, length)
- Twitter thread respects character limits
- Video script includes proper visual cue tags
- All outputs stored in DB with correct story association

---

## Sprint 4 — Verification Module

**Duration:** 3 days
**Goal:** Automated and semi-automated verification pipeline ensuring factual accuracy before publication.

### Tasks

#### S4-T1: Primary Source Verifier
- [ ] Create `pipeline/verification/source_check.py`:
  - Extracts all URLs from generated content
  - Verifies each URL is accessible (HTTP 200)
  - Checks if source is a primary document (government, court, official report) vs. secondary
  - Flags stories with no primary source link → blocks publication
  - Output: `verifications.primary_source_verified`, `primary_source_url`

#### S4-T2: Claim Cross-Reference
- [ ] Create `pipeline/verification/cross_ref.py`:
  - Extracts factual claims from the article using Claude
  - For each claim, searches for corroborating sources (web search API or pre-indexed sources)
  - Flags claims with <2 independent sources as "needs review"
  - Output: `verifications.claims_cross_referenced`, `cross_reference_notes`

#### S4-T3: Bias & Tone Checker
- [ ] Create `pipeline/verification/bias_check.py`:
  - Sends content to Claude with bias-detection prompt:
    ```
    Review this article for: conspiratorial language, one-sided framing,
    unattributed "they" pronouns, emotional manipulation, unsupported
    implications, and sensationalism. Flag any issues.
    ```
  - Checks for forbidden phrases: "they don't want you to know", "wake up", "sheeple", "cover-up" (without evidence), "mainstream media lies"
  - Output: `verifications.bias_check_passed`, `bias_check_notes`

#### S4-T4: Human Review Workflow
- [ ] Create `pipeline/verification/review_workflow.py`:
  - After automated checks pass, sends full content package to founder via Telegram:
    - Newsletter article (formatted)
    - Verification report (sources checked, claims verified, bias score)
    - Video script summary
    - Twitter thread preview
  - Founder responds: ✅ Approve / ✏️ Edit / ❌ Reject
  - On approve: story `status = 'verified'`, all content `status = 'approved'`
  - On reject: story `status = 'rejected'` with notes

**Acceptance Criteria:**
- Every story must pass all 4 verification checks before publication
- Automated checks complete in <2 minutes per story
- Human review workflow sends clean, readable Telegram messages
- Stories with blocked primary sources cannot proceed to publication

---

## Sprint 5 — Newsletter System

**Duration:** 4 days
**Goal:** beehiiv integration, newsletter template design, automated publishing.

### Tasks

#### S5-T1: beehiiv API Integration
- [ ] Create `pipeline/publishers/beehiiv.py`:
  - beehiiv API v2 integration (create post, update post, schedule)
  - HTML formatting from Markdown content
  - Sponsor block insertion (placeholder for ad network)
  - Schedule publishing (Mon/Wed/Fri at 7 AM EST)
  - Handle draft → review → publish flow

#### S5-T2: Newsletter Template Design
- [ ] Design HTML email template with Dead Drop branding:
  - Header: Dead Drop logo + edition # + date
  - Sponsor block (primary): logo + 2 lines + CTA
  - Lead story: full article with inline source links
  - "The Briefing": 3-4 short items (150-200 words each)
  - "From the Archives": one historical piece
  - "The Signal": 3 data points
  - Sponsor block (secondary): text-only
  - Footer: referral program CTA, social links
- [ ] Create reusable HTML template in `config/templates/newsletter.html`
- [ ] Test rendering across email clients (Litmus or manual Gmail/Outlook)

#### S5-T3: beehiiv Account Setup
- [ ] Set up beehiiv Scale account
- [ ] Configure custom domain: deaddrop.media
- [ ] Set up referral program (3 refs = bonus deep dive, 10 = Telegram access)
- [ ] Configure welcome email sequence (3-email onboarding)
- [ ] Set up subscriber segmentation (by pillar interest)

#### S5-T4: Newsletter Publishing Pipeline
- [ ] Create `pipeline/publishers/newsletter_publisher.py`:
  - Takes verified + approved `content_outputs` (newsletter type)
  - Applies template formatting
  - Inserts "The Briefing" items from other scored stories
  - Adds "From the Archives" and "The Signal" sections
  - Publishes to beehiiv as draft → sends preview to founder → founder approves → auto-publish on schedule
  - Logs publish confirmation and beehiiv post URL

**Acceptance Criteria:**
- Newsletter publishes automatically on Mon/Wed/Fri schedule
- Template renders correctly in Gmail, Outlook, Apple Mail
- Referral program functional
- beehiiv analytics accessible

---

## Sprint 6 — Video Production Pipeline

**Duration:** 7 days
**Goal:** Automated video production from script to published YouTube video.

### Tasks

#### S6-T1: ElevenLabs Integration
- [ ] Create `video/narration/elevenlabs_client.py`:
  - ElevenLabs API v3 integration
  - Create custom voice profile ("The Analyst" — deep, authoritative, measured)
  - Text-to-speech with emotional tags:
    ```python
    def generate_narration(script: str, voice_id: str) -> bytes:
        # Parse script for [EMPHASIS], [PAUSE], [DRAMATIC] tags
        # Convert to ElevenLabs audio tags
        # Generate audio, return WAV bytes
    ```
  - Segment narration by script sections (for timing synchronization)
  - Output: WAV file + timestamp JSON per section
- [ ] Test voice quality with sample scripts

#### S6-T2: Visual Asset Manager
- [ ] Create `video/assembly/asset_manager.py`:
  - Asset library organizer:
    ```
    video/assets/
    ├── footage/
    │   ├── intelligence/     # spy-related B-roll
    │   ├── conflicts/        # war footage, military
    │   ├── ai/              # tech, servers, robots
    │   ├── cyber/           # hacking, screens, networks
    │   └── historical/      # WWII, Cold War, archives
    ├── maps/                # pre-generated map templates
    ├── overlays/            # text templates, lower thirds
    └── music/               # background tracks by mood
    ```
  - Tag-based retrieval: `get_assets(tags=["wwii", "declassified"])`
  - Auto-download from public domain sources (Internet Archive, NARA)
  - Fallback to AI-generated images (DALL-E) when no matching footage exists
- [ ] Download initial asset library (50+ clips, organized by pillar)

#### S6-T3: Map Generator
- [ ] Create `video/maps/map_generator.py`:
  - Mapbox GL JS or Folium-based map generation
  - Templates: conflict zone highlight, troop movement arrows, country comparison, timeline map
  - Render to video segments (Selenium screenshot → image sequence → video)
  - Input: JSON config `{"center": [lat, lng], "zoom": 5, "highlights": ["Syria", "Iraq"], "style": "dark"}`
  - Output: MP4 segment (5-10 sec loop)

#### S6-T4: Video Assembler
- [ ] Create `video/assembly/assembler.py`:
  - Main assembly engine using MoviePy + FFmpeg:
    ```python
    def assemble_video(script: VideoScript, narration: AudioFile, assets: AssetPack) -> VideoFile:
        # 1. Parse script sections
        # 2. Align narration audio with sections
        # 3. For each section:
        #    - Select/generate visual (footage, map, text overlay)
        #    - Apply Ken Burns effect on stills
        #    - Add text overlays (burned-in captions)
        #    - Transition between sections (crossfade)
        # 4. Add background music (ducked under narration)
        # 5. Add intro/outro (Dead Drop branded)
        # 6. Export: 16:9 (YouTube), 9:16 (Shorts), 1:1 (Twitter)
    ```
  - Text overlay system: headline text, source citations, "CLASSIFIED" / "DECLASSIFIED" stamps
  - Subtitle/caption generation: auto from narration transcript, burned-in
  - Ken Burns: configurable pan/zoom on still images for visual interest
- [ ] Test with sample 5-minute video

#### S6-T5: Thumbnail Generator
- [ ] Create `video/thumbnails/thumbnail_gen.py`:
  - DALL-E API integration for documentary-style thumbnails
  - Template system: title text + background image + Dead Drop watermark
  - Generate 3 variants per video for A/B testing
  - Style: cinematic, dark tones, red accent, large readable text

#### S6-T6: Video Publishing
- [ ] Create `pipeline/publishers/youtube_publisher.py`:
  - YouTube Data API v3 integration
  - Upload video with: title, description (with newsletter link), tags, thumbnail
  - Auto-generate description with timestamps, sources, and subscribe CTA
  - Schedule publishing
- [ ] Create `pipeline/publishers/shorts_publisher.py`:
  - Extract 60-90 sec clips from full video based on script markers
  - Re-export in 9:16 format
  - Upload as YouTube Shorts with link to full video

#### S6-T7: Video Pipeline Orchestrator
- [ ] Create `video/pipeline.py`:
  - End-to-end orchestrator:
    1. Read approved video script from DB
    2. Generate narration (ElevenLabs)
    3. Select/generate visual assets
    4. Generate maps (if needed)
    5. Assemble full video
    6. Generate thumbnail variants
    7. Generate Shorts clips
    8. Upload to YouTube (draft)
    9. Notify founder for final review
  - Target: <2 hours from script to ready-for-review video
  - `make video-generate STORY_ID=xxx` CLI command

**Acceptance Criteria:**
- Full video generated from script in <2 hours
- AI narration sounds professional and natural
- Visual asset selection is contextually appropriate
- Subtitles/captions are accurate and readable
- YouTube upload works with proper metadata
- 3 Shorts clips auto-extracted per full video
- Founder review time: <30 minutes per video

---

## Sprint 7 — Social Distribution Engine

**Duration:** 4 days
**Goal:** Automated cross-posting to all social channels with platform-specific formatting.

### Tasks

#### S7-T1: Twitter/X Publisher
- [ ] Create `pipeline/publishers/twitter_publisher.py`:
  - Twitter API v2 integration
  - Post thread (sequential tweets with `reply_to`)
  - Auto-add media cards (image per key tweet)
  - Rate limiting and retry logic
  - Schedule: post threads at optimal times (8-10 AM EST for US audience)
  - Engagement tracking: likes, retweets, impressions via API

#### S7-T2: Reddit Publisher
- [ ] Create `pipeline/publishers/reddit_publisher.py`:
  - Reddit API (PRAW) integration
  - Post to multiple subreddits with subreddit-specific formatting
  - Respect subreddit rules (flair, title format, link/self post requirements)
  - Anti-spam: stagger posts across subreddits (15-30 min intervals)
  - Track karma and comments for engagement metrics

#### S7-T3: Telegram Publisher
- [ ] Create `pipeline/publishers/telegram_publisher.py`:
  - Telegram Bot API integration
  - Post to public channel (@DeadDropIntel)
  - Rich formatting: bold, links, inline preview
  - Pin important posts
  - Weekly digest compilation

#### S7-T4: Distribution Orchestrator
- [ ] Create `pipeline/publishers/orchestrator.py`:
  - Master publishing scheduler:
    ```
    Story approved → 
      T+0:  Newsletter published (beehiiv)
      T+1h: Twitter thread posted
      T+2h: Reddit posts (staggered across subreddits)
      T+2h: Telegram drop
      T+4h: YouTube video published
      T+4h: YouTube Shorts published
    ```
  - Retry logic for failed publishes
  - Status tracking in `content_outputs.status` and `published_url`
  - Daily summary to Telegram: what published, engagement metrics

**Acceptance Criteria:**
- All channels publish automatically after story approval
- Proper formatting per platform
- No rate limiting violations
- Publishing schedule is configurable
- Engagement metrics tracked in DB

---

## Sprint 8 — Web (Landing + Archive)

**Duration:** 4 days
**Goal:** Next.js website for deaddrop.media — landing page, content archive, SEO.

### Tasks

#### S8-T1: Next.js Project Setup
- [ ] Initialize Next.js 14 project in `web/` with App Router, TypeScript strict
- [ ] Configure Tailwind CSS with Dead Drop color palette
- [ ] Set up fonts: JetBrains Mono (headings), Inter (body)
- [ ] Create shared layout with navigation and footer

#### S8-T2: Landing Page
- [ ] Hero section: "The stories that fell through the cracks" + email capture
- [ ] Social proof: subscriber count, notable mentions
- [ ] Content preview: last 3 newsletter editions (titles + excerpts)
- [ ] Pillar showcase: 5 content pillars with icons and descriptions
- [ ] CTA: subscribe form (beehiiv embed or API integration)
- [ ] Mobile-responsive, dark theme matching brand

#### S8-T3: Archive Page
- [ ] Paginated list of all published newsletter editions
- [ ] Filter by pillar (Intelligence, Conflicts, AI, Cyber, Historical)
- [ ] Search functionality
- [ ] Each article page: full content + social sharing + subscribe CTA
- [ ] SEO: meta tags, OG images, structured data (Article schema)

#### S8-T4: SEO & Analytics
- [ ] Set up Plausible Analytics (self-hosted on ab-prod)
- [ ] Sitemap generation
- [ ] robots.txt
- [ ] OG image generation for social sharing
- [ ] Performance optimization: Core Web Vitals targets (LCP <2.5s, CLS <0.1)

**Acceptance Criteria:**
- Landing page converts visitors to newsletter signups at >5% rate
- Archive loads and renders correctly with 100+ articles
- SEO: pages indexed by Google within 1 week
- Mobile-first, responsive, fast

---

## Sprint 9 — Content Stockpile

**Duration:** 5 days
**Goal:** Create pre-launch content buffer: 15 newsletter editions, 6 YouTube videos, 10+ Twitter threads.

### Tasks

#### S9-T1: Run Pipeline on Real Sources
- [ ] Activate full source monitoring (100+ feeds)
- [ ] Run gap detection for 5 consecutive days
- [ ] Review and select top 15 stories for newsletter editions
- [ ] Select 6 strongest visual stories for YouTube videos

#### S9-T2: Generate & Edit Newsletter Editions
- [ ] Generate 15 newsletter articles via content pipeline
- [ ] Founder edits each article (target: 30 min per article)
- [ ] Run verification on all 15
- [ ] Format in beehiiv template
- [ ] Schedule first 2 weeks of publications

#### S9-T3: Produce YouTube Videos
- [ ] Generate 6 video scripts via pipeline
- [ ] Produce 6 full videos (8-20 min each)
- [ ] Generate thumbnails (3 per video)
- [ ] Create YouTube channel artwork and branding
- [ ] Upload 3 videos as unlisted (ready for launch day)

#### S9-T4: Prepare Social Content
- [ ] Generate 10+ Twitter threads (scheduled but not posted)
- [ ] Prepare 5+ Reddit posts per target subreddit
- [ ] Create 15+ Shorts/TikTok scripts
- [ ] Set up Telegram channel with welcome message

#### S9-T5: Brand Asset Creation
- [ ] Final logo design (vector + raster)
- [ ] Social media profile/banner images (Twitter, YouTube, Telegram, Reddit)
- [ ] beehiiv newsletter template finalized
- [ ] Video intro/outro (5-sec branded animation)
- [ ] Media kit (for future sponsors): audience demo, engagement metrics template

**Acceptance Criteria:**
- 15 newsletter editions ready (2 weeks of daily content + buffer)
- 6 YouTube videos produced and uploaded
- 10+ Twitter threads scheduled
- All brand assets created and deployed
- Content quality approved by founder

---

## Sprint 10 — Launch & Growth Infrastructure

**Duration:** 3 days
**Goal:** Analytics dashboards, referral program, ad network activation, launch execution.

### Tasks

#### S10-T1: Analytics Dashboard
- [ ] Grafana dashboard for pipeline metrics:
  - Sources monitored / items ingested per day
  - Gap scores distribution
  - Content generated per format
  - Claude API costs per day/week
  - Video production time per video
- [ ] beehiiv analytics review setup (open rates, CTR, growth)
- [ ] YouTube Analytics integration
- [ ] Twitter analytics tracking

#### S10-T2: Referral & Growth Setup
- [ ] beehiiv referral program configured and tested
- [ ] Referral rewards:
  - 3 referrals: exclusive "Deep Dive" edition
  - 10 referrals: Telegram community access
  - 25 referrals: name in newsletter credits
- [ ] Cross-promotion partnerships: reach out to 5 complementary newsletters
- [ ] beehiiv Boost enrollment (earn for recommending other newsletters)

#### S10-T3: Launch Execution
- [ ] Soft launch week (Week -1):
  - Post 3 Twitter threads (no newsletter mention yet)
  - Post on Reddit (value-first, no promotion)
  - Build initial engagement and following
- [ ] Launch day (Week 0):
  - Publish first newsletter edition
  - Release 3 YouTube videos simultaneously
  - Announce on all social channels
  - Post on relevant subreddits
  - Activate Telegram channel
- [ ] Launch week follow-up:
  - Daily Twitter threads
  - 2 more YouTube videos
  - 2 more newsletter editions
  - Monitor all metrics, respond to all comments/replies

#### S10-T4: Post-Launch Monitoring
- [ ] Set up alerting:
  - Pipeline failure alerts (Telegram)
  - Publishing failure alerts
  - Engagement anomaly detection (sudden spike or drop)
- [ ] Daily metrics review checklist for first 2 weeks
- [ ] Weekly retrospective template for continuous improvement

**Acceptance Criteria:**
- All analytics dashboards live and tracking
- Referral program tested end-to-end
- Launch checklist executed
- All channels live with content
- No critical bugs in first 48 hours post-launch

---

## Post-Launch Sprint Cadence

After launch, switch to 1-week sprints focused on:

| Week | Focus |
|------|-------|
| L+1 to L+4 | Iteration: optimize pipeline quality, fix edge cases, improve video production speed |
| L+5 to L+8 | Growth: paid acquisition testing (SparkLoop), sponsor outreach, collaboration with other creators |
| L+9 to L+12 | Monetization: activate beehiiv Ad Network, first direct sponsors, premium tier launch ($12/mo) |
| L+13 to L+16 | Scale: expand to 5x/week newsletter, podcast launch planning, hire part-time editor |
| L+17 to L+24 | Diversify: Discord/Slack community, digital products (OSINT toolkit), virtual briefings |

---

## Appendix: Key Commands

```bash
# Development
make dev                          # Start local Docker environment
make test                         # Run full test suite
make lint                         # Run all linters

# Pipeline
make pipeline-run                 # Run full pipeline cycle (fetch → score → generate)
make pipeline-score               # Run gap detection scoring only
make video-generate STORY_ID=123  # Generate video for specific story

# Database
make db-migrate                   # Run pending migrations
make db-backup                    # Backup PostgreSQL to file

# Deployment
make deploy                       # Full production deploy (backup → build → migrate → restart → verify)
make rollback                     # Emergency rollback to previous version
```

---

*This document is the development execution plan for Dead Drop PRD v1.0. Each sprint should be executed sequentially, with acceptance criteria verified before moving to the next sprint.*
