-- Useful query examples for the manga database

-- 1. Get complete manga information with all related data
SELECT 
    m.*,
    -- Authors
    COALESCE(
        json_agg(DISTINCT a.name) FILTER (WHERE a.name IS NOT NULL), 
        '[]'::json
    ) as authors,
    -- Artists  
    COALESCE(
        json_agg(DISTINCT ar.name) FILTER (WHERE ar.name IS NOT NULL),
        '[]'::json
    ) as artists,
    -- Genres
    COALESCE(
        json_agg(DISTINCT g.name) FILTER (WHERE g.name IS NOT NULL),
        '[]'::json
    ) as genres,
    -- Publishers
    COALESCE(
        json_agg(DISTINCT p.name) FILTER (WHERE p.name IS NOT NULL),
        '[]'::json
    ) as publishers,
    -- Cover images
    COALESCE(
        json_object_agg(mc.type, mc.url) FILTER (WHERE mc.type IS NOT NULL),
        '{}'::json
    ) as covers,
    -- External links
    COALESCE(
        json_agg(DISTINCT ml.url) FILTER (WHERE ml.url IS NOT NULL),
        '[]'::json
    ) as links
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
LEFT JOIN manga_links ml ON m.id = ml.manga_id
WHERE m.id = 119560
GROUP BY m.id;

-- 2. Search manga by title (full-text search)
SELECT 
    m.id,
    m.title,
    m.native_title,
    m.romanized_title,
    m.rating,
    m.year,
    m.status,
    array_agg(DISTINCT a.name) as authors,
    array_agg(DISTINCT g.name) as genres
FROM manga m
LEFT JOIN manga_authors ma ON m.id = ma.manga_id
LEFT JOIN authors a ON ma.author_id = a.id  
LEFT JOIN manga_genres mg ON m.id = mg.manga_id
LEFT JOIN genres g ON mg.genre_id = g.id
WHERE 
    to_tsvector('english', m.title || ' ' || COALESCE(m.native_title, '') || ' ' || COALESCE(m.romanized_title, '')) 
    @@ plainto_tsquery('english', 'Once')
GROUP BY m.id, m.title, m.native_title, m.romanized_title, m.rating, m.year, m.status
ORDER BY m.rating DESC;

-- 3. Get manga by genre
SELECT 
    m.id,
    m.title,
    m.rating,
    m.year,
    array_agg(DISTINCT a.name) as authors
FROM manga m
JOIN manga_genres mg ON m.id = mg.manga_id
JOIN genres g ON mg.genre_id = g.id
LEFT JOIN manga_authors ma ON m.id = ma.manga_id
LEFT JOIN authors a ON ma.author_id = a.id
WHERE g.name = 'Hentai'
GROUP BY m.id, m.title, m.rating, m.year
ORDER BY m.rating DESC;

-- 4. Get manga by author
SELECT 
    m.id,
    m.title,
    m.rating,
    m.year,
    m.status,
    array_agg(DISTINCT g.name) as genres
FROM manga m
JOIN manga_authors ma ON m.id = ma.manga_id
JOIN authors a ON ma.author_id = a.id
LEFT JOIN manga_genres mg ON m.id = mg.manga_id
LEFT JOIN genres g ON mg.genre_id = g.id
WHERE a.name = 'Mojarin'
GROUP BY m.id, m.title, m.rating, m.year, m.status
ORDER BY m.year DESC;

-- 5. Get external source information for a manga
SELECT 
    m.title,
    es.name as source_name,
    mes.external_id,
    mes.rating as source_rating,
    mes.cover_url,
    mes.last_updated_at,
    mes.response_data,
    mes.statistics
FROM manga m
JOIN manga_external_sources mes ON m.id = mes.manga_id
JOIN external_sources es ON mes.source_id = es.id
WHERE m.id = 119560;

-- 6. Get manga statistics and rankings
SELECT 
    COUNT(*) as total_manga,
    AVG(rating) as average_rating,
    COUNT(*) FILTER (WHERE status = 'completed') as completed_count,
    COUNT(*) FILTER (WHERE status = 'ongoing') as ongoing_count,
    COUNT(*) FILTER (WHERE is_licensed = true) as licensed_count
FROM manga;

-- 7. Top rated manga by genre
SELECT 
    g.name as genre,
    m.title,
    m.rating,
    m.year,
    array_agg(DISTINCT a.name) as authors
FROM manga m
JOIN manga_genres mg ON m.id = mg.manga_id
JOIN genres g ON mg.genre_id = g.id
LEFT JOIN manga_authors ma ON m.id = ma.manga_id
LEFT JOIN authors a ON ma.author_id = a.id
WHERE m.rating IS NOT NULL
GROUP BY g.name, m.id, m.title, m.rating, m.year
ORDER BY g.name, m.rating DESC;

-- 8. Find related manga
SELECT 
    m1.title as main_manga,
    mr.relationship_type,
    m2.title as related_manga,
    m2.rating as related_rating
FROM manga m1
JOIN manga_relationships mr ON m1.id = mr.manga_id
JOIN manga m2 ON mr.related_manga_id = m2.id
WHERE m1.id = 119560;

-- 9. Recent updates
SELECT 
    m.id,
    m.title,
    m.last_updated_at,
    array_agg(DISTINCT a.name) as authors,
    array_agg(DISTINCT g.name) as genres
FROM manga m
LEFT JOIN manga_authors ma ON m.id = ma.manga_id
LEFT JOIN authors a ON ma.author_id = a.id
LEFT JOIN manga_genres mg ON m.id = mg.manga_id  
LEFT JOIN genres g ON mg.genre_id = g.id
WHERE m.last_updated_at >= CURRENT_DATE - INTERVAL '7 days'
GROUP BY m.id, m.title, m.last_updated_at
ORDER BY m.last_updated_at DESC;

-- 10. Complex search with filters
SELECT 
    m.id,
    m.title,
    m.rating,
    m.year,
    m.content_rating,
    array_agg(DISTINCT a.name) as authors,
    array_agg(DISTINCT g.name) as genres
FROM manga m
LEFT JOIN manga_authors ma ON m.id = ma.manga_id
LEFT JOIN authors a ON ma.author_id = a.id
LEFT JOIN manga_genres mg ON m.id = mg.manga_id
LEFT JOIN genres g ON mg.genre_id = g.id
WHERE 
    m.year BETWEEN 2015 AND 2025
    AND m.rating >= 7.0
    AND m.status = 'completed'
    AND m.is_licensed = true
GROUP BY m.id, m.title, m.rating, m.year, m.content_rating
ORDER BY m.rating DESC
LIMIT 10;
