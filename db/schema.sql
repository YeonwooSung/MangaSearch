-- Manga Database Schema for PostgreSQL

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
    anime_id BIGINT, -- Reference to anime if exists
    content_rating VARCHAR(20),
    type VARCHAR(20) NOT NULL DEFAULT 'manga',
    rating DECIMAL(3,1) CHECK (rating >= 0 AND rating <= 10),
    final_volume INTEGER,
    final_chapter INTEGER,
    total_chapters TEXT, -- Can be number or text like "ongoing"
    last_updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
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

-- Indexes for better performance
CREATE INDEX idx_manga_title ON manga USING gin(to_tsvector('english', title));
CREATE INDEX idx_manga_native_title ON manga USING gin(to_tsvector('english', native_title));
CREATE INDEX idx_manga_description ON manga USING gin(to_tsvector('english', description));
CREATE INDEX idx_manga_status ON manga(status);
CREATE INDEX idx_manga_type ON manga(type);
CREATE INDEX idx_manga_year ON manga(year);
CREATE INDEX idx_manga_rating ON manga(rating);
CREATE INDEX idx_manga_content_rating ON manga(content_rating);
CREATE INDEX idx_manga_updated_at ON manga(last_updated_at);

CREATE INDEX idx_secondary_titles_manga_id ON manga_secondary_titles(manga_id);
CREATE INDEX idx_secondary_titles_language ON manga_secondary_titles(language_code);
CREATE INDEX idx_secondary_titles_text ON manga_secondary_titles USING gin(to_tsvector('english', title));

CREATE INDEX idx_covers_manga_id ON manga_covers(manga_id);
CREATE INDEX idx_covers_type ON manga_covers(type);

CREATE INDEX idx_links_manga_id ON manga_links(manga_id);
CREATE INDEX idx_relationships_manga_id ON manga_relationships(manga_id);
CREATE INDEX idx_relationships_related_id ON manga_relationships(related_manga_id);
CREATE INDEX idx_relationships_type ON manga_relationships(relationship_type);

CREATE INDEX idx_external_sources_manga_id ON manga_external_sources(manga_id);
CREATE INDEX idx_external_sources_source_id ON manga_external_sources(source_id);
CREATE INDEX idx_external_sources_external_id ON manga_external_sources(external_id);

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

-- Insert base external sources
INSERT INTO external_sources (name, base_url) VALUES 
    ('anilist', 'https://anilist.co'),
    ('anime_news_network', 'https://www.animenewsnetwork.com'),
    ('mangadex', 'https://mangadex.org'),
    ('manga_updates', 'https://www.mangaupdates.com'),
    ('my_anime_list', 'https://myanimelist.net'),
    ('kitsu', 'https://kitsu.io')
ON CONFLICT (name) DO NOTHING;
