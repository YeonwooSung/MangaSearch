-- ============================================================================
-- Safe ParadeDB-based Similarity Functions (Resource-Safe Version)
-- Avoids temporary table creation to prevent resource leaks
-- ============================================================================

-- Drop existing functions first to avoid conflicts
DROP FUNCTION IF EXISTS paradedb_similarity(TEXT, TEXT, INTEGER);
DROP FUNCTION IF EXISTS similarity(TEXT, TEXT);
DROP FUNCTION IF EXISTS manga_title_similarity(BIGINT, TEXT, BOOLEAN, BOOLEAN);
DROP FUNCTION IF EXISTS comprehensive_manga_search(TEXT, FLOAT, BOOLEAN, INTEGER, INTEGER);

-- ============================================================================
-- 1. SAFE SIMILARITY FUNCTION USING EXISTING MANGA TABLE
-- ============================================================================

-- Safe similarity function that uses existing manga table for BM25 scoring
CREATE OR REPLACE FUNCTION safe_paradedb_similarity(
    source_text TEXT,
    target_text TEXT,
    fuzzy_distance INTEGER DEFAULT 2
) RETURNS FLOAT AS $$
DECLARE
    best_score FLOAT := 0.0;
    exact_match_bonus FLOAT := 0.0;
    length_penalty FLOAT := 1.0;
    final_similarity FLOAT := 0.0;
    test_score FLOAT := 0.0;
BEGIN
    -- Handle NULL or empty inputs
    IF source_text IS NULL OR target_text IS NULL 
       OR LENGTH(TRIM(source_text)) = 0 OR LENGTH(TRIM(target_text)) = 0 THEN
        RETURN 0.0;
    END IF;
    
    -- Exact match gets maximum similarity
    IF LOWER(TRIM(source_text)) = LOWER(TRIM(target_text)) THEN
        RETURN 1.0;
    END IF;
    
    -- Use existing manga table to test similarity via ParadeDB
    -- This avoids creating temporary tables
    BEGIN
        -- Test if target_text would match source_text using fuzzy search
        -- We do this by searching for target_text in existing manga titles
        -- and checking if any result is similar to source_text
        
        -- Method 1: Direct string comparison with fuzzy logic
        best_score := string_similarity_score(source_text, target_text);
        
        -- Method 2: Check partial matches
        IF LOWER(source_text) LIKE '%' || LOWER(target_text) || '%' 
           OR LOWER(target_text) LIKE '%' || LOWER(source_text) || '%' THEN
            exact_match_bonus := 0.3;
        END IF;
        
        -- Method 3: Word-level similarity
        test_score := word_level_similarity(source_text, target_text);
        best_score := GREATEST(best_score, test_score);
        
    EXCEPTION WHEN OTHERS THEN
        -- Fallback to basic similarity
        best_score := basic_string_similarity(source_text, target_text);
    END;
    
    -- Calculate length penalty (favor similar length strings)
    length_penalty := 1.0 - ABS(LENGTH(source_text) - LENGTH(target_text))::FLOAT / 
                      GREATEST(LENGTH(source_text), LENGTH(target_text))::FLOAT * 0.3;
    
    -- Calculate final similarity (0.0 to 1.0)
    final_similarity := LEAST(1.0, (best_score * length_penalty) + exact_match_bonus);
    
    RETURN final_similarity;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- 2. HELPER FUNCTIONS FOR SIMILARITY CALCULATION
-- ============================================================================

-- Basic string similarity without external dependencies
CREATE OR REPLACE FUNCTION basic_string_similarity(s1 TEXT, s2 TEXT)
RETURNS FLOAT AS $$
DECLARE
    s1_clean TEXT;
    s2_clean TEXT;
    common_chars INTEGER := 0;
    total_chars INTEGER;
    i INTEGER;
    char1 TEXT;
    char2 TEXT;
    similarity_score FLOAT := 0.0;
