-- ============================================================================
-- ParadeDB Fuzzy Search SQL Queries for Manga Database
-- Test these queries directly in psql
-- ============================================================================

-- ============================================================================
-- 1. BASIC PARADEDB SETUP VERIFICATION
-- ============================================================================

-- Check if ParadeDB extension is loaded
SELECT * FROM pg_extension WHERE extname = 'pg_search';

-- Verify BM25 indexes exist
SELECT 
    indexname, 
    tablename, 
    indexdef 
FROM pg_indexes 
WHERE indexdef LIKE '%bm25%' 
    AND tablename IN ('manga', 'authors', 'manga_secondary_titles');

-- Check search-related columns exist
\d manga;

-- ============================================================================
-- 2. BASIC BM25 SEARCH (No Fuzzy)
-- ============================================================================

-- Basic title search
SELECT 
    id, title, native_title, rating, year,
    paradedb.score(id) as bm25_score
FROM manga 
WHERE id @@@ paradedb.match('title_search', 'naruto')
ORDER BY paradedb.score(id) DESC
LIMIT 10;

-- Full-text search across all fields
SELECT 
    id, title, native_title, rating,
    paradedb.score(id) as bm25_score
FROM manga 
WHERE id @@@ paradedb.match('search_text', 'action adventure')
ORDER BY paradedb.score(id) DESC
LIMIT 10;

-- Description-only search
SELECT 
    id, title, 
    SUBSTR(description, 1, 100) as description_snippet,
    paradedb.score(id) as bm25_score
FROM manga 
WHERE id @@@ paradedb.match('description', 'magic school')
ORDER BY paradedb.score(id) DESC
LIMIT 10;

-- ============================================================================
-- 3. FUZZY SEARCH WITH PARADEDB.MATCH
-- ============================================================================

-- Basic fuzzy search - handle typos in "naruto"
SELECT 
    id, title, native_title, rating,
    paradedb.score(id) as bm25_score
FROM manga 
WHERE id @@@ paradedb.match('title_search', 'narto', fuzzy_distance => 2)
ORDER BY paradedb.score(id) DESC
LIMIT 10;

-- Fuzzy search for "one piece" with typo
SELECT 
    id, title, native_title, rating,
    paradedb.score(id) as bm25_score
FROM manga 
WHERE id @@@ paradedb.match('title_search', 'one peice', fuzzy_distance => 2)
ORDER BY paradedb.score(id) DESC
LIMIT 10;

-- Fuzzy search for "attack on titan" with typos
SELECT 
    id, title, native_title, rating,
    paradedb.score(id) as bm25_score
FROM manga 
WHERE id @@@ paradedb.match('title_search', 'attack on titna', fuzzy_distance => 3)
ORDER BY paradedb.score(id) DESC
LIMIT 10;

-- Fuzzy search in description field
SELECT 
    id, title, 
    SUBSTR(description, 1, 150) as description_snippet,
    paradedb.score(id) as bm25_score
FROM manga 
WHERE id @@@ paradedb.match('description', 'magik scool', fuzzy_distance => 3)
ORDER BY paradedb.score(id) DESC
LIMIT 10;

-- ============================================================================
-- 4. MULTI-FIELD FUZZY SEARCH
-- ============================================================================

-- Search across multiple fields with OR condition
SELECT 
    id, title, native_title, romanized_title,
    paradedb.score(id) as bm25_score,
    CASE 
        WHEN id @@@ paradedb.match('title_search', 'demon slyer', fuzzy_distance => 2) THEN 'title'
        WHEN id @@@ paradedb.match('description', 'demon slyer', fuzzy_distance => 2) THEN 'description'
        ELSE 'other'
    END as matched_field
FROM manga 
WHERE id @@@ paradedb.match('title_search', 'demon slyer', fuzzy_distance => 2)
   OR id @@@ paradedb.match('description', 'demon slyer', fuzzy_distance => 2)
ORDER BY paradedb.score(id) DESC
LIMIT 10;

-- Multi-field search with different fuzzy distances
SELECT 
    id, title, native_title,
    GREATEST(
        COALESCE((SELECT paradedb.score(m1.id) FROM manga m1 WHERE m1.id = manga.id AND m1.id @@@ paradedb.match('title_search', 'jujutsu kasen', fuzzy_distance => 2)), 0),
        COALESCE((SELECT paradedb.score(m2.id) FROM manga m2 WHERE m2.id = manga.id AND m2.id @@@ paradedb.match('description', 'jujutsu kasen', fuzzy_distance => 3)), 0)
    ) as max_score
