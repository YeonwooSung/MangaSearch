-- Manga Database Schema for ParadeDB with BM25 Search
-- ParadeDB provides PostgreSQL with BM25 full-text search capabilities

-- Enable pg_search extension for BM25 indexing
CREATE EXTENSION IF NOT EXISTS pg_search;

-- Enable UUID extension for better ID management (optional)
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Main manga table
CREATE TABLE manga (
    id BIGINT PRIMARY KEY,
    state VARCHAR(20) NOT NULL DEFAULT 'active',
    merged_with BIGINT REFERENCES manga(id),
    title TEXT NOT NULL,
    native_title TEXT,
    romanized_title TEXT,
    description TEXT,
    year INTEGER,
    status VARCHAR(20),
    is_licensed BOOLEAN DEFAULT FALSE,
    has_anime BOOLEAN DEFAULT FALSE,
    anime JSONB, -- Reference to anime if exists
    content_rating VARCHAR(20),
    type VARCHAR(20) NOT NULL DEFAULT 'manga',
    rating DECIMAL(3,1) CHECK (rating >= 0 AND rating <= 10),
    final_volume FLOAT,
    final_chapter FLOAT,
    total_chapters TEXT, -- Can be number or text like "ongoing"
    last_updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Computed search fields for BM25 indexing
    search_text TEXT GENERATED ALWAYS AS (
        COALESCE(title, '') || ' ' ||
        COALESCE(native_title, '') || ' ' ||
        COALESCE(romanized_title, '') || ' ' ||
        COALESCE(description, '')
    ) STORED,
    
    title_search TEXT GENERATED ALWAYS AS (
        COALESCE(title, '') || ' ' ||
        COALESCE(native_title, '') || ' ' ||
        COALESCE(romanized_title, '')
    ) STORED
);

-- Secondary titles table for multiple titles per manga
CREATE TABLE manga_secondary_titles (
    id SERIAL PRIMARY KEY,
    manga_id BIGINT NOT NULL REFERENCES manga(id) ON DELETE CASCADE,
    language_code VARCHAR(5) NOT NULL, -- 'en', 'ja', etc.
    title TEXT NOT NULL,
    type VARCHAR(20), -- 'official', 'unofficial', 'synonym', etc.
    note TEXT
);