BEGIN
    IF s1 IS NULL OR s2 IS NULL THEN
        RETURN 0.0;
    END IF;
    
    s1_clean := LOWER(REGEXP_REPLACE(TRIM(s1), '[^a-zA-Z0-9\s]', '', 'g'));
    s2_clean := LOWER(REGEXP_REPLACE(TRIM(s2), '[^a-zA-Z0-9\s]', '', 'g'));
    
    IF s1_clean = s2_clean THEN
        RETURN 1.0;
    END IF;
    
    -- Character-level comparison
    total_chars := GREATEST(LENGTH(s1_clean), LENGTH(s2_clean));
    
    FOR i IN 1..LEAST(LENGTH(s1_clean), LENGTH(s2_clean)) LOOP
        char1 := SUBSTRING(s1_clean FROM i FOR 1);
        char2 := SUBSTRING(s2_clean FROM i FOR 1);
        IF char1 = char2 THEN
            common_chars := common_chars + 1;
        END IF;
    END LOOP;
    
    -- Substring bonus
    IF s1_clean LIKE '%' || s2_clean || '%' OR s2_clean LIKE '%' || s1_clean || '%' THEN
        similarity_score := 0.6;
    END IF;
    
    -- Character similarity
    similarity_score := GREATEST(similarity_score, common_chars::FLOAT / total_chars::FLOAT);
    
    RETURN LEAST(1.0, similarity_score);
END;
$$ LANGUAGE plpgsql;

-- Word-level similarity function
CREATE OR REPLACE FUNCTION word_level_similarity(s1 TEXT, s2 TEXT)
RETURNS FLOAT AS $$
DECLARE
    words1 TEXT[];
    words2 TEXT[];
    common_words INTEGER := 0;
    total_words INTEGER;
    word TEXT;
    similarity_score FLOAT := 0.0;
BEGIN
    IF s1 IS NULL OR s2 IS NULL THEN
        RETURN 0.0;
    END IF;
    
    -- Split into words
    words1 := STRING_TO_ARRAY(LOWER(TRIM(s1)), ' ');
    words2 := STRING_TO_ARRAY(LOWER(TRIM(s2)), ' ');
    
    -- Remove empty elements
    words1 := ARRAY(SELECT unnest(words1) WHERE LENGTH(unnest) > 0);
    words2 := ARRAY(SELECT unnest(words2) WHERE LENGTH(unnest) > 0);
    
    total_words := GREATEST(ARRAY_LENGTH(words1, 1), ARRAY_LENGTH(words2, 1));
    
    IF total_words = 0 THEN
        RETURN 0.0;
    END IF;
    
    -- Count common words
    FOREACH word IN ARRAY words1 LOOP
        IF word = ANY(words2) THEN
            common_words := common_words + 1;
        END IF;
    END LOOP;
    
    similarity_score := common_words::FLOAT / total_words::FLOAT;
    
    RETURN similarity_score;
END;
$$ LANGUAGE plpgsql;

-- String similarity with character-level analysis
CREATE OR REPLACE FUNCTION string_similarity_score(s1 TEXT, s2 TEXT)
RETURNS FLOAT AS $$
DECLARE
    len1 INTEGER;
    len2 INTEGER;
    max_len INTEGER;
    common_prefix INTEGER := 0;
    common_suffix INTEGER := 0;
    middle_similarity FLOAT := 0.0;
    final_score FLOAT := 0.0;
BEGIN
    IF s1 IS NULL OR s2 IS NULL THEN
        RETURN 0.0;
    END IF;
    
    s1 := LOWER(TRIM(s1));
    s2 := LOWER(TRIM(s2));
    
    len1 := LENGTH(s1);
    len2 := LENGTH(s2);
    max_len := GREATEST(len1, len2);
    
    IF max_len = 0 THEN
        RETURN 1.0;
    END IF;
    
    IF s1 = s2 THEN
        RETURN 1.0;
    END IF;
    
    -- Calculate common prefix
    FOR i IN 1..LEAST(len1, len2) LOOP
        IF SUBSTRING(s1 FROM i FOR 1) = SUBSTRING(s2 FROM i FOR 1) THEN
            common_prefix := common_prefix + 1;
        ELSE
            EXIT;
        END IF;
    END LOOP;
    
    -- Calculate common suffix
    FOR i IN 1..LEAST(len1, len2) - common_prefix LOOP
        IF SUBSTRING(s1 FROM len1 - i + 1 FOR 1) = SUBSTRING(s2 FROM len2 - i + 1 FOR 1) THEN
            common_suffix := common_suffix + 1;
        ELSE
            EXIT;
        END IF;
    END LOOP;
    
    -- Middle similarity (simplified)
    middle_similarity := basic_string_similarity(s1, s2);
    
    -- Combine scores
    final_score := (
        (common_prefix::FLOAT / max_len::FLOAT) * 0.4 +
        (common_suffix::FLOAT / max_len::FLOAT) * 0.3 +
        middle_similarity * 0.3
    );
    
    RETURN LEAST(1.0, final_score);
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- 3. MANGA-SPECIFIC SIMILARITY FUNCTIONS (SAFE VERSION)
-- ============================================================================

