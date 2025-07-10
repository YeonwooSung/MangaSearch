#!/usr/bin/env python3
"""
Simple JSONL Manga Import Script
Simplified version for basic manga data import
"""

import json
import psycopg2
from psycopg2.extras import execute_values
import sys
from datetime import datetime


def connect_db(host, port, database, username, password):
    """Connect to PostgreSQL database"""
    try:
        conn = psycopg2.connect(
            host=host,
            port=port,
            database=database,
            user=username,
            password=password
        )
        conn.autocommit = False
        print("✓ Connected to database")
        return conn
    except Exception as e:
        print(f"✗ Database connection failed: {e}")
        sys.exit(1)

def read_jsonl_file(file_path):
    """Read and parse JSONL file"""
    manga_data = []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            for line_num, line in enumerate(file, 1):
                line = line.strip()
                if not line:
                    continue
                    
                try:
                    data = json.loads(line)
                    manga_data.append(data)
                    
                    if line_num % 1000 == 0:
                        print(f"Parsed {line_num} lines...")
                        
                except json.JSONDecodeError as e:
                    print(f"Warning: JSON error at line {line_num}: {e}")
                    continue
                    
    except FileNotFoundError:
        print(f"✗ File not found: {file_path}")
        sys.exit(1)
    except Exception as e:
        print(f"✗ Error reading file: {e}")
        sys.exit(1)
        
    print(f"✓ Parsed {len(manga_data)} manga records")
    return manga_data


def get_or_create_lookup_ids(conn, table_name, names):
    """Get or create IDs for lookup table entries"""
    if not names:
        return {}
        
    name_to_id = {}
    
    with conn.cursor() as cur:
        # Get existing IDs
        placeholders = ','.join(['%s'] * len(names))
        cur.execute(f"SELECT name, id FROM {table_name} WHERE name IN ({placeholders})", list(names))
        name_to_id = {name: id for name, id in cur.fetchall()}
        
        # Insert new entries
        new_names = [name for name in names if name not in name_to_id]
        if new_names:
            data = [(name,) for name in new_names]
            cur.execute(f"INSERT INTO {table_name} (name) VALUES %s ON CONFLICT (name) DO NOTHING RETURNING name, id", data)
            for name, id in cur.fetchall():
                name_to_id[name] = id
                
            # Get IDs for entries that already existed (conflict case)
            if len(name_to_id) < len(names):
                missing_names = [name for name in new_names if name not in name_to_id]
                if missing_names:
                    placeholders = ','.join(['%s'] * len(missing_names))
                    cur.execute(f"SELECT name, id FROM {table_name} WHERE name IN ({placeholders})", missing_names)
                    for name, id in cur.fetchall():
                        name_to_id[name] = id
    
    return name_to_id