FROM manga 
WHERE id @@@ paradedb.match('title_search', 'jujutsu kasen', fuzzy_distance => 2)
   OR id @@@ paradedb.match('description', 'jujutsu kasen', fuzzy_distance => 3)
ORDER BY max_score DESC
LIMIT 10;

-- ============================================================================
-- 5. FUZZY SEARCH COMBINED WITH POSTGRESQL SIMILARITY
-- ============================================================================

-- Enable pg_trgm extension for similarity function (if not already enabled)
-- CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- Combine ParadeDB fuzzy with PostgreSQL similarity
SELECT 
    id, title, native_title, rating,
    paradedb.score(id) as bm25_score,
    similarity(title, 'one piece') as title_similarity,
    COALESCE(similarity(native_title, 'one piece'), 0) as native_similarity,
    GREATEST(
        paradedb.score(id),
        similarity(title, 'one piece') * 10,
        COALESCE(similarity(native_title, 'one piece'), 0) * 8
    ) as combined_score
FROM manga 
WHERE id @@@ paradedb.match('title_search', 'one peice', fuzzy_distance => 2)
   OR similarity(title, 'one piece') > 0.3
   OR similarity(native_title, 'one piece') > 0.3
ORDER BY combined_score DESC
LIMIT 15;

-- Fuzzy search with minimum similarity threshold
SELECT 
    id, title, native_title,
    paradedb.score(id) as bm25_score,
    GREATEST(
        similarity(title, 'tokyo ghoul'),
        COALESCE(similarity(native_title, 'tokyo ghoul'), 0),
        COALESCE(similarity(romanized_title, 'tokyo ghoul'), 0)
    ) as best_similarity
FROM manga 
WHERE (id @@@ paradedb.match('title_search', 'tokyo goul', fuzzy_distance => 2)
   OR similarity(title, 'tokyo ghoul') > 0.4)
   AND GREATEST(
        similarity(title, 'tokyo ghoul'),
        COALESCE(similarity(native_title, 'tokyo ghoul'), 0),
        COALESCE(similarity(romanized_title, 'tokyo ghoul'), 0)
   ) > 0.3
ORDER BY bm25_score DESC, best_similarity DESC
LIMIT 10;

-- ============================================================================
-- 6. FUZZY SEARCH WITH FILTERING
-- ============================================================================

-- Fuzzy search with rating filter
SELECT 
    id, title, native_title, rating, year, status,
    paradedb.score(id) as bm25_score
FROM manga 
WHERE id @@@ paradedb.match('search_text', 'actoin adventur', fuzzy_distance => 3)
    AND rating >= 8.0
    AND status = 'completed'
ORDER BY paradedb.score(id) DESC
LIMIT 10;

-- Fuzzy search with year range
SELECT 
    id, title, year, rating,
    paradedb.score(id) as bm25_score
FROM manga 
WHERE id @@@ paradedb.match('title_search', 'my hero academi', fuzzy_distance => 2)
    AND year BETWEEN 2010 AND 2020
ORDER BY paradedb.score(id) DESC, rating DESC
LIMIT 10;

-- Fuzzy search with genre filtering
SELECT 
    m.id, m.title, m.rating,
    paradedb.score(m.id) as bm25_score,
    array_agg(g.name) as genres
FROM manga m
JOIN manga_genres mg ON m.id = mg.manga_id
JOIN genres g ON mg.genre_id = g.id
WHERE m.id @@@ paradedb.match('search_text', 'romanse scool', fuzzy_distance => 3)
    AND g.name IN ('Romance', 'School Life', 'Comedy')
GROUP BY m.id, m.title, m.rating
ORDER BY paradedb.score(m.id) DESC
LIMIT 10;

-- ============================================================================
-- 7. FUZZY SEARCH SUGGESTIONS (Auto-complete)
-- ============================================================================

-- Simple fuzzy suggestions
SELECT DISTINCT
    title,
    native_title,
    romanized_title,
    paradedb.score(id) as relevance_score
FROM manga
WHERE id @@@ paradedb.match('title_search', 'naru', fuzzy_distance => 2)
ORDER BY paradedb.score(id) DESC
LIMIT 10;

