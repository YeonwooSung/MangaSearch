-- ParadeDB BM25 Search Query Examples for Manga Database

-- =====================================
-- BASIC BM25 SEARCH QUERIES
-- =====================================

-- 1. Simple text search across all manga content
SELECT 
    m.id,
    m.title,
    m.native_title,
    m.rating,
    m.year,
    paradedb.score(m.id) as relevance_score
FROM manga m
WHERE m.search_text @@@ 'romance school life'
ORDER BY paradedb.score(m.id) DESC
LIMIT 10;

-- 2. Title-only search with BM25 scoring
SELECT 
    m.id,
    m.title,
    m.native_title,
    m.romanized_title,
    paradedb.score(m.id) as relevance_score
FROM manga m
WHERE m.title_search @@@ 'naruto'
ORDER BY paradedb.score(m.id) DESC;

-- 3. Using the search helper function
SELECT * FROM search_manga('adventure fantasy magic', 20, 0);

-- 4. Author search with BM25
SELECT * FROM search_authors('akira toriyama');

-- =====================================
-- ADVANCED BM25 SEARCH WITH FILTERS
-- =====================================

-- 5. Combined BM25 search with rating and year filters
SELECT 
    m.id,
    m.title,
    m.rating,
    m.year,
    m.status,
    paradedb.score(m.id) as relevance_score,
    array_agg(DISTINCT a.name) as authors,
    array_agg(DISTINCT g.name) as genres
FROM manga m
LEFT JOIN manga_authors ma ON m.id = ma.manga_id
LEFT JOIN authors a ON ma.author_id = a.id
LEFT JOIN manga_genres mg ON m.id = mg.manga_id
LEFT JOIN genres g ON mg.genre_id = g.id
WHERE m.search_text @@@ 'action adventure'
    AND m.year >= 2015
    AND m.rating >= 7.0
    AND m.status = 'completed'
GROUP BY m.id, m.title, m.rating, m.year, m.status
ORDER BY paradedb.score(m.id) DESC, m.rating DESC
LIMIT 15;

-- 6. Genre-specific search with BM25 relevance
SELECT 
    m.id,
    m.title,
    m.rating,
    paradedb.score(m.id) as relevance_score,
    array_agg(DISTINCT g.name) as genres
FROM manga m
JOIN manga_genres mg ON m.id = mg.manga_id
JOIN genres g ON mg.genre_id = g.id
WHERE m.search_text @@@ 'supernatural power'
    AND g.name IN ('Action', 'Supernatural', 'Seinen')
GROUP BY m.id, m.title, m.rating
ORDER BY paradedb.score(m.id) DESC
LIMIT 10;

-- 7. Multi-language title search
SELECT 
    m.id,
    m.title,
    m.native_title,
    m.romanized_title,
    paradedb.score(m.id) as title_score,
    COALESCE(
        array_agg(DISTINCT st.title) FILTER (WHERE st.title IS NOT NULL),
        ARRAY[]::text[]
    ) as alternative_titles
FROM manga m
LEFT JOIN manga_secondary_titles st ON m.id = st.manga_id
WHERE m.title_search @@@ 'attack titan'
    OR st.title @@@ 'attack titan'
GROUP BY m.id, m.title, m.native_title, m.romanized_title
ORDER BY paradedb.score(m.id) DESC;

-- =====================================
-- SEARCH WITH HIGHLIGHTING (if supported)
-- =====================================

-- 8. Search with text highlighting
SELECT 
    m.id,
    m.title,
    paradedb.highlight(m.search_text, 'romance school') as highlighted_description,
    paradedb.score(m.id) as relevance_score
FROM manga m
WHERE m.search_text @@@ 'romance school'
ORDER BY paradedb.score(m.id) DESC
LIMIT 5;

-- =====================================
-- COMPLEX SEARCH SCENARIOS
-- =====================================

-- 9. Search for manga by author name with content relevance
WITH author_search AS (
    SELECT 
        a.id as author_id,
        a.name as author_name,
        paradedb.score(a.id) as author_relevance
    FROM authors a
    WHERE a.name @@@ 'kentaro miura'
)
SELECT 
    m.id,
    m.title,
    m.rating,
    m.year,
    as_result.author_name,
    as_result.author_relevance,
    COALESCE(paradedb.score(m.id), 0) as content_relevance
