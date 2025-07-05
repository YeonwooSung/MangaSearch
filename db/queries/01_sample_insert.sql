-- Example: Insert the provided JSON data into the schema

-- 1. Insert main manga record
INSERT INTO manga (
    id, state, merged_with, title, native_title, romanized_title, 
    description, year, status, is_licensed, has_anime, anime_id,
    content_rating, type, rating, final_volume, final_chapter, 
    total_chapters, last_updated_at
) VALUES (
    119560,
    'active',
    NULL,
    'Just Once',
    '1回だけ',
    '1-kai dake',
    'A night of engaging in dangerous play. ♥♥<br><br>(Source: fakku)<br><br><i>Note: Published in Comic Kairakuten 2018-08</i>',
    2018,
    'completed',
    true,
    false,
    NULL,
    'pornographic',
    'manga',
    7.2,
    NULL,
    NULL,
    '1',
    '2025-07-04T20:12:46.264+00:00'::timestamp with time zone
) ON CONFLICT (id) DO UPDATE SET
    state = EXCLUDED.state,
    title = EXCLUDED.title,
    native_title = EXCLUDED.native_title,
    romanized_title = EXCLUDED.romanized_title,
    description = EXCLUDED.description,
    year = EXCLUDED.year,
    status = EXCLUDED.status,
    is_licensed = EXCLUDED.is_licensed,
    has_anime = EXCLUDED.has_anime,
    content_rating = EXCLUDED.content_rating,
    rating = EXCLUDED.rating,
    total_chapters = EXCLUDED.total_chapters,
    last_updated_at = EXCLUDED.last_updated_at,
    updated_at = CURRENT_TIMESTAMP;

-- 2. Insert secondary titles
INSERT INTO manga_secondary_titles (manga_id, language_code, title, type, note)
VALUES (119560, 'en', 'Just Once', 'unofficial', NULL)
ON CONFLICT DO NOTHING;

-- 3. Insert cover images
INSERT INTO manga_covers (manga_id, type, url) VALUES
    (119560, 'raw', 'https://s4.anilist.co/file/anilistcdn/media/manga/cover/large/bx119057-c5DD1ZzoG6Y0.jpg'),
    (119560, 'default', 'https://cdn.mangabaka.dev/0x350,q90,s4qHFwvKmnRqJucpYS4s6aYdj-ou7lpSvA_fMzYlLtfE=/https://s4.anilist.co/file/anilistcdn/media/manga/cover/large/bx119057-c5DD1ZzoG6Y0.jpg'),
    (119560, 'small', 'https://cdn.mangabaka.dev/0x250,q90,sDMq7WkUuOSu0uQp0UVWhtqO68yVyjVtaq9IcUp5Xqkc=/https://s4.anilist.co/file/anilistcdn/media/manga/cover/large/bx119057-c5DD1ZzoG6Y0.jpg')
ON CONFLICT DO NOTHING;

-- 4. Insert authors
INSERT INTO authors (name) VALUES ('Mojarin') ON CONFLICT (name) DO NOTHING;

-- 5. Insert artists  
INSERT INTO artists (name) VALUES ('Mojarin') ON CONFLICT (name) DO NOTHING;

-- 6. Insert genres
INSERT INTO genres (name) VALUES ('Hentai') ON CONFLICT (name) DO NOTHING;

-- 7. Link manga with authors
INSERT INTO manga_authors (manga_id, author_id)
SELECT 119560, id FROM authors WHERE name = 'Mojarin'
ON CONFLICT DO NOTHING;

-- 8. Link manga with artists
INSERT INTO manga_artists (manga_id, artist_id)
SELECT 119560, id FROM artists WHERE name = 'Mojarin'
ON CONFLICT DO NOTHING;

-- 9. Link manga with genres
INSERT INTO manga_genres (manga_id, genre_id)
SELECT 119560, id FROM genres WHERE name = 'Hentai'
ON CONFLICT DO NOTHING;

-- 10. Insert external links
INSERT INTO manga_links (manga_id, url, link_type) VALUES
    (119560, 'https://www.fakku.net/hentai/just-once-english-1531513403', 'store'),
    (119560, 'https://mangabaka.dev/119560', 'reader')
ON CONFLICT DO NOTHING;

-- 11. Insert relationships (other manga)
-- First ensure the related manga exists or handle appropriately
INSERT INTO manga_relationships (manga_id, related_manga_id, relationship_type)
VALUES (119560, 119236, 'other')
ON CONFLICT DO NOTHING;

-- 12. Insert external source data
INSERT INTO manga_external_sources (
    manga_id, source_id, external_id, rating, cover_url, 
    last_updated_at, response_data, statistics
)
SELECT 
    119560,
    es.id,
    CASE es.name
        WHEN 'anilist' THEN '119057'
        ELSE NULL
    END,
    CASE es.name
        WHEN 'anilist' THEN 7.2
        ELSE NULL
    END,
    NULL, -- cover_url is null in the source data
    NULL, -- last_updated_at is null in the source data
    NULL, -- response is null in the source data
    CASE es.name
        WHEN 'mangadex' THEN NULL::jsonb -- statistics field only exists for mangadex
        ELSE NULL
    END
FROM external_sources es
WHERE es.name IN ('anilist', 'anime_news_network', 'mangadex', 'manga_updates', 'my_anime_list', 'kitsu')
ON CONFLICT (manga_id, source_id) DO UPDATE SET
    external_id = EXCLUDED.external_id,
    rating = EXCLUDED.rating,
    cover_url = EXCLUDED.cover_url,
    last_updated_at = EXCLUDED.last_updated_at,
    response_data = EXCLUDED.response_data,
    statistics = EXCLUDED.statistics;