-- Advanced fuzzy suggestions with similarity
SELECT DISTINCT
    title,
    native_title,
    paradedb.score(id) as bm25_score,
    similarity(title, 'naru') as title_sim,
    CASE 
        WHEN title ILIKE 'naru%' THEN title
        WHEN native_title ILIKE '%naru%' THEN native_title
        WHEN romanized_title ILIKE '%naru%' THEN romanized_title
        ELSE title
    END as suggestion_text
FROM manga
WHERE id @@@ paradedb.match('title_search', 'naru', fuzzy_distance => 2)
   OR similarity(title, 'naru') > 0.3
   OR title ILIKE '%naru%'
ORDER BY bm25_score DESC, title_sim DESC
LIMIT 8;

-- ============================================================================
-- 8. FUZZY SEARCH WITH BOOSTING
-- ============================================================================

-- Boost exact matches over fuzzy matches
SELECT 
    id, title, native_title, rating,
    CASE
        WHEN title ILIKE '%one piece%' OR native_title ILIKE '%one piece%' THEN 10.0
        WHEN title ILIKE '%one%' AND title ILIKE '%piece%' THEN 8.0
        ELSE paradedb.score(id)
    END as boosted_score,
    paradedb.score(id) as original_score
FROM manga 
WHERE id @@@ paradedb.match('title_search', 'one peice', fuzzy_distance => 2)
   OR title ILIKE '%one piece%'
   OR native_title ILIKE '%one piece%'
ORDER BY boosted_score DESC
LIMIT 10;

-- Boost recent manga in fuzzy search
SELECT 
    id, title, year, rating,
    paradedb.score(id) as bm25_score,
    CASE 
        WHEN year >= 2020 THEN paradedb.score(id) * 1.5
        WHEN year >= 2015 THEN paradedb.score(id) * 1.2
        ELSE paradedb.score(id)
    END as year_boosted_score
FROM manga 
WHERE id @@@ paradedb.match('search_text', 'isekay fantasy', fuzzy_distance => 3)
ORDER BY year_boosted_score DESC
LIMIT 10;

-- ============================================================================
-- 9. COMPLEX FUZZY SEARCH SCENARIOS
-- ============================================================================

-- Search for "attack on titan" with various typos and language variations
WITH fuzzy_searches AS (
    SELECT id, 'exact_title' as match_type, paradedb.score(id) as score
    FROM manga WHERE id @@@ paradedb.match('title_search', 'attack on titan', fuzzy_distance => 0)
    
    UNION ALL
    
    SELECT id, 'fuzzy_title' as match_type, paradedb.score(id) as score
    FROM manga WHERE id @@@ paradedb.match('title_search', 'attack on titna', fuzzy_distance => 2)
    
    UNION ALL
    
    SELECT id, 'very_fuzzy' as match_type, paradedb.score(id) as score
    FROM manga WHERE id @@@ paradedb.match('title_search', 'atack titna', fuzzy_distance => 4)
    
    UNION ALL
    
    SELECT id, 'description' as match_type, paradedb.score(id) as score
    FROM manga WHERE id @@@ paradedb.match('description', 'giant humanoid', fuzzy_distance => 2)
)
SELECT 
    m.id, m.title, m.native_title, m.rating,
    fs.match_type,
    MAX(fs.score) as best_score
FROM manga m
JOIN fuzzy_searches fs ON m.id = fs.id
GROUP BY m.id, m.title, m.native_title, m.rating, fs.match_type
ORDER BY best_score DESC
LIMIT 15;

-- Multi-language fuzzy search
SELECT 
    id, title, native_title, romanized_title,
    GREATEST(
        COALESCE((SELECT paradedb.score(m1.id) FROM manga m1 WHERE m1.id = manga.id AND m1.id @@@ paradedb.match('title_search', 'demon slayer', fuzzy_distance => 1)), 0),
        COALESCE((SELECT paradedb.score(m2.id) FROM manga m2 WHERE m2.id = manga.id AND m2.id @@@ paradedb.match('title_search', 'kimetsu no yaiba', fuzzy_distance => 2)), 0),
        COALESCE((SELECT paradedb.score(m3.id) FROM manga m3 WHERE m3.id = manga.id AND m3.id @@@ paradedb.match('title_search', '鬼滅の刃', fuzzy_distance => 1)), 0)
    ) as best_score