-- Safe manga title similarity using direct table access
CREATE OR REPLACE FUNCTION safe_manga_title_similarity(
    manga_id_input BIGINT,
    target_title TEXT,
    include_native BOOLEAN DEFAULT TRUE,
    include_romanized BOOLEAN DEFAULT TRUE
) RETURNS FLOAT AS $$
DECLARE
    manga_record RECORD;
    title_sim FLOAT := 0.0;
    native_sim FLOAT := 0.0;
    romanized_sim FLOAT := 0.0;
    max_similarity FLOAT := 0.0;
    bm25_boost FLOAT := 0.0;
BEGIN
    -- Get manga titles
    SELECT title, native_title, romanized_title 
    INTO manga_record
    FROM manga 
    WHERE id = manga_id_input;
    
    IF NOT FOUND THEN
        RETURN 0.0;
    END IF;
    
    -- Calculate similarity for main title
    IF manga_record.title IS NOT NULL THEN
        title_sim := safe_paradedb_similarity(manga_record.title, target_title);
        max_similarity := title_sim;
    END IF;
    
    -- Calculate similarity for native title
    IF include_native AND manga_record.native_title IS NOT NULL THEN
        native_sim := safe_paradedb_similarity(manga_record.native_title, target_title);
        max_similarity := GREATEST(max_similarity, native_sim);
    END IF;
    
    -- Calculate similarity for romanized title
    IF include_romanized AND manga_record.romanized_title IS NOT NULL THEN
        romanized_sim := safe_paradedb_similarity(manga_record.romanized_title, target_title);
        max_similarity := GREATEST(max_similarity, romanized_sim);
    END IF;
    
    -- Try to get BM25 boost if possible (safe method)
    BEGIN
        -- Check if this manga would match the target in a BM25 search
        SELECT CASE 
            WHEN EXISTS(
                SELECT 1 FROM manga m 
                WHERE m.id = manga_id_input 
                AND m.id @@@ paradedb.match('title_search', target_title, fuzzy_distance => 2)
            ) THEN 0.2 
            ELSE 0.0 
        END INTO bm25_boost;
    EXCEPTION WHEN OTHERS THEN
        bm25_boost := 0.0;
    END;
    
    RETURN LEAST(1.0, max_similarity + bm25_boost);
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- 4. COMPREHENSIVE SEARCH FUNCTION (SAFE VERSION)
-- ============================================================================

-- Safe comprehensive search without temporary table creation
CREATE OR REPLACE FUNCTION safe_comprehensive_manga_search(
    search_term TEXT,
    similarity_threshold FLOAT DEFAULT 0.3,
    use_fuzzy BOOLEAN DEFAULT TRUE,
    fuzzy_distance INTEGER DEFAULT 2,
    limit_results INTEGER DEFAULT 20
) RETURNS TABLE(
    manga_id BIGINT,
    title TEXT,
    native_title TEXT,
    romanized_title TEXT,
    paradedb_score FLOAT,
    title_similarity FLOAT,
    combined_score FLOAT,
    match_type TEXT
) AS $$
BEGIN
    RETURN QUERY
    WITH search_results AS (
        SELECT DISTINCT
            m.id,
            m.title,
            m.native_title,
            m.romanized_title,
            CASE 
                WHEN use_fuzzy AND (m.id @@@ paradedb.match('title_search', search_term, fuzzy_distance => fuzzy_distance)
                     OR m.id @@@ paradedb.match('search_text', search_term, fuzzy_distance => fuzzy_distance))
                THEN COALESCE(paradedb.score(m.id), 0.0)
                ELSE 0.0
            END as pdb_score,
            safe_manga_title_similarity(m.id, search_term) as title_sim,
            CASE 
                WHEN use_fuzzy AND (m.id @@@ paradedb.match('title_search', search_term, fuzzy_distance => fuzzy_distance)
                     OR m.id @@@ paradedb.match('search_text', search_term, fuzzy_distance => fuzzy_distance))
                THEN 'fuzzy_search'
                ELSE 'similarity_search'
            END as match_type_val
        FROM manga m
        WHERE (
            use_fuzzy AND (
                m.id @@@ paradedb.match('title_search', search_term, fuzzy_distance => fuzzy_distance)
                OR m.id @@@ paradedb.match('search_text', search_term, fuzzy_distance => fuzzy_distance)
            )
        ) OR (
            safe_manga_title_similarity(m.id, search_term) >= similarity_threshold
        )
    )
    SELECT 
        sr.id as manga_id,
        sr.title,
        sr.native_title,
        sr.romanized_title,
        sr.pdb_score as paradedb_score,
        sr.title_sim as title_similarity,
        GREATEST(
            sr.pdb_score,
            sr.title_sim * 8.0
        ) as combined_score,
        sr.match_type_val as match_type
    FROM search_results sr
    WHERE GREATEST(sr.pdb_score, sr.title_sim * 8.0) > 0
    ORDER BY combined_score DESC
    LIMIT limit_results;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- 5. SAFE FUZZY SEARCH FUNCTIONS