FROM manga m
JOIN manga_authors ma ON m.id = ma.manga_id
JOIN author_search as_result ON ma.author_id = as_result.author_id
LEFT JOIN LATERAL (
    SELECT paradedb.score(m.id) 
    FROM manga m2 
    WHERE m2.id = m.id AND m2.search_text @@@ 'dark fantasy'
) scores ON true
ORDER BY as_result.author_relevance DESC, content_relevance DESC;

-- 10. Fuzzy search for titles with typos
SELECT 
    m.id,
    m.title,
    m.native_title,
    paradedb.score(m.id) as relevance_score,
    -- Calculate similarity for fuzzy matching
    similarity(m.title, 'One Peice') as title_similarity  -- Note: intentional typo
FROM manga m
WHERE m.title_search @@@ 'one piece'
    OR similarity(m.title, 'One Peice') > 0.3
ORDER BY paradedb.score(m.id) DESC, title_similarity DESC;

-- =====================================
-- ANALYTICS AND DISCOVERY QUERIES
-- =====================================

-- 11. Popular search terms analysis (for analytics)
SELECT 
    g.name as genre,
    COUNT(*) as manga_count,
    AVG(m.rating) as avg_rating,
    AVG(paradedb.score(m.id)) as avg_search_relevance
FROM manga m
JOIN manga_genres mg ON m.id = mg.manga_id
JOIN genres g ON mg.genre_id = g.id
WHERE m.search_text @@@ 'action'
GROUP BY g.name
ORDER BY avg_search_relevance DESC, avg_rating DESC;

-- 12. Content recommendation based on search similarity
WITH user_search AS (
    SELECT m.id, paradedb.score(m.id) as base_score
    FROM manga m
    WHERE m.search_text @@@ 'magic school academy'
    ORDER BY paradedb.score(m.id) DESC
    LIMIT 5
),
similar_content AS (
    SELECT 
        m.id,
        m.title,
        m.rating,
        paradedb.score(m.id) as similarity_score
    FROM manga m
    WHERE m.search_text @@@ 'fantasy adventure young protagonist'
        AND m.id NOT IN (SELECT id FROM user_search)
    ORDER BY paradedb.score(m.id) DESC
    LIMIT 10
)
SELECT * FROM similar_content
ORDER BY similarity_score DESC;

-- =====================================
-- FACETED SEARCH QUERIES
-- =====================================

-- 13. Faceted search with aggregated filters
WITH search_results AS (
    SELECT m.id, paradedb.score(m.id) as relevance_score
    FROM manga m
    WHERE m.search_text @@@ 'slice of life comedy'
)
SELECT 
    'year' as facet_type,
    m.year::text as facet_value,
    COUNT(*) as count,
    AVG(sr.relevance_score) as avg_relevance
FROM search_results sr
JOIN manga m ON sr.id = m.id
WHERE m.year IS NOT NULL
GROUP BY m.year

UNION ALL

SELECT 
    'genre' as facet_type,
    g.name as facet_value,
    COUNT(*) as count,
    AVG(sr.relevance_score) as avg_relevance
FROM search_results sr
JOIN manga m ON sr.id = m.id
JOIN manga_genres mg ON m.id = mg.manga_id
JOIN genres g ON mg.genre_id = g.id
GROUP BY g.name

UNION ALL

SELECT 
    'status' as facet_type,
    m.status as facet_value,
    COUNT(*) as count,
    AVG(sr.relevance_score) as avg_relevance
FROM search_results sr
JOIN manga m ON sr.id = m.id
WHERE m.status IS NOT NULL
GROUP BY m.status

ORDER BY facet_type, avg_relevance DESC;

-- =====================================
-- PERFORMANCE MONITORING QUERIES
-- =====================================

-- 14. Search performance analysis
EXPLAIN (ANALYZE, BUFFERS) 
SELECT 
    m.id,
    m.title,
    paradedb.score(m.id) as relevance_score
FROM manga m
WHERE m.search_text @@@ 'popular manga series'
ORDER BY paradedb.score(m.id) DESC
LIMIT 20;

-- 15. Index usage statistics
SELECT 
    schemaname,
    tablename,
    indexname,
    idx_tup_read,
    idx_tup_fetch
FROM pg_stat_user_indexes 
WHERE indexname LIKE '%bm25%'
ORDER BY idx_tup_read DESC;

-- =====================================
-- SPECIALIZED SEARCH FUNCTIONS
-- =====================================