def import_manga_simple(conn, manga_data):
    """Import manga data with simplified approach"""
    
    print("Starting import process...")
    
    # Collect all unique lookup values
    all_authors = set()
    all_artists = set()
    all_genres = set()
    all_publishers = set()
    
    for manga in manga_data:
        all_authors.update(manga.get('authors', []))
        all_artists.update(manga.get('artists', []))
        all_genres.update(manga.get('genres', []))
        if manga.get('publishers'):
            all_publishers.update(manga.get('publishers', []))
    
    print(f"Found {len(all_authors)} unique authors, {len(all_artists)} artists, {len(all_genres)} genres")
    
    # Get/create lookup IDs
    author_ids = get_or_create_lookup_ids(conn, 'authors', all_authors)
    artist_ids = get_or_create_lookup_ids(conn, 'artists', all_artists)
    genre_ids = get_or_create_lookup_ids(conn, 'genres', all_genres)
    publisher_ids = get_or_create_lookup_ids(conn, 'publishers', all_publishers)
    
    # Get external source IDs
    source_ids = {}
    with conn.cursor() as cur:
        cur.execute("SELECT name, id FROM external_sources")
        source_ids = {name: id for name, id in cur.fetchall()}
    
    # Prepare manga data for insertion
    manga_records = []
    cover_records = []
    link_records = []
    author_relations = []
    artist_relations = []
    genre_relations = []
    publisher_relations = []
    secondary_titles = []
    external_source_records = []
    
    for manga in manga_data:
        manga_id = manga.get('id')
        if not manga_id:
            continue
            
        # Main manga record
        manga_records.append((
            manga_id,
            manga.get('state', 'active'),
            manga.get('merged_with'),
            manga.get('title', ''),
            manga.get('native_title'),
            manga.get('romanized_title'),
            manga.get('description'),
            manga.get('year'),
            manga.get('status'),
            manga.get('is_licensed', False),
            manga.get('has_anime', False),
            manga.get('anime'),
            manga.get('content_rating'),
            manga.get('type', 'manga'),
            manga.get('rating'),
            manga.get('final_volume'),
            manga.get('final_chapter'),
            manga.get('total_chapters'),
            manga.get('last_updated_at', datetime.now().isoformat())
        ))
        
        # Cover images
        if manga.get('cover'):
            for cover_type, url in manga['cover'].items():
                if url:
                    cover_records.append((manga_id, cover_type, url))
        
        # External links
        for link in manga.get('links', []):
            if link:
                link_type = 'unknown'
                if 'fakku.net' in link:
                    link_type = 'store'
                elif any(domain in link for domain in ['mangadex', 'mangabaka']):
                    link_type = 'reader'
                link_records.append((manga_id, link, link_type))
        
        # Author relationships
        for author_name in manga.get('authors', []):
            if author_name in author_ids:
                author_relations.append((manga_id, author_ids[author_name]))
        
        # Artist relationships
        for artist_name in manga.get('artists', []):
            if artist_name in artist_ids:
                artist_relations.append((manga_id, artist_ids[artist_name]))
        
        # Genre relationships
        for genre_name in manga.get('genres', []):
            if genre_name in genre_ids:
                genre_relations.append((manga_id, genre_ids[genre_name]))
        
        # Publisher relationships
        for publisher_name in manga.get('publishers', []):
            if publisher_name in publisher_ids:
                publisher_relations.append((manga_id, publisher_ids[publisher_name]))
        
        # Secondary titles
        if manga.get('secondary_titles'):
            for lang_code, titles in manga['secondary_titles'].items():
                if isinstance(titles, list):
                    for title_info in titles:
                        if isinstance(title_info, dict) and title_info.get('title'):
                            secondary_titles.append((
                                manga_id,
                                lang_code,
                                title_info['title'],
                                title_info.get('type'),
                                title_info.get('note')
                            ))
        
        # External sources
        if manga.get('source'):
            for source_name, source_data in manga['source'].items():
                if source_name in source_ids and source_data:
                    external_source_records.append((
                        manga_id,
                        source_ids[source_name],
                        source_data.get('id'),
                        source_data.get('rating'),
                        source_data.get('cover'),
                        source_data.get('last_updated_at'),
                        json.dumps(source_data.get('response')) if source_data.get('response') else None,
                        json.dumps(source_data.get('statistics')) if source_data.get('statistics') else None
                    ))
    
    # Insert all data
    try:
        with conn.cursor() as cur:
            cur.execute("BEGIN")
            
            # Insert main manga data
            if manga_records:
                execute_values(cur, """
                    INSERT INTO manga (
                        id, state, merged_with, title, native_title, romanized_title,
                        description, year, status, is_licensed, has_anime, anime_id,
                        content_rating, type, rating, final_volume, final_chapter,
                        total_chapters, last_updated_at
                    ) VALUES %s
                    ON CONFLICT (id) DO UPDATE SET
                        state = EXCLUDED.state,
                        title = EXCLUDED.title,
                        native_title = EXCLUDED.native_title,
                        romanized_title = EXCLUDED.romanized_title,
                        description = EXCLUDED.description,
                        year = EXCLUDED.year,
                        status = EXCLUDED.status,
                        is_licensed = EXCLUDED.is_licensed,
                        has_anime = EXCLUDED.has_anime,
                        anime_id = EXCLUDED.anime_id,
                        content_rating = EXCLUDED.content_rating,
                        rating = EXCLUDED.rating,
                        final_volume = EXCLUDED.final_volume,
                        final_chapter = EXCLUDED.final_chapter,
                        total_chapters = EXCLUDED.total_chapters,
                        last_updated_at = EXCLUDED.last_updated_at,
                        updated_at = CURRENT_TIMESTAMP
                """, manga_records)
                print(f"✓ Inserted {len(manga_records)} manga records")
            
            # Insert covers
            if cover_records:
                execute_values(cur, """
                    INSERT INTO manga_covers (manga_id, type, url)
                    VALUES %s ON CONFLICT DO NOTHING
                """, cover_records)
                print(f"✓ Inserted {len(cover_records)} cover images")
            
            # Insert links
            if link_records:
                execute_values(cur, """
                    INSERT INTO manga_links (manga_id, url, link_type)
                    VALUES %s ON CONFLICT DO NOTHING
                """, link_records)
                print(f"✓ Inserted {len(link_records)} external links")
            
            # Insert relationships
            if author_relations:
                execute_values(cur, """
                    INSERT INTO manga_authors (manga_id, author_id)
                    VALUES %s ON CONFLICT DO NOTHING
                """, author_relations)
                print(f"✓ Inserted {len(author_relations)} author relationships")
            
            if artist_relations:
                execute_values(cur, """
                    INSERT INTO manga_artists (manga_id, artist_id)
                    VALUES %s ON CONFLICT DO NOTHING
                """, artist_relations)
                print(f"✓ Inserted {len(artist_relations)} artist relationships")
            
            if genre_relations:
                execute_values(cur, """
                    INSERT INTO manga_genres (manga_id, genre_id)
                    VALUES %s ON CONFLICT DO NOTHING
                """, genre_relations)
                print(f"✓ Inserted {len(genre_relations)} genre relationships")
            
            if publisher_relations:
                execute_values(cur, """
                    INSERT INTO manga_publishers (manga_id, publisher_id)
                    VALUES %s ON CONFLICT DO NOTHING
                """, publisher_relations)
                print(f"✓ Inserted {len(publisher_relations)} publisher relationships")
            
            # Insert secondary titles
            if secondary_titles:
                execute_values(cur, """
                    INSERT INTO manga_secondary_titles (manga_id, language_code, title, type, note)
                    VALUES %s ON CONFLICT DO NOTHING
                """, secondary_titles)
                print(f"✓ Inserted {len(secondary_titles)} secondary titles")
            
            # Insert external sources
            if external_source_records:
                execute_values(cur, """
                    INSERT INTO manga_external_sources (
                        manga_id, source_id, external_id, rating, cover_url,
                        last_updated_at, response_data, statistics
                    ) VALUES %s
                    ON CONFLICT (manga_id, source_id) DO UPDATE SET
                        external_id = EXCLUDED.external_id,
                        rating = EXCLUDED.rating,
                        cover_url = EXCLUDED.cover_url,
                        last_updated_at = EXCLUDED.last_updated_at,
                        response_data = EXCLUDED.response_data,
                        statistics = EXCLUDED.statistics
                """, external_source_records)
                print(f"✓ Inserted {len(external_source_records)} external source records")
            
            conn.commit()
            print("✓ All data committed successfully!")
            
    except Exception as e:
        conn.rollback()
        print(f"✗ Error during import: {e}")
        raise

def main():
    """Main function"""
    if len(sys.argv) != 6:
        print("Usage: python simple_import.py <jsonl_file> <host> <database> <username> <password>")
        print("Example: python simple_import.py manga.jsonl localhost manga_db postgres mypassword")
        sys.exit(1)
    
    file_path = sys.argv[1]
    host = sys.argv[2]
    database = sys.argv[3]
    username = sys.argv[4]
    password = sys.argv[5]
    port = 5432
    
    print(f"Starting import of {file_path} to {database}@{host}")
    
    # Connect to database
    conn = connect_db(host, port, database, username, password)
    
    try:
        # Read data
        manga_data = read_jsonl_file(file_path)
        
        # Import data
        import_manga_simple(conn, manga_data)
        
        print("\n🎉 Import completed successfully!")
        
    except Exception as e:
        print(f"\n💥 Import failed: {e}")
        sys.exit(1)
    finally:
        conn.close()


if __name__ == '__main__':
    main()