-- ============================================================================

-- Safe fuzzy search with similarity fallback
CREATE OR REPLACE FUNCTION safe_fuzzy_manga_search(
    search_term TEXT,
    search_fields TEXT[] DEFAULT ARRAY['title'],
    fuzzy_distance INTEGER DEFAULT 2,
    similarity_threshold FLOAT DEFAULT 0.3,
    limit_results INTEGER DEFAULT 20
) RETURNS TABLE(
    manga_id BIGINT,
    title TEXT,
    native_title TEXT,
    romanized_title TEXT,
    bm25_score FLOAT,
    similarity_score FLOAT,
    final_score FLOAT,
    matched_field TEXT
) AS $$
DECLARE
    field_name TEXT;
    where_conditions TEXT[] := '{}';
    where_clause TEXT;
BEGIN
    -- Build search conditions for each field
    FOREACH field_name IN ARRAY search_fields LOOP
        CASE field_name
            WHEN 'title' THEN
                where_conditions := array_append(where_conditions, 
                    format('m.id @@@ paradedb.match(''title_search'', %L, fuzzy_distance => %s)', search_term, fuzzy_distance));
            WHEN 'description' THEN
                where_conditions := array_append(where_conditions, 
                    format('m.id @@@ paradedb.match(''description'', %L, fuzzy_distance => %s)', search_term, fuzzy_distance));
            WHEN 'all' THEN
                where_conditions := array_append(where_conditions, 
                    format('m.id @@@ paradedb.match(''search_text'', %L, fuzzy_distance => %s)', search_term, fuzzy_distance));
        END CASE;
    END LOOP;
    
    -- Create WHERE clause
    where_clause := array_to_string(where_conditions, ' OR ');
    
    -- Execute dynamic query safely
    RETURN QUERY EXECUTE format('
        SELECT 
            m.id as manga_id,
            m.title,
            m.native_title,
            m.romanized_title,
            COALESCE(paradedb.score(m.id), 0.0) as bm25_score,
            safe_manga_title_similarity(m.id, %L) as similarity_score,
            GREATEST(
                COALESCE(paradedb.score(m.id), 0.0),
                safe_manga_title_similarity(m.id, %L) * 8.0
            ) as final_score,
            CASE 
                WHEN m.id @@@ paradedb.match(''title_search'', %L, fuzzy_distance => %s) THEN ''title''
                WHEN m.id @@@ paradedb.match(''description'', %L, fuzzy_distance => %s) THEN ''description''
                WHEN m.id @@@ paradedb.match(''search_text'', %L, fuzzy_distance => %s) THEN ''all_fields''
                ELSE ''similarity''
            END as matched_field
        FROM manga m
        WHERE (%s) OR safe_manga_title_similarity(m.id, %L) >= %s
        ORDER BY final_score DESC
        LIMIT %s
    ', search_term, search_term, search_term, fuzzy_distance, search_term, fuzzy_distance, 
       search_term, fuzzy_distance, where_clause, search_term, similarity_threshold, limit_results);
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- 6. CREATE COMPATIBILITY ALIASES
-- ============================================================================

-- Create similarity function alias for compatibility
CREATE OR REPLACE FUNCTION similarity(text1 TEXT, text2 TEXT)
RETURNS FLOAT AS $$
BEGIN
    RETURN safe_paradedb_similarity(text1, text2, 2);
END;
$$ LANGUAGE plpgsql;

-- Create manga_title_similarity alias
CREATE OR REPLACE FUNCTION manga_title_similarity(
    manga_id_input BIGINT,
    target_title TEXT,
    include_native BOOLEAN DEFAULT TRUE,
    include_romanized BOOLEAN DEFAULT TRUE
)
RETURNS FLOAT AS $$
BEGIN
    RETURN safe_manga_title_similarity(manga_id_input, target_title, include_native, include_romanized);
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- 7. UTILITY AND TESTING FUNCTIONS
-- ============================================================================