FROM manga 
WHERE id @@@ paradedb.match('title_search', 'demon slayer', fuzzy_distance => 1)
   OR id @@@ paradedb.match('title_search', 'kimetsu no yaiba', fuzzy_distance => 2)
   OR id @@@ paradedb.match('title_search', '鬼滅の刃', fuzzy_distance => 1)
ORDER BY best_score DESC
LIMIT 10;

-- ============================================================================
-- 10. PERFORMANCE TESTING QUERIES
-- ============================================================================

-- Test query performance with EXPLAIN
EXPLAIN (ANALYZE, BUFFERS) 
SELECT id, title, paradedb.score(id) as score
FROM manga 
WHERE id @@@ paradedb.match('search_text', 'popular manga series', fuzzy_distance => 2)
ORDER BY paradedb.score(id) DESC
LIMIT 20;

-- Performance comparison: fuzzy vs exact
EXPLAIN (ANALYZE, BUFFERS)
SELECT 'exact' as search_type, COUNT(*) as result_count, AVG(paradedb.score(id)) as avg_score
FROM manga WHERE id @@@ paradedb.match('title_search', 'naruto', fuzzy_distance => 0)
UNION ALL
SELECT 'fuzzy' as search_type, COUNT(*) as result_count, AVG(paradedb.score(id)) as avg_score  
FROM manga WHERE id @@@ paradedb.match('title_search', 'naruto', fuzzy_distance => 3);

-- Index usage analysis
SELECT 
    schemaname, tablename, indexname, idx_scan, idx_tup_read, idx_tup_fetch
FROM pg_stat_user_indexes 
WHERE indexname LIKE '%bm25%'
ORDER BY idx_scan DESC;

-- ============================================================================
-- 11. DEBUGGING AND ANALYSIS QUERIES
-- ============================================================================

-- Analyze fuzzy search results with scoring details
SELECT 
    id, title, native_title,
    paradedb.score(id) as bm25_score,
    similarity(title, 'one piece') as title_similarity,
    levenshtein(title, 'one piece') as edit_distance,
    length(title) as title_length,
    CASE 
        WHEN title ILIKE '%one%' AND title ILIKE '%piece%' THEN 'partial_match'
        WHEN similarity(title, 'one piece') > 0.5 THEN 'high_similarity'
        WHEN paradedb.score(id) > 5.0 THEN 'high_bm25'
        ELSE 'low_match'
    END as match_quality
FROM manga 
WHERE id @@@ paradedb.match('title_search', 'one peice', fuzzy_distance => 2)
ORDER BY bm25_score DESC
LIMIT 20;

-- Find optimal fuzzy distance for specific queries
WITH distance_test AS (
    SELECT 0 as distance UNION SELECT 1 UNION SELECT 2 UNION SELECT 3 UNION SELECT 4
),
fuzzy_results AS (
    SELECT 
        dt.distance,
        COUNT(*) as result_count,
        AVG(paradedb.score(m.id)) as avg_score,
        MAX(paradedb.score(m.id)) as max_score
    FROM distance_test dt
    CROSS JOIN LATERAL (
        SELECT id FROM manga 
        WHERE id @@@ paradedb.match('title_search', 'narto', fuzzy_distance => dt.distance)
        LIMIT 100
    ) m
    GROUP BY dt.distance
)
SELECT * FROM fuzzy_results ORDER BY distance;

-- ============================================================================
-- 12. SAMPLE DATA FOR TESTING
-- ============================================================================

-- Insert sample data if needed for testing
/*
INSERT INTO manga (id, title, native_title, romanized_title, description, year, rating, status, type) VALUES
(1, 'One Piece', 'ワンピース', 'Wan Piisu', 'A story about pirates searching for treasure', 1997, 9.2, 'ongoing', 'manga'),
(2, 'Naruto', 'ナルト', 'Naruto', 'A young ninja seeks recognition from his peers', 1999, 8.7, 'completed', 'manga'),
(3, 'Attack on Titan', '進撃の巨人', 'Shingeki no Kyojin', 'Humanity fights against giant humanoid creatures', 2009, 9.0, 'completed', 'manga'),
(4, 'Demon Slayer', '鬼滅の刃', 'Kimetsu no Yaiba', 'A boy becomes a demon slayer to save his sister', 2016, 8.8, 'completed', 'manga'),
(5, 'My Hero Academia', '僕のヒーローアカデミア', 'Boku no Hero Academia', 'Students learn to become superheroes', 2014, 8.5, 'ongoing', 'manga');
*/

