-- Migration: 001_initial_schema.sql
-- Description: Create initial database schema for Dead Drop

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
CREATE INDEX idx_content_outputs_story_id ON content_outputs(story_id);
CREATE INDEX idx_content_outputs_status ON content_outputs(status);
CREATE INDEX idx_verifications_story_id ON verifications(story_id);
