#!/usr/bin/env python3
"""
JSONL Manga Data Bulk Insert Script
Reads JSONL file and inserts manga data into PostgreSQL database
"""

import json
import logging
import sys
from datetime import datetime
from typing import Dict, List, Optional, Set, Tuple
from dataclasses import dataclass
import orjson
# from pathlib import Path

import psycopg2
from psycopg2.extras import execute_values #, execute_batch
from psycopg2.extensions import connection
import click


# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('manga_import.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class MangaData:
    """Data class for manga information"""
    id: int
    state: str
    merged_with: Optional[int]
    title: str
    native_title: Optional[str]
    romanized_title: Optional[str]
    secondary_titles: Dict
    cover: Dict
    authors: List[str]
    artists: List[str]
    description: Optional[str]
    year: Optional[int]
    status: Optional[str]
    is_licensed: bool
    has_anime: bool
    anime: Optional[dict]
    content_rating: Optional[str]
    type: str
    rating: Optional[float]
    final_volume: Optional[int]
    final_chapter: Optional[float]
    total_chapters: Optional[str]
    links: List[str]
    publishers: Optional[List[str]]
    relationships: Dict
    genres: List[str]
    tags: Optional[List[str]]
    last_updated_at: str
    source: Dict

class MangaBulkImporter:
    """Bulk importer for manga data"""
    
    def __init__(self, connection_string: str, batch_size: int = 1000):
        self.connection_string = connection_string
        self.batch_size = batch_size
        self.conn: Optional[connection] = None

        self.manga_ids = set()

        # Cache for normalized data
        self.authors_cache: Dict[str, int] = {}
        self.artists_cache: Dict[str, int] = {}
        self.genres_cache: Dict[str, int] = {}
        self.tags_cache: Dict[str, int] = {}
        self.publishers_cache: Dict[str, int] = {}
        self.external_sources_cache: Dict[str, int] = {}
        
    def connect(self):
        """Connect to database"""
        try:
            self.conn = psycopg2.connect(self.connection_string)
            self.conn.autocommit = False
            logger.info("Connected to database")
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            raise
            
    def disconnect(self):
        """Disconnect from database"""
        if self.conn:
            self.conn.close()
            logger.info("Disconnected from database")
            
    def load_caches(self):
        """Load existing data into caches"""
        with self.conn.cursor() as cur:
            # Load authors
            cur.execute("SELECT name, id FROM authors")
            self.authors_cache = {name: id for name, id in cur.fetchall()}
            
            # Load artists
            cur.execute("SELECT name, id FROM artists")
            self.artists_cache = {name: id for name, id in cur.fetchall()}

            # Load genres
            cur.execute("SELECT name, id FROM genres")
            self.genres_cache = {name: id for name, id in cur.fetchall()}

            # Load tags
            cur.execute("SELECT name, id FROM tags")
            self.tags_cache = {name: id for name, id in cur.fetchall()}
            
            # Load publishers
            cur.execute("SELECT name, id FROM publishers")
            self.publishers_cache = {name: id for name, id in cur.fetchall()}
            
            # Load external sources
            cur.execute("SELECT name, id FROM external_sources")
            self.external_sources_cache = {name: id for name, id in cur.fetchall()}
            
        logger.info(f"Loaded caches: {len(self.authors_cache)} authors, "
                   f"{len(self.artists_cache)} artists, {len(self.genres_cache)} genres")


    def parse_jsonl_file(self, file_path: str) -> List[MangaData]:
        """Parse JSONL file and return manga data"""
        manga_list = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                for line_num, line in enumerate(file, 1):
                    line = line.strip()
                    if not line:
                        continue
                        
                    try:
                        data = json.loads(line)
                        manga = self._parse_manga_json(data)
                        manga_list.append(manga)
                        
                        if line_num % 1000 == 0:
                            logger.info(f"Parsed {line_num} lines")
                            
                    except json.JSONDecodeError as e:
                        logger.error(f"JSON decode error at line {line_num}: {e}")
                        continue
                    except Exception as e:
                        logger.error(f"Error parsing line {line_num}: {e}")
                        continue
                        
        except FileNotFoundError:
            logger.error(f"File not found: {file_path}")
            raise
        except Exception as e:
            logger.error(f"Error reading file {file_path}: {e}")
            raise
            
        logger.info(f"Successfully parsed {len(manga_list)} manga records")
        return manga_list
        
    def _extract_names(self, data_list) -> Set[str]:
        """Extract names from various data formats (strings, dicts, mixed)"""
        names = set()
        if not data_list:
            return names
            
        try:
            for item in data_list:
                if isinstance(item, str):
                    # Simple string
                    if item.strip():
                        names.add(item.strip())
                elif isinstance(item, dict):
                    # Dictionary format - try common name fields
                    name = (item.get('name') or 
                           item.get('Name') or 
                           item.get('title') or 
                           item.get('Title') or
                           str(item))
                    if name and isinstance(name, str) and name.strip():
                        names.add(name.strip())
                elif item is not None:
                    # Convert other types to string
                    name_str = str(item).strip()
                    if name_str:
                        names.add(name_str)
        except (TypeError, AttributeError) as e:
            logger.warning(f"Error extracting names from {data_list}: {e}")
            # Fallback: try to convert the whole thing to string if it's not iterable
            try:
                if isinstance(data_list, str) and data_list.strip():
                    names.add(data_list.strip())
            except Exception as e:
                print(f"> Exception while extracting names: {e}")
                
        return names
        
    def _parse_manga_json(self, data: Dict) -> MangaData:
        """Parse single manga JSON record"""
        manga = MangaData(
            id=data.get('id'),
            state=data.get('state', 'active'),
            merged_with=data.get('merged_with'),
            title=data.get('title', ''),
            native_title=data.get('native_title'),
            romanized_title=data.get('romanized_title'),
            secondary_titles=data.get('secondary_titles', {}),
            cover=data.get('cover', {}),
            authors=data.get('authors', []),
            artists=data.get('artists', []),
            description=data.get('description'),
            year=data.get('year'),
            status=data.get('status'),
            is_licensed=data.get('is_licensed', False),
            has_anime=data.get('has_anime', False),
            anime=data.get('anime'),
            content_rating=data.get('content_rating'),
            type=data.get('type', 'manga'),
            rating=data.get('rating'),
            final_volume=data.get('final_volume'),
            final_chapter=data.get('final_chapter'),
            total_chapters=data.get('total_chapters'),
            links=data.get('links', []),
            publishers=data.get('publishers'),
            relationships=data.get('relationships', {}),
            genres=data.get('genres', []),
            tags=data.get('tags'),
            last_updated_at=data.get('last_updated_at', datetime.now().isoformat()),
            source=data.get('source', {})
        )

        # final_chapter -> convert to float if it's a string
        if isinstance(manga.final_chapter, str):
            try:
                manga.final_chapter = float(manga.final_chapter)
            except ValueError:
                manga.final_chapter = None

        return manga

        
    def insert_lookup_data(self, manga_list: List[MangaData]):
        """Insert and cache lookup table data (authors, artists, genres, etc.)"""
        # Collect unique values
        authors = set()
        artists = set()
        genres = set()
        tags = set()
        publishers = set()
        
        for manga in manga_list:
            # Handle different data formats safely
            authors.update(self._extract_names(manga.authors))
            artists.update(self._extract_names(manga.artists))
            genres.update(self._extract_names(manga.genres))
            if manga.tags:
                tags.update(self._extract_names(manga.tags))
            if manga.publishers:
                publishers.update(self._extract_names(manga.publishers))
                
        # Insert new authors
        new_authors = [(name,) for name in authors if name not in self.authors_cache]
        if new_authors:
            self._insert_and_cache('authors', new_authors, self.authors_cache)
            
        # Insert new artists
        new_artists = [(name,) for name in artists if name not in self.artists_cache]
        if new_artists:
            self._insert_and_cache('artists', new_artists, self.artists_cache)
            
        # Insert new genres
        new_genres = [(name,) for name in genres if name not in self.genres_cache]
        if new_genres:
            self._insert_and_cache('genres', new_genres, self.genres_cache)
            
        # Insert new tags
        new_tags = [(name,) for name in tags if name not in self.tags_cache]
        if new_tags:
            self._insert_and_cache('tags', new_tags, self.tags_cache)
            
        # Insert new publishers
        new_publishers = [(name,) for name in publishers if name not in self.publishers_cache]
        if new_publishers:
            self._insert_and_cache('publishers', new_publishers, self.publishers_cache)
            
    def _insert_and_cache(self, table_name: str, data: List[Tuple], cache: Dict[str, int]):
        """Insert data into lookup table and update cache"""
        if not data:
            return
            
        with self.conn.cursor() as cur:
            query = f"""
                INSERT INTO {table_name} (name) 
                VALUES %s 
                ON CONFLICT (name) DO NOTHING
                RETURNING name, id
            """
            
            execute_values(cur, query, data, template=None, page_size=self.batch_size)
            results = cur.fetchall()
            
            # Update cache
            for name, id in results:
                cache[name] = id
                
            # Get IDs for items that already existed
            if len(results) < len(data):
                existing_names = [item[0] for item in data]
                placeholders = ','.join(['%s'] * len(existing_names))
                cur.execute(f"SELECT name, id FROM {table_name} WHERE name IN ({placeholders})", 
                           existing_names)
                for name, id in cur.fetchall():
                    cache[name] = id
                    
        logger.info(f"Inserted/cached {len(data)} {table_name}")


    def insert_manga_data(self, manga_list: List[MangaData]):
        """Insert main manga data"""
        manga_data = []

        for manga in manga_list:
            if manga.anime is None:
                pass
            elif not isinstance(manga.anime, str):
                if isinstance(manga.anime, dict):
                    manga.anime = orjson.dumps(manga.anime).decode('utf-8')
                else:
                    manga.anime = f"""{manga.anime}"""

            manga_data.append((
                manga.id,
                manga.state,
                # manga.merged_with,
                manga.title or '',
                manga.native_title,
                manga.romanized_title,
                manga.description,
                manga.year,
                manga.status,
                manga.is_licensed,
                manga.has_anime,
                manga.anime,
                manga.content_rating,
                manga.type,
                manga.rating,
                manga.final_volume,
                manga.final_chapter,
                manga.total_chapters,
                manga.last_updated_at
            ))
            self.manga_ids.add(manga.id)

        with self.conn.cursor() as cur:
            query = """
                INSERT INTO manga (
                    id, state, title, native_title, romanized_title,
                    description, year, status, is_licensed, has_anime, anime,
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
                    anime = EXCLUDED.anime,
                    content_rating = EXCLUDED.content_rating,
                    rating = EXCLUDED.rating,
                    final_volume = EXCLUDED.final_volume,
                    final_chapter = EXCLUDED.final_chapter,
                    total_chapters = EXCLUDED.total_chapters,
                    last_updated_at = EXCLUDED.last_updated_at,
                    updated_at = CURRENT_TIMESTAMP
            """
            
            execute_values(cur, query, manga_data, template=None, page_size=self.batch_size)

        logger.info(f"Inserted {len(manga_data)} manga records")


    def insert_related_data(self, manga_list: List[MangaData]):
        """Insert all related data (covers, links, relationships, etc.)"""
        self._insert_secondary_titles(manga_list)
        self._insert_covers(manga_list)
        self._insert_manga_authors(manga_list)
        self._insert_manga_artists(manga_list)
        self._insert_manga_genres(manga_list)
        self._insert_manga_tags(manga_list)
        self._insert_manga_publishers(manga_list)
        self._insert_links(manga_list)
        self._insert_relationships(manga_list)
        self._insert_external_sources(manga_list)


    def _insert_secondary_titles(self, manga_list: List[MangaData]):
        """Insert secondary titles"""
        data = []
        for manga in manga_list:
            if manga.secondary_titles:
                for lang_code, titles in manga.secondary_titles.items():
                    if isinstance(titles, list):
                        for title_info in titles:
                            if isinstance(title_info, dict):
                                data.append((
                                    manga.id,
                                    lang_code,
                                    title_info.get('title', ''),
                                    title_info.get('type'),
                                    title_info.get('note')
                                ))
                                
        if data:
            with self.conn.cursor() as cur:
                query = """
                    INSERT INTO manga_secondary_titles (manga_id, language_code, title, type, note)
                    VALUES %s ON CONFLICT DO NOTHING
                """
                execute_values(cur, query, data, template=None, page_size=self.batch_size)
            logger.info(f"Inserted {len(data)} secondary titles")
            
    def _insert_covers(self, manga_list: List[MangaData]):
        """Insert cover images"""
        data = []
        for manga in manga_list:
            if manga.cover:
                for cover_type, url in manga.cover.items():
                    if url:
                        data.append((manga.id, cover_type, url))
                        
        if data:
            with self.conn.cursor() as cur:
                query = """
                    INSERT INTO manga_covers (manga_id, type, url)
                    VALUES %s ON CONFLICT DO NOTHING
                """
                execute_values(cur, query, data, template=None, page_size=self.batch_size)
            logger.info(f"Inserted {len(data)} cover images")
            
    def _insert_manga_authors(self, manga_list: List[MangaData]):
        """Insert manga-author relationships"""
        data = []
        for manga in manga_list:
            author_names = self._extract_names(manga.authors)
            for author_name in author_names:
                if author_name in self.authors_cache:
                    data.append((manga.id, self.authors_cache[author_name]))
                    
        if data:
            with self.conn.cursor() as cur:
                query = """
                    INSERT INTO manga_authors (manga_id, author_id)
                    VALUES %s ON CONFLICT DO NOTHING
                """
                execute_values(cur, query, data, template=None, page_size=self.batch_size)
            logger.info(f"Inserted {len(data)} manga-author relationships")
            
    def _insert_manga_artists(self, manga_list: List[MangaData]):
        """Insert manga-artist relationships"""
        data = []
        for manga in manga_list:
            artist_names = self._extract_names(manga.artists)
            for artist_name in artist_names:
                if artist_name in self.artists_cache:
                    data.append((manga.id, self.artists_cache[artist_name]))
                    
        if data:
            with self.conn.cursor() as cur:
                query = """
                    INSERT INTO manga_artists (manga_id, artist_id)
                    VALUES %s ON CONFLICT DO NOTHING
                """
                execute_values(cur, query, data, template=None, page_size=self.batch_size)
            logger.info(f"Inserted {len(data)} manga-artist relationships")
            
    def _insert_manga_genres(self, manga_list: List[MangaData]):
        """Insert manga-genre relationships"""
        data = []
        for manga in manga_list:
            genre_names = self._extract_names(manga.genres)
            for genre_name in genre_names:
                if genre_name in self.genres_cache:
                    data.append((manga.id, self.genres_cache[genre_name]))
                    
        if data:
            with self.conn.cursor() as cur:
                query = """
                    INSERT INTO manga_genres (manga_id, genre_id)
                    VALUES %s ON CONFLICT DO NOTHING
                """
                execute_values(cur, query, data, template=None, page_size=self.batch_size)
            logger.info(f"Inserted {len(data)} manga-genre relationships")
            
    def _insert_manga_tags(self, manga_list: List[MangaData]):
        """Insert manga-tag relationships"""
        data = []
        for manga in manga_list:
            tag_names = self._extract_names(manga.tags)
            for tag_name in tag_names:
                if tag_name in self.tags_cache:
                    data.append((manga.id, self.tags_cache[tag_name]))
                    
        if data:
            with self.conn.cursor() as cur:
                query = """
                    INSERT INTO manga_tags (manga_id, tag_id)
                    VALUES %s ON CONFLICT DO NOTHING
                """
                execute_values(cur, query, data, template=None, page_size=self.batch_size)
            logger.info(f"Inserted {len(data)} manga-tag relationships")
            
    def _insert_manga_publishers(self, manga_list: List[MangaData]):
        """Insert manga-publisher relationships"""
        data = []
        for manga in manga_list:
            publisher_names = self._extract_names(manga.publishers)
            for publisher_name in publisher_names:
                if publisher_name in self.publishers_cache:
                    data.append((manga.id, self.publishers_cache[publisher_name]))
                    
        if data:
            with self.conn.cursor() as cur:
                query = """
                    INSERT INTO manga_publishers (manga_id, publisher_id)
                    VALUES %s ON CONFLICT DO NOTHING
                """
                execute_values(cur, query, data, template=None, page_size=self.batch_size)
            logger.info(f"Inserted {len(data)} manga-publisher relationships")
            
    def _insert_links(self, manga_list: List[MangaData]):
        """Insert external links"""
        data = []
        for manga in manga_list:
            for link in manga.links or []:
                if link:
                    # Determine link type based on domain
                    link_type = 'unknown'
                    if 'fakku.net' in link:
                        link_type = 'store'
                    elif 'mangadex' in link or 'mangabaka' in link:
                        link_type = 'reader'
                    elif 'anilist' in link or 'myanimelist' in link:
                        link_type = 'database'
                        
                    data.append((manga.id, link, link_type))
                    
        if data:
            with self.conn.cursor() as cur:
                query = """
                    INSERT INTO manga_links (manga_id, url, link_type)
                    VALUES %s ON CONFLICT DO NOTHING
                """
                execute_values(cur, query, data, template=None, page_size=self.batch_size)
            logger.info(f"Inserted {len(data)} external links")


    def _insert_relationships(self, manga_list: List[MangaData]):
        """Insert manga relationships"""
        data = []
        for manga in manga_list:
            if manga.relationships:
                for rel_type, related_ids in manga.relationships.items():
                    if isinstance(related_ids, list):
                        for related_id in related_ids:
                            # check if related_id is in manga_ids
                            if related_id in self.manga_ids:
                                data.append((manga.id, related_id, rel_type))

        if data:
            with self.conn.cursor() as cur:
                query = """
                    INSERT INTO manga_relationships (manga_id, related_manga_id, relationship_type)
                    VALUES %s ON CONFLICT DO NOTHING
                """
                execute_values(cur, query, data, template=None, page_size=self.batch_size)
            logger.info(f"Inserted {len(data)} manga relationships")


    def _insert_external_sources(self, manga_list: List[MangaData]):
        """Insert external source data"""
        data = []
        for manga in manga_list:
            if manga.source:
                for source_name, source_data in manga.source.items():
                    if source_name in self.external_sources_cache and source_data:
                        source_id = self.external_sources_cache[source_name]
                        data.append((
                            manga.id,
                            source_id,
                            source_data.get('id'),
                            source_data.get('rating'),
                            source_data.get('cover'),
                            source_data.get('last_updated_at'),
                            json.dumps(source_data.get('response')) if source_data.get('response') else None,
                            json.dumps(source_data.get('statistics')) if source_data.get('statistics') else None
                        ))
                        
        if data:
            with self.conn.cursor() as cur:
                query = """
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
                """
                execute_values(cur, query, data, template=None, page_size=self.batch_size)
            logger.info(f"Inserted {len(data)} external source records")


    def import_file(self, file_path: str):
        """Main import function"""
        try:
            logger.info(f"Starting import of {file_path}")
            
            # Parse JSONL file
            manga_list = self.parse_jsonl_file(file_path)
            if not manga_list:
                logger.warning("No manga data found in file")
                return


            # Process in batches
            for i in range(0, len(manga_list), self.batch_size):
                batch = manga_list[i:i + self.batch_size]
                batch_num = i // self.batch_size + 1
                total_batches = (len(manga_list) + self.batch_size - 1) // self.batch_size

                logger.info(f"Processing batch {batch_num}/{total_batches} ({len(batch)} records)")

                lookup_done = False
                manga_data_done = False
                related_data_done = False
                try:
                    # Start transaction
                    with self.conn.cursor() as cur:
                        cur.execute("BEGIN")
                        
                    # Insert lookup data first
                    self.insert_lookup_data(batch)
                    lookup_done = True

                    # Insert main manga data
                    self.insert_manga_data(batch)
                    manga_data_done = True

                    # # Insert related data
                    # self.insert_related_data(batch)
                    # related_data_done = True

                    # Commit transaction
                    self.conn.commit()
                    logger.info(f"Batch {batch_num} completed successfully")
                    
                except Exception as e:
                    self.conn.rollback()
                    logger.error(f"Error processing batch {batch_num}: {e}")
                    if not lookup_done:
                        logger.error("Lookup data insertion failed, rolling back")
                    elif not manga_data_done:
                        logger.error("Manga data insertion failed, rolling back")
                    elif not related_data_done:
                        logger.error("Related data insertion failed, rolling back")
                    else:
                        logger.error("Unknown error occurred, rolling back")

                    raise

            # Process in batches
            for i in range(0, len(manga_list), self.batch_size):
                batch = manga_list[i:i + self.batch_size]
                batch_num = i // self.batch_size + 1
                total_batches = (len(manga_list) + self.batch_size - 1) // self.batch_size

                logger.info(f"Processing batch {batch_num}/{total_batches} ({len(batch)} records)")

                lookup_done = False
                manga_data_done = False
                related_data_done = False
                try:
                    # Start transaction
                    with self.conn.cursor() as cur:
                        cur.execute("BEGIN")

                    # Insert related data
                    self.insert_related_data(batch)
                    related_data_done = True

                    # Commit transaction
                    self.conn.commit()
                    logger.info(f"Batch {batch_num} completed successfully")

                except Exception as e:
                    self.conn.rollback()
                    logger.error(f"Error processing batch {batch_num}: {e}")
                    if not related_data_done:
                        logger.error("Related data insertion failed, rolling back")
                    else:
                        logger.error("Unknown error occurred, rolling back")

                    raise

            logger.info(f"Import completed successfully. Total records: {len(manga_list)}")
            
        except Exception as e:
            logger.error(f"Import failed: {e}")
            raise


@click.command()
@click.option('--file', '-f', required=True, help='Path to JSONL file')
@click.option('--host', default='localhost', help='Database host')
@click.option('--port', default=5432, help='Database port')
@click.option('--database', '-d', required=True, help='Database name')
@click.option('--username', '-u', required=True, help='Database username')
@click.option('--password', '-p', prompt=True, hide_input=True, help='Database password')
@click.option('--batch-size', default=1000, help='Batch size for bulk operations')
def main(file, host, port, database, username, password, batch_size):
    """Import manga data from JSONL file to PostgreSQL database"""
    
    # Build connection string
    connection_string = f"host={host} port={port} dbname={database} user={username} password={password}"
    
    # Create importer
    importer = MangaBulkImporter(connection_string, batch_size)

    try:
        # Connect to database
        importer.connect()

        # Load existing caches
        importer.load_caches()

        # Import file
        importer.import_file(file)
        
    except Exception as e:
        logger.error(f"Import failed: {e}")
        sys.exit(1)
    finally:
        importer.disconnect()


if __name__ == '__main__':
    main()