-- 16. Create a comprehensive search function
CREATE OR REPLACE FUNCTION advanced_manga_search(
    search_text TEXT DEFAULT '',
    min_rating DECIMAL DEFAULT 0,
    max_rating DECIMAL DEFAULT 10,
    year_from INTEGER DEFAULT 1900,
    year_to INTEGER DEFAULT 2100,
    genres TEXT[] DEFAULT ARRAY[]::TEXT[],
    status_filter TEXT DEFAULT '',
    content_rating_filter TEXT DEFAULT '',
    limit_count INTEGER DEFAULT 20,
    offset_count INTEGER DEFAULT 0
)
RETURNS TABLE (
    manga_id BIGINT,
    title TEXT,
    native_title TEXT,
    year INTEGER,
    rating DECIMAL(3,1),
    status TEXT,
    relevance_score REAL,
    authors TEXT[],
    genres TEXT[]
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        m.id,
        m.title,
        m.native_title,
        m.year,
        m.rating,
        m.status,
        CASE 
            WHEN search_text != '' THEN paradedb.score(m.id)::REAL
            ELSE 0::REAL
        END as relevance_score,
        COALESCE(array_agg(DISTINCT a.name) FILTER (WHERE a.name IS NOT NULL), ARRAY[]::TEXT[]) as authors,
        COALESCE(array_agg(DISTINCT g.name) FILTER (WHERE g.name IS NOT NULL), ARRAY[]::TEXT[]) as genres
    FROM manga m
    LEFT JOIN manga_authors ma ON m.id = ma.manga_id
    LEFT JOIN authors a ON ma.author_id = a.id
    LEFT JOIN manga_genres mg ON m.id = mg.manga_id
    LEFT JOIN genres g ON mg.genre_id = g.id
    WHERE 
        (search_text = '' OR m.search_text @@@ search_text)
        AND m.rating BETWEEN min_rating AND max_rating
        AND COALESCE(m.year, 0) BETWEEN year_from AND year_to
        AND (array_length(genres, 1) IS NULL OR g.name = ANY(genres))
        AND (status_filter = '' OR m.status = status_filter)
        AND (content_rating_filter = '' OR m.content_rating = content_rating_filter)
    GROUP BY m.id, m.title, m.native_title, m.year, m.rating, m.status
    ORDER BY 
        CASE 
            WHEN search_text != '' THEN paradedb.score(m.id)
            ELSE m.rating
        END DESC NULLS LAST
    LIMIT limit_count
    OFFSET offset_count;
END;
$$ LANGUAGE plpgsql;

-- Example usage of the advanced search function:
-- SELECT * FROM advanced_manga_search(
--     search_text := 'action adventure',
--     min_rating := 7.0,
--     year_from := 2010,
--     genres := ARRAY['Action', 'Adventure'],
--     status_filter := 'completed',
--     limit_count := 10
-- );

-- =====================================
-- REAL-TIME SEARCH SUGGESTIONS
-- =====================================

-- 17. Auto-complete/suggestion query
WITH title_matches AS (
    SELECT 
        id, title, paradedb.score(id) as score
    FROM manga
    WHERE title_search @@@ 'naru'
    ORDER BY paradedb.score(id) DESC
    LIMIT 5
),
author_matches AS (
    SELECT 
        a.id, a.name, paradedb.score(a.id) as score
    FROM authors a
    WHERE a.name @@@ 'naru'
    ORDER BY paradedb.score(a.id) DESC
    LIMIT 3
)
SELECT 'manga' as type, title as suggestion, score
FROM title_matches
UNION ALL
SELECT 'author' as type, name as suggestion, score  
FROM author_matches
ORDER BY score DESC;

-- =====================================
-- SEARCH ANALYTICS QUERIES
-- =====================================

-- 18. Most relevant content by search term
SELECT 
    search_term,
    COUNT(*) as result_count,
    AVG(relevance_score) as avg_relevance,
    MAX(relevance_score) as max_relevance
FROM (
    SELECT 
        'romance' as search_term,
        paradedb.score(id) as relevance_score
    FROM manga 
    WHERE search_text @@@ 'romance'
    
    UNION ALL
    
    SELECT 
        'action' as search_term,
        paradedb.score(id) as relevance_score
    FROM manga 
    WHERE search_text @@@ 'action'
    
    UNION ALL
    
    SELECT 
        'fantasy' as search_term,
        paradedb.score(id) as relevance_score
    FROM manga 
    WHERE search_text @@@ 'fantasy'
) search_results
GROUP BY search_term
ORDER BY avg_relevance DESC;