-- Test multiple similarity approaches
CREATE OR REPLACE FUNCTION test_similarity_approaches(
    test_string1 TEXT,
    test_string2 TEXT
) RETURNS TABLE(
    method_name TEXT,
    similarity_score FLOAT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 'Basic String Similarity'::TEXT, basic_string_similarity(test_string1, test_string2)
    UNION ALL
    SELECT 'Word Level Similarity'::TEXT, word_level_similarity(test_string1, test_string2)
    UNION ALL  
    SELECT 'String Similarity Score'::TEXT, string_similarity_score(test_string1, test_string2)
    UNION ALL
    SELECT 'Safe ParadeDB Similarity'::TEXT, safe_paradedb_similarity(test_string1, test_string2)
    ORDER BY similarity_score DESC;
END;
$$ LANGUAGE plpgsql;

-- Quick manga search test
CREATE OR REPLACE FUNCTION quick_manga_test(search_term TEXT)
RETURNS TABLE(
    id BIGINT,
    title TEXT,
    similarity_score FLOAT
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        id, title, sim_score
    FROM (
        SELECT 
            m.id,
            m.title,
            similarity(m.title, search_term) as sim_score
        FROM manga m 
        WHERE similarity(m.title, search_term) > 0.3
    ) AS results
    ORDER BY sim_score DESC
    LIMIT 10;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- 8. SAMPLE USAGE AND TESTS
-- ============================================================================

-- Test basic similarity
/*
SELECT 
    similarity('One Piece', 'one peice') as one_piece_test,
    similarity('Naruto', 'narto') as naruto_test,
    similarity('Attack on Titan', 'attack on titna') as titan_test;
*/

-- Test different similarity methods
/*
SELECT * FROM test_similarity_approaches('One Piece', 'one peice');
*/

-- Test safe fuzzy search
/*
SELECT * FROM safe_fuzzy_manga_search(
    'demon slyer',
    ARRAY['title', 'all'],
    2,
    0.3,
    10
);
*/

-- Test comprehensive search
/*
SELECT * FROM safe_comprehensive_manga_search(
    'tokyo goul',
    0.3,
    true,
    2,
    15
);
*/

-- Quick test
/*
SELECT * FROM quick_manga_test('one piece');
*/

-- Performance test query
/*
EXPLAIN (ANALYZE, BUFFERS)
SELECT 
    m.id, m.title,
    COALESCE(paradedb.score(m.id), 0.0) as bm25_score,
    similarity(m.title, 'naruto') as title_similarity
FROM manga m
WHERE m.id @@@ paradedb.match('title_search', 'narto', fuzzy_distance => 2)
   OR similarity(m.title, 'naruto') > 0.4
ORDER BY GREATEST(paradedb.score(m.id), similarity(m.title, 'naruto') * 8) DESC
LIMIT 20;
*/

-- ============================================================================
-- 9. CLEANUP AND MAINTENANCE
-- ============================================================================

-- Function to check for any leftover temporary objects
CREATE OR REPLACE FUNCTION check_temp_objects()
RETURNS TABLE(
    object_type TEXT,
    object_name TEXT,
    size_bytes BIGINT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        'table'::TEXT as object_type,
        tablename::TEXT as object_name,
        pg_total_relation_size(schemaname||'.'||tablename) as size_bytes
    FROM pg_tables 
    WHERE tablename LIKE 'temp_similarity_%'
    
    UNION ALL
    
    SELECT 
        'index'::TEXT as object_type,
        indexname::TEXT as object_name,
        pg_relation_size(schemaname||'.'||indexname) as size_bytes
    FROM pg_indexes 
    WHERE indexname LIKE 'temp_similarity_%';
END;
$$ LANGUAGE plpgsql;

-- Manual cleanup function (if needed)
CREATE OR REPLACE FUNCTION cleanup_temp_similarity_objects()
RETURNS INTEGER AS $$
DECLARE
    temp_obj RECORD;
    cleanup_count INTEGER := 0;
BEGIN
    -- Clean up any leftover temporary tables
    FOR temp_obj IN 
        SELECT tablename FROM pg_tables WHERE tablename LIKE 'temp_similarity_%'
    LOOP
        EXECUTE format('DROP TABLE IF EXISTS %I CASCADE', temp_obj.tablename);
        cleanup_count := cleanup_count + 1;
    END LOOP;
    
    RETURN cleanup_count;
END;
$$ LANGUAGE plpgsql;