-- ============================================================================
-- 13. UTILITY QUERIES
-- ============================================================================

-- Check which manga have searchable text
SELECT 
    COUNT(*) as total_manga,
    COUNT(CASE WHEN title IS NOT NULL AND length(trim(title)) > 0 THEN 1 END) as with_title,
    COUNT(CASE WHEN description IS NOT NULL AND length(trim(description)) > 0 THEN 1 END) as with_description,
    COUNT(CASE WHEN native_title IS NOT NULL AND length(trim(native_title)) > 0 THEN 1 END) as with_native_title
FROM manga;

-- Find manga with special characters that might affect fuzzy search
SELECT id, title, native_title
FROM manga 
WHERE title ~ '[^\x00-\x7F]'  -- Non-ASCII characters
   OR native_title ~ '[^\x00-\x7F]'
LIMIT 10;

-- Test different tokenization patterns
SELECT 
    id, title,
    to_tsvector('english', title) as english_tokens,
    to_tsvector('simple', title) as simple_tokens
FROM manga 
WHERE title IS NOT NULL
LIMIT 5;

-- ============================================================================
-- 14. COMMON TYPO PATTERNS FOR TESTING
-- ============================================================================

-- Test common manga title typos
SELECT 'Testing Common Typos:' as test_description;

-- "Naruto" variations
SELECT 'Naruto variations:' as query_type, title, paradedb.score(id) as score
FROM manga WHERE id @@@ paradedb.match('title_search', 'narto', fuzzy_distance => 2)
UNION ALL
SELECT 'Naruto variations:' as query_type, title, paradedb.score(id) as score  
FROM manga WHERE id @@@ paradedb.match('title_search', 'nauto', fuzzy_distance => 2)
UNION ALL
SELECT 'Naruto variations:' as query_type, title, paradedb.score(id) as score
FROM manga WHERE id @@@ paradedb.match('title_search', 'narto', fuzzy_distance => 2)
ORDER BY score DESC;

-- "One Piece" variations  
SELECT 'One Piece variations:' as query_type, title, paradedb.score(id) as score
FROM manga WHERE id @@@ paradedb.match('title_search', 'one peice', fuzzy_distance => 2)
UNION ALL
SELECT 'One Piece variations:' as query_type, title, paradedb.score(id) as score
FROM manga WHERE id @@@ paradedb.match('title_search', 'onepiece', fuzzy_distance => 2)  
UNION ALL
SELECT 'One Piece variations:' as query_type, title, paradedb.score(id) as score
FROM manga WHERE id @@@ paradedb.match('title_search', 'won piece', fuzzy_distance => 2)
ORDER BY score DESC;

-- ============================================================================
-- 15. BATCH TESTING SCRIPT
-- ============================================================================

-- Create a function to test multiple fuzzy searches
CREATE OR REPLACE FUNCTION test_fuzzy_searches()
RETURNS TABLE(
    test_query TEXT,
    result_count BIGINT,
    avg_score NUMERIC,
    top_result TEXT
) AS $$
DECLARE
    test_queries TEXT[] := ARRAY[
        'narto',
        'one peice', 
        'attack on titna',
        'demon slyer',
        'my hero academi',
        'tokyo goul',
        'jujutsu kasen',
        'chainsaw mn'
    ];
    query_text TEXT;
BEGIN
    FOREACH query_text IN ARRAY test_queries LOOP
        RETURN QUERY
        SELECT 
            query_text as test_query,
            COUNT(*) as result_count,
            ROUND(AVG(paradedb.score(id))::NUMERIC, 2) as avg_score,
            (SELECT title FROM manga WHERE id @@@ paradedb.match('title_search', query_text, fuzzy_distance => 2) 
             ORDER BY paradedb.score(id) DESC LIMIT 1) as top_result
        FROM manga 
        WHERE id @@@ paradedb.match('title_search', query_text, fuzzy_distance => 2);
    END LOOP;
END;
$$ LANGUAGE plpgsql;

-- Run the batch test
SELECT * FROM test_fuzzy_searches();

-- Clean up
-- DROP FUNCTION IF EXISTS test_fuzzy_searches();