-- Cover images table
CREATE TABLE manga_covers (
    id SERIAL PRIMARY KEY,
    manga_id BIGINT NOT NULL REFERENCES manga(id) ON DELETE CASCADE,
    type VARCHAR(20) NOT NULL, -- 'raw', 'default', 'small', 'medium', 'large'
    url TEXT NOT NULL,
    width INTEGER,
    height INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Authors table
CREATE TABLE authors (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Artists table  
CREATE TABLE artists (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Publishers table
CREATE TABLE publishers (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Genres table
CREATE TABLE genres (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Tags table
CREATE TABLE tags (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Junction tables for many-to-many relationships

-- Manga-Authors relationship
CREATE TABLE manga_authors (
    manga_id BIGINT NOT NULL REFERENCES manga(id) ON DELETE CASCADE,
    author_id INTEGER NOT NULL REFERENCES authors(id) ON DELETE CASCADE,
    PRIMARY KEY (manga_id, author_id)
);

-- Manga-Artists relationship
CREATE TABLE manga_artists (
    manga_id BIGINT NOT NULL REFERENCES manga(id) ON DELETE CASCADE,
    artist_id INTEGER NOT NULL REFERENCES artists(id) ON DELETE CASCADE,
    PRIMARY KEY (manga_id, artist_id)
);

-- Manga-Publishers relationship
CREATE TABLE manga_publishers (
    manga_id BIGINT NOT NULL REFERENCES manga(id) ON DELETE CASCADE,
    publisher_id INTEGER NOT NULL REFERENCES publishers(id) ON DELETE CASCADE,
    PRIMARY KEY (manga_id, publisher_id)
);

-- Manga-Genres relationship
CREATE TABLE manga_genres (
    manga_id BIGINT NOT NULL REFERENCES manga(id) ON DELETE CASCADE,
    genre_id INTEGER NOT NULL REFERENCES genres(id) ON DELETE CASCADE,
    PRIMARY KEY (manga_id, genre_id)
);

-- Manga-Tags relationship
CREATE TABLE manga_tags (
    manga_id BIGINT NOT NULL REFERENCES manga(id) ON DELETE CASCADE,
    tag_id INTEGER NOT NULL REFERENCES tags(id) ON DELETE CASCADE,
    PRIMARY KEY (manga_id, tag_id)
);

-- External links table
CREATE TABLE manga_links (
    id SERIAL PRIMARY KEY,
    manga_id BIGINT NOT NULL REFERENCES manga(id) ON DELETE CASCADE,
    url TEXT NOT NULL,
    link_type VARCHAR(50), -- 'official', 'reader', 'store', etc.
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Manga relationships (other manga relationships)
CREATE TABLE manga_relationships (
    id SERIAL PRIMARY KEY,
    manga_id BIGINT NOT NULL REFERENCES manga(id) ON DELETE CASCADE,
    related_manga_id BIGINT NOT NULL REFERENCES manga(id) ON DELETE CASCADE,
    relationship_type VARCHAR(20) NOT NULL, -- 'sequel', 'prequel', 'other', 'spin-off', etc.
    UNIQUE(manga_id, related_manga_id, relationship_type)
);

-- External sources table for tracking data from different sources
CREATE TABLE external_sources (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL UNIQUE, -- 'anilist', 'mangadex', 'myanimelist', etc.
    base_url TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Manga external source data
CREATE TABLE manga_external_sources (
    id SERIAL PRIMARY KEY,
    manga_id BIGINT NOT NULL REFERENCES manga(id) ON DELETE CASCADE,
    source_id INTEGER NOT NULL REFERENCES external_sources(id) ON DELETE CASCADE,
    external_id TEXT, -- ID on the external source
    rating DECIMAL(3,1),
    cover_url TEXT,
    last_updated_at TIMESTAMP WITH TIME ZONE,
    response_data JSONB, -- Store additional response data as JSON
    statistics JSONB, -- Store statistics data as JSON
    UNIQUE(manga_id, source_id)
);

-- =====================================
-- BM25 INDEXES FOR ADVANCED SEARCH
-- =====================================

CREATE INDEX manga_search_bm25_idx ON manga 
USING bm25 (id, search_text, title_search, description) 
WITH (key_field='id');

-- -- Main manga search index using BM25
-- CREATE INDEX manga_search_bm25_idx ON manga 
-- USING bm25 (id, search_text) 
-- WITH (key_field='id');

-- -- Title-specific search index
-- CREATE INDEX manga_title_search_bm25_idx ON manga 
-- USING bm25 (id, title_search) 
-- WITH (key_field='id');

-- -- Description search index
-- CREATE INDEX manga_description_bm25_idx ON manga 
-- USING bm25 (id, description) 
-- WITH (key_field='id');

-- Secondary titles search index
CREATE INDEX secondary_titles_search_bm25_idx ON manga_secondary_titles 
USING bm25 (id, title) 
WITH (key_field='id');

-- Author names search index
CREATE INDEX authors_search_bm25_idx ON authors 
USING bm25 (id, name) 
WITH (key_field='id');

-- =====================================
-- TRADITIONAL INDEXES FOR FILTERS
-- =====================================

-- Regular indexes for non-search queries
CREATE INDEX idx_manga_status ON manga(status);
CREATE INDEX idx_manga_type ON manga(type);
CREATE INDEX idx_manga_year ON manga(year);
CREATE INDEX idx_manga_rating ON manga(rating);
CREATE INDEX idx_manga_content_rating ON manga(content_rating);
CREATE INDEX idx_manga_updated_at ON manga(last_updated_at);
CREATE INDEX idx_manga_state ON manga(state);

CREATE INDEX idx_secondary_titles_manga_id ON manga_secondary_titles(manga_id);
CREATE INDEX idx_secondary_titles_language ON manga_secondary_titles(language_code);

CREATE INDEX idx_covers_manga_id ON manga_covers(manga_id);
CREATE INDEX idx_covers_type ON manga_covers(type);

CREATE INDEX idx_links_manga_id ON manga_links(manga_id);
CREATE INDEX idx_relationships_manga_id ON manga_relationships(manga_id);
CREATE INDEX idx_relationships_related_id ON manga_relationships(related_manga_id);
CREATE INDEX idx_relationships_type ON manga_relationships(relationship_type);

CREATE INDEX idx_external_sources_manga_id ON manga_external_sources(manga_id);
CREATE INDEX idx_external_sources_source_id ON manga_external_sources(source_id);
CREATE INDEX idx_external_sources_external_id ON manga_external_sources(external_id);

-- Composite indexes for common query patterns
CREATE INDEX idx_manga_rating_year ON manga(rating DESC, year DESC) WHERE rating IS NOT NULL;
CREATE INDEX idx_manga_status_type ON manga(status, type);
CREATE INDEX idx_manga_year_rating ON manga(year DESC, rating DESC) WHERE year IS NOT NULL;

-- =====================================
-- JSONB INDEXES FOR SOURCE DATA
-- =====================================

-- JSONB indexes for external source data
CREATE INDEX idx_external_response_data ON manga_external_sources USING gin(response_data);
CREATE INDEX idx_external_statistics ON manga_external_sources USING gin(statistics);

-- =====================================
-- FUNCTIONS AND TRIGGERS
-- =====================================

-- Functions for automatic timestamp updates
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Trigger for auto-updating updated_at field
CREATE TRIGGER update_manga_updated_at 
    BEFORE UPDATE ON manga 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- =====================================
-- SEARCH HELPER FUNCTIONS
-- =====================================

-- Function for comprehensive manga search with BM25 scoring
CREATE OR REPLACE FUNCTION search_manga(
    search_query TEXT,
    limit_count INTEGER DEFAULT 20,
    offset_count INTEGER DEFAULT 0
)
RETURNS TABLE (
    manga_id BIGINT,
    title TEXT,
    native_title TEXT,
    year INTEGER,
    rating DECIMAL(3,1),
    bm25_score REAL
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        m.id,
        m.title,
        m.native_title,
        m.year,
        m.rating,
        paradedb.score(m.id) as bm25_score
    FROM manga m
    WHERE m.search_text @@@ search_query
    ORDER BY paradedb.score(m.id) DESC
    LIMIT limit_count
    OFFSET offset_count;
END;
$$ LANGUAGE plpgsql;

-- Function for title-only search
CREATE OR REPLACE FUNCTION search_manga_titles(
    search_query TEXT,
    limit_count INTEGER DEFAULT 20
)
RETURNS TABLE (
    manga_id BIGINT,
    title TEXT,
    native_title TEXT,
    romanized_title TEXT,
    bm25_score REAL
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        m.id,
        m.title,
        m.native_title,
        m.romanized_title,
        paradedb.score(m.id) as bm25_score
    FROM manga m
    WHERE m.title_search @@@ search_query
    ORDER BY paradedb.score(m.id) DESC
    LIMIT limit_count;
END;
$$ LANGUAGE plpgsql;


-- Function for author search
CREATE OR REPLACE FUNCTION search_authors(
    search_query TEXT,
    limit_count INTEGER DEFAULT 10
)
RETURNS TABLE (
    author_id INTEGER,
    author_name TEXT,
    bm25_score REAL
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        a.id,
        a.name,
        paradedb.score(a.id) as bm25_score
    FROM authors a
    WHERE a.name @@@ search_query
    ORDER BY paradedb.score(a.id) DESC
    LIMIT limit_count;
END;
$$ LANGUAGE plpgsql;

-- =====================================
-- INITIAL DATA
-- =====================================

-- Insert base external sources
INSERT INTO external_sources (name, base_url) VALUES 
    ('anilist', 'https://anilist.co'),
    ('anime_news_network', 'https://www.animenewsnetwork.com'),
    ('mangadex', 'https://mangadex.org'),
    ('manga_updates', 'https://www.mangaupdates.com'),
    ('my_anime_list', 'https://myanimelist.net'),
    ('kitsu', 'https://kitsu.io')
ON CONFLICT (name) DO NOTHING;

-- =====================================
-- PERFORMANCE OPTIMIZATION SETTINGS
-- =====================================

-- Recommended settings for BM25 performance
-- (These should be set in postgresql.conf or via ALTER SYSTEM)

-- COMMENT: Add these to your postgresql.conf for better BM25 performance:
-- shared_preload_libraries = 'pg_search'
-- pg_search.enable_bm25 = on
-- pg_search.bm25_k1 = 1.2
-- pg_search.bm25_b = 0.75

-- =====================================
-- VIEWS FOR COMMON QUERIES
-- =====================================

-- View for manga with all related information
CREATE VIEW manga_complete AS
SELECT 
    m.*,
    COALESCE(
        json_agg(DISTINCT jsonb_build_object('id', a.id, 'name', a.name)) 
        FILTER (WHERE a.name IS NOT NULL), 
        '[]'::json
    ) as authors,
    COALESCE(
        json_agg(DISTINCT jsonb_build_object('id', ar.id, 'name', ar.name)) 
        FILTER (WHERE ar.name IS NOT NULL),
        '[]'::json
    ) as artists,
    COALESCE(
        json_agg(DISTINCT jsonb_build_object('id', g.id, 'name', g.name)) 
        FILTER (WHERE g.name IS NOT NULL),
        '[]'::json
    ) as genres,
    COALESCE(
        json_agg(DISTINCT jsonb_build_object('id', p.id, 'name', p.name)) 
        FILTER (WHERE p.name IS NOT NULL),
        '[]'::json
    ) as publishers,
    COALESCE(
        json_object_agg(mc.type, mc.url) FILTER (WHERE mc.type IS NOT NULL),
        '{}'::json
    ) as covers
FROM manga m
LEFT JOIN manga_authors ma ON m.id = ma.manga_id
LEFT JOIN authors a ON ma.author_id = a.id
LEFT JOIN manga_artists mar ON m.id = mar.manga_id  
LEFT JOIN artists ar ON mar.artist_id = ar.id
LEFT JOIN manga_genres mg ON m.id = mg.manga_id
LEFT JOIN genres g ON mg.genre_id = g.id
LEFT JOIN manga_publishers mp ON m.id = mp.manga_id
LEFT JOIN publishers p ON mp.publisher_id = p.id
LEFT JOIN manga_covers mc ON m.id = mc.manga_id
GROUP BY m.id;

-- =====================================
-- EXAMPLE USAGE COMMENTS
-- =====================================

/*
-- Example BM25 search queries:

-- Basic search across all text fields
SELECT * FROM search_manga('adventure fantasy');

-- Title-only search
SELECT * FROM search_manga_titles('naruto');

-- Direct BM25 search with custom scoring
SELECT 
    id, title, rating,
    paradedb.score(id) as relevance_score
FROM manga 
WHERE search_text @@@ 'romance school'
ORDER BY paradedb.score(id) DESC;

-- Combined search with filters
SELECT 
    m.id, m.title, m.rating,
    paradedb.score(m.id) as relevance_score
FROM manga m
WHERE m.search_text @@@ 'action'
    AND m.year >= 2020
    AND m.rating >= 8.0
ORDER BY paradedb.score(m.id) DESC, m.rating DESC;

-- Search with highlighting (if supported)
SELECT 
    id, title,
    paradedb.highlight(search_text, 'romance') as highlighted_text,
    paradedb.score(id) as score
FROM manga 
WHERE search_text @@@ 'romance'
ORDER BY paradedb.score(id) DESC;
*/