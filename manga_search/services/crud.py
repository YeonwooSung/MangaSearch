from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, insert, update, delete, text, and_, func
from sqlalchemy.orm import selectinload
from typing import Optional, Sequence, List, Dict, Any
from decimal import Decimal

from ..model.models import (
    Manga, Author, Artist, Publisher, Genre, Tag,
    MangaCover, MangaSecondaryTitle, MangaLink
)
from ..model.schemas import (
    MangaCreate, MangaUpdate, SearchParams, MangaSearchResult,
    AuthorCreate, ArtistCreate, PublisherCreate, GenreCreate, TagCreate,
    MangaCoverCreate, MangaSecondaryTitleCreate, MangaLinkCreate
)
from ..model.metadata import (
    manga_authors, manga_artists, manga_publishers, manga_genres, manga_tags
)


class MangaCRUD:
    """CRUD operations for Manga entity"""
    
    @staticmethod
    async def get_manga(db: AsyncSession, manga_id: int) -> Optional[Manga]:
        """Get a single manga with all related data"""
        query = select(Manga).options(
            selectinload(Manga.authors),
            selectinload(Manga.artists),
            selectinload(Manga.publishers),
            selectinload(Manga.genres),
            selectinload(Manga.tags),
            selectinload(Manga.covers),
            selectinload(Manga.secondary_titles),
            selectinload(Manga.links)
        ).where(Manga.id == manga_id)
        
        result = await db.execute(query)
        return result.scalar_one_or_none()

    @staticmethod
    async def get_manga_list(
        db: AsyncSession, 
        skip: int = 0, 
        limit: int = 20,
        status: Optional[str] = None,
        year: Optional[int] = None,
        min_rating: Optional[Decimal] = None,
        max_rating: Optional[Decimal] = None,
        content_rating: Optional[str] = None,
        manga_type: Optional[str] = None
    ) -> Sequence[Manga]:
        """Get list of manga with optional filters"""
        query = select(Manga).options(
            selectinload(Manga.authors),
            selectinload(Manga.genres)
        )
        
        conditions = []
        if status:
            conditions.append(Manga.status == status)
        if year:
            conditions.append(Manga.year == year)
        if min_rating:
            conditions.append(Manga.rating >= min_rating)
        if max_rating:
            conditions.append(Manga.rating <= max_rating)
        if content_rating:
            conditions.append(Manga.content_rating == content_rating)
        if manga_type:
            conditions.append(Manga.type == manga_type)
            
        if conditions:
            query = query.where(and_(*conditions))
            
        query = query.offset(skip).limit(limit).order_by(Manga.rating.desc().nulls_last())
        
        result = await db.execute(query)
        return result.scalars().all()

    @staticmethod
    async def get_manga_count(
        db: AsyncSession,
        status: Optional[str] = None,
        year: Optional[int] = None,
        min_rating: Optional[Decimal] = None,
        max_rating: Optional[Decimal] = None,
        content_rating: Optional[str] = None,
        manga_type: Optional[str] = None
    ) -> int:
        """Get total count of manga matching filters"""
        query = select(func.count(Manga.id))
        
        conditions = []
        if status:
            conditions.append(Manga.status == status)
        if year:
            conditions.append(Manga.year == year)
        if min_rating:
            conditions.append(Manga.rating >= min_rating)
        if max_rating:
            conditions.append(Manga.rating <= max_rating)
        if content_rating:
            conditions.append(Manga.content_rating == content_rating)
        if manga_type:
            conditions.append(Manga.type == manga_type)
            
        if conditions:
            query = query.where(and_(*conditions))
            
        result = await db.execute(query)
        return result.scalar()

    @staticmethod
    async def create_manga(db: AsyncSession, manga_data: MangaCreate) -> Manga:
        """Create a new manga with relationships"""
        # Create manga record
        manga_dict = manga_data.model_dump(exclude={
            'author_ids', 'artist_ids', 'publisher_ids', 'genre_ids', 'tag_ids'
        })
        
        manga = Manga(**manga_dict)
        db.add(manga)
        await db.flush()  # Get the ID
        
        # Add relationships
        if manga_data.author_ids:
            await MangaCRUD._add_manga_authors(db, manga.id, manga_data.author_ids)
        if manga_data.artist_ids:
            await MangaCRUD._add_manga_artists(db, manga.id, manga_data.artist_ids)
        if manga_data.publisher_ids:
            await MangaCRUD._add_manga_publishers(db, manga.id, manga_data.publisher_ids)
        if manga_data.genre_ids:
            await MangaCRUD._add_manga_genres(db, manga.id, manga_data.genre_ids)
        if manga_data.tag_ids:
            await MangaCRUD._add_manga_tags(db, manga.id, manga_data.tag_ids)
            
        await db.commit()
        await db.refresh(manga)
        
        return await MangaCRUD.get_manga(db, manga.id)

    @staticmethod
    async def update_manga(db: AsyncSession, manga_id: int, manga_data: MangaUpdate) -> Optional[Manga]:
        """Update an existing manga"""
        # Update manga fields
        update_dict = {k: v for k, v in manga_data.model_dump().items() 
                      if v is not None and k not in [
                          'author_ids', 'artist_ids', 'publisher_ids', 'genre_ids', 'tag_ids'
                      ]}
        
        if update_dict:
            query = update(Manga).where(Manga.id == manga_id).values(**update_dict)
            result = await db.execute(query)
            if result.rowcount == 0:
                return None
        
        # Update relationships if provided
        if manga_data.author_ids is not None:
            await MangaCRUD._replace_manga_authors(db, manga_id, manga_data.author_ids)
        if manga_data.artist_ids is not None:
            await MangaCRUD._replace_manga_artists(db, manga_id, manga_data.artist_ids)
        if manga_data.publisher_ids is not None:
            await MangaCRUD._replace_manga_publishers(db, manga_id, manga_data.publisher_ids)
        if manga_data.genre_ids is not None:
            await MangaCRUD._replace_manga_genres(db, manga_id, manga_data.genre_ids)
        if manga_data.tag_ids is not None:
            await MangaCRUD._replace_manga_tags(db, manga_id, manga_data.tag_ids)
            
        await db.commit()
        return await MangaCRUD.get_manga(db, manga_id)

    @staticmethod
    async def delete_manga(db: AsyncSession, manga_id: int) -> bool:
        """Delete a manga (cascades to relationships)"""
        query = delete(Manga).where(Manga.id == manga_id)
        result = await db.execute(query)
        await db.commit()
        return result.rowcount > 0

    # Helper methods for relationship management
    @staticmethod
    async def _add_manga_authors(db: AsyncSession, manga_id: int, author_ids: List[int]):
        if not author_ids:
            return
        values = [{'manga_id': manga_id, 'author_id': author_id} for author_id in author_ids]
        query = insert(manga_authors).values(values)
        await db.execute(query)

    @staticmethod
    async def _replace_manga_authors(db: AsyncSession, manga_id: int, author_ids: List[int]):
        # Delete existing
        del_query = delete(manga_authors).where(manga_authors.c.manga_id == manga_id)
        await db.execute(del_query)
        # Add new
        if author_ids:
            await MangaCRUD._add_manga_authors(db, manga_id, author_ids)

    @staticmethod
    async def _add_manga_artists(db: AsyncSession, manga_id: int, artist_ids: List[int]):
        if not artist_ids:
            return
        values = [{'manga_id': manga_id, 'artist_id': artist_id} for artist_id in artist_ids]
        query = insert(manga_artists).values(values)
        await db.execute(query)

    @staticmethod
    async def _replace_manga_artists(db: AsyncSession, manga_id: int, artist_ids: List[int]):
        del_query = delete(manga_artists).where(manga_artists.c.manga_id == manga_id)
        await db.execute(del_query)
        if artist_ids:
            await MangaCRUD._add_manga_artists(db, manga_id, artist_ids)

    @staticmethod
    async def _add_manga_publishers(db: AsyncSession, manga_id: int, publisher_ids: List[int]):
        if not publisher_ids:
            return
        values = [{'manga_id': manga_id, 'publisher_id': publisher_id} for publisher_id in publisher_ids]
        query = insert(manga_publishers).values(values)
        await db.execute(query)

    @staticmethod
    async def _replace_manga_publishers(db: AsyncSession, manga_id: int, publisher_ids: List[int]):
        del_query = delete(manga_publishers).where(manga_publishers.c.manga_id == manga_id)
        await db.execute(del_query)
        if publisher_ids:
            await MangaCRUD._add_manga_publishers(db, manga_id, publisher_ids)

    @staticmethod
    async def _add_manga_genres(db: AsyncSession, manga_id: int, genre_ids: List[int]):
        if not genre_ids:
            return
        values = [{'manga_id': manga_id, 'genre_id': genre_id} for genre_id in genre_ids]
        query = insert(manga_genres).values(values)
        await db.execute(query)

    @staticmethod
    async def _replace_manga_genres(db: AsyncSession, manga_id: int, genre_ids: List[int]):
        del_query = delete(manga_genres).where(manga_genres.c.manga_id == manga_id)
        await db.execute(del_query)
        if genre_ids:
            await MangaCRUD._add_manga_genres(db, manga_id, genre_ids)

    @staticmethod
    async def _add_manga_tags(db: AsyncSession, manga_id: int, tag_ids: List[int]):
        if not tag_ids:
            return
        values = [{'manga_id': manga_id, 'tag_id': tag_id} for tag_id in tag_ids]
        query = insert(manga_tags).values(values)
        await db.execute(query)

    @staticmethod
    async def _replace_manga_tags(db: AsyncSession, manga_id: int, tag_ids: List[int]):
        del_query = delete(manga_tags).where(manga_tags.c.manga_id == manga_id)
        await db.execute(del_query)
        if tag_ids:
            await MangaCRUD._add_manga_tags(db, manga_id, tag_ids)

    # BM25 Search methods
    @staticmethod
    async def search_manga(db: AsyncSession, params: SearchParams) -> List[MangaSearchResult]:
        """Basic BM25 search using database function"""
        query = text("""
            SELECT * FROM search_manga(:query, :limit_count, :offset_count)
        """)
        
        result = await db.execute(query, {
            'query': params.query,
            'limit_count': params.limit,
            'offset_count': params.offset
        })
        
        return [MangaSearchResult(
            manga_id=row.manga_id,
            title=row.title,
            native_title=row.native_title,
            year=row.year,
            rating=row.rating,
            relevance_score=row.bm25_score
        ) for row in result.fetchall()]

    @staticmethod
    async def advanced_search_manga(db: AsyncSession, params: SearchParams) -> List[Dict[str, Any]]:
        """Advanced search with filters using database function"""
        query = text("""
            SELECT * FROM advanced_manga_search(
                search_text := :search_text,
                min_rating := :min_rating,
                max_rating := :max_rating,
                year_from := :year_from,
                year_to := :year_to,
                genres := :genres,
                status_filter := :status_filter,
                content_rating_filter := :content_rating_filter,
                limit_count := :limit_count,
                offset_count := :offset_count
            )
        """)
        
        result = await db.execute(query, {
            'search_text': params.query or '',
            'min_rating': params.min_rating or 0,
            'max_rating': params.max_rating or 10,
            'year_from': params.year_from or 1900,
            'year_to': params.year_to or 2100,
            'genres': params.genres or [],
            'status_filter': params.status or '',
            'content_rating_filter': params.content_rating or '',
            'limit_count': params.limit,
            'offset_count': params.offset
        })
        
        return [dict(row._mapping) for row in result.fetchall()]


class AuthorCRUD:
    """CRUD operations for Author entity"""
    
    @staticmethod
    async def get_authors(
        db: AsyncSession, 
        skip: int = 0, 
        limit: int = 100,
        search: Optional[str] = None
    ) -> Sequence[Author]:
        """Get list of authors with optional search"""
        query = select(Author)
        
        if search:
            query = query.where(Author.name.ilike(f"%{search}%"))
            
        query = query.offset(skip).limit(limit).order_by(Author.name)
        result = await db.execute(query)
        return result.scalars().all()

    @staticmethod
    async def get_authors_count(
        db: AsyncSession,
        search: Optional[str] = None
    ) -> int:
        """Get total count of authors"""
        query = select(func.count(Author.id))
        
        if search:
            query = query.where(Author.name.ilike(f"%{search}%"))
            
        result = await db.execute(query)
        return result.scalar()

    @staticmethod
    async def create_author(db: AsyncSession, author: AuthorCreate) -> Author:
        """Create a new author"""
        db_author = Author(**author.model_dump())
        db.add(db_author)
        await db.commit()
        await db.refresh(db_author)
        return db_author

    @staticmethod
    async def get_author(db: AsyncSession, author_id: int) -> Optional[Author]:
        """Get author by ID with related manga"""
        query = select(Author).options(
            selectinload(Author.manga)
        ).where(Author.id == author_id)
        result = await db.execute(query)
        return result.scalar_one_or_none()

    @staticmethod
    async def get_author_by_name(db: AsyncSession, name: str) -> Optional[Author]:
        """Get author by exact name"""
        query = select(Author).where(Author.name == name)
        result = await db.execute(query)
        return result.scalar_one_or_none()

    @staticmethod
    async def update_author(
        db: AsyncSession, 
        author_id: int, 
        author: AuthorCreate
    ) -> Optional[Author]:
        """Update author"""
        query = update(Author).where(Author.id == author_id).values(**author.model_dump())
        result = await db.execute(query)
        if result.rowcount == 0:
            return None
        await db.commit()
        return await AuthorCRUD.get_author(db, author_id)

    @staticmethod
    async def delete_author(db: AsyncSession, author_id: int) -> bool:
        """Delete author (check for manga relationships first)"""
        # Check if author has manga relationships
        manga_count = await db.execute(
            select(func.count(manga_authors.c.manga_id))
            .where(manga_authors.c.author_id == author_id)
        )
        
        if manga_count.scalar() > 0:
            return False  # Cannot delete author with manga relationships
            
        query = delete(Author).where(Author.id == author_id)
        result = await db.execute(query)
        await db.commit()
        return result.rowcount > 0

    @staticmethod
    async def get_author_manga_count(db: AsyncSession, author_id: int) -> int:
        """Get count of manga for this author"""
        result = await db.execute(
            select(func.count(manga_authors.c.manga_id))
            .where(manga_authors.c.author_id == author_id)
        )
        return result.scalar()


class ArtistCRUD:
    """CRUD operations for Artist entity"""
    
    @staticmethod
    async def get_artists(
        db: AsyncSession, 
        skip: int = 0, 
        limit: int = 100,
        search: Optional[str] = None
    ) -> Sequence[Artist]:
        """Get list of artists with optional search"""
        query = select(Artist)
        
        if search:
            query = query.where(Artist.name.ilike(f"%{search}%"))
            
        query = query.offset(skip).limit(limit).order_by(Artist.name)
        result = await db.execute(query)
        return result.scalars().all()

    @staticmethod
    async def get_artists_count(
        db: AsyncSession,
        search: Optional[str] = None
    ) -> int:
        """Get total count of artists"""
        query = select(func.count(Artist.id))
        
        if search:
            query = query.where(Artist.name.ilike(f"%{search}%"))
            
        result = await db.execute(query)
        return result.scalar()

    @staticmethod
    async def create_artist(db: AsyncSession, artist: ArtistCreate) -> Artist:
        """Create a new artist"""
        db_artist = Artist(**artist.model_dump())
        db.add(db_artist)
        await db.commit()
        await db.refresh(db_artist)
        return db_artist

    @staticmethod
    async def get_artist(db: AsyncSession, artist_id: int) -> Optional[Artist]:
        """Get artist by ID with related manga"""
        query = select(Artist).options(
            selectinload(Artist.manga)
        ).where(Artist.id == artist_id)
        result = await db.execute(query)
        return result.scalar_one_or_none()

    @staticmethod
    async def get_artist_by_name(db: AsyncSession, name: str) -> Optional[Artist]:
        """Get artist by exact name"""
        query = select(Artist).where(Artist.name == name)
        result = await db.execute(query)
        return result.scalar_one_or_none()

    @staticmethod
    async def update_artist(
        db: AsyncSession, 
        artist_id: int, 
        artist: ArtistCreate
    ) -> Optional[Artist]:
        """Update artist"""
        query = update(Artist).where(Artist.id == artist_id).values(**artist.model_dump())
        result = await db.execute(query)
        if result.rowcount == 0:
            return None
        await db.commit()
        return await ArtistCRUD.get_artist(db, artist_id)

    @staticmethod
    async def delete_artist(db: AsyncSession, artist_id: int) -> bool:
        """Delete artist (check for manga relationships first)"""
        # Check if artist has manga relationships
        manga_count = await db.execute(
            select(func.count(manga_artists.c.manga_id))
            .where(manga_artists.c.artist_id == artist_id)
        )
        
        if manga_count.scalar() > 0:
            return False  # Cannot delete artist with manga relationships
            
        query = delete(Artist).where(Artist.id == artist_id)
        result = await db.execute(query)
        await db.commit()
        return result.rowcount > 0

    @staticmethod
    async def get_artist_manga_count(db: AsyncSession, artist_id: int) -> int:
        """Get count of manga for this artist"""
        result = await db.execute(
            select(func.count(manga_artists.c.manga_id))
            .where(manga_artists.c.artist_id == artist_id)
        )
        return result.scalar()


class PublisherCRUD:
    """CRUD operations for Publisher entity"""
    
    @staticmethod
    async def get_publishers(
        db: AsyncSession, 
        skip: int = 0, 
        limit: int = 100,
        search: Optional[str] = None
    ) -> Sequence[Publisher]:
        """Get list of publishers with optional search"""
        query = select(Publisher)
        
        if search:
            query = query.where(Publisher.name.ilike(f"%{search}%"))
            
        query = query.offset(skip).limit(limit).order_by(Publisher.name)
        result = await db.execute(query)
        return result.scalars().all()

    @staticmethod
    async def get_publishers_count(
        db: AsyncSession,
        search: Optional[str] = None
    ) -> int:
        """Get total count of publishers"""
        query = select(func.count(Publisher.id))
        
        if search:
            query = query.where(Publisher.name.ilike(f"%{search}%"))
            
        result = await db.execute(query)
        return result.scalar()

    @staticmethod
    async def create_publisher(db: AsyncSession, publisher: PublisherCreate) -> Publisher:
        """Create a new publisher"""
        db_publisher = Publisher(**publisher.model_dump())
        db.add(db_publisher)
        await db.commit()
        await db.refresh(db_publisher)
        return db_publisher

    @staticmethod
    async def get_publisher(db: AsyncSession, publisher_id: int) -> Optional[Publisher]:
        """Get publisher by ID with related manga"""
        query = select(Publisher).options(
            selectinload(Publisher.manga)
        ).where(Publisher.id == publisher_id)
        result = await db.execute(query)
        return result.scalar_one_or_none()

    @staticmethod
    async def get_publisher_by_name(db: AsyncSession, name: str) -> Optional[Publisher]:
        """Get publisher by exact name"""
        query = select(Publisher).where(Publisher.name == name)
        result = await db.execute(query)
        return result.scalar_one_or_none()

    @staticmethod
    async def update_publisher(
        db: AsyncSession, 
        publisher_id: int, 
        publisher: PublisherCreate
    ) -> Optional[Publisher]:
        """Update publisher"""
        query = update(Publisher).where(Publisher.id == publisher_id).values(**publisher.model_dump())
        result = await db.execute(query)
        if result.rowcount == 0:
            return None
        await db.commit()
        return await PublisherCRUD.get_publisher(db, publisher_id)

    @staticmethod
    async def delete_publisher(db: AsyncSession, publisher_id: int) -> bool:
        """Delete publisher (check for manga relationships first)"""
        # Check if publisher has manga relationships
        manga_count = await db.execute(
            select(func.count(manga_publishers.c.manga_id))
            .where(manga_publishers.c.publisher_id == publisher_id)
        )
        
        if manga_count.scalar() > 0:
            return False  # Cannot delete publisher with manga relationships
            
        query = delete(Publisher).where(Publisher.id == publisher_id)
        result = await db.execute(query)
        await db.commit()
        return result.rowcount > 0

    @staticmethod
    async def get_publisher_manga_count(db: AsyncSession, publisher_id: int) -> int:
        """Get count of manga for this publisher"""
        result = await db.execute(
            select(func.count(manga_publishers.c.manga_id))
            .where(manga_publishers.c.publisher_id == publisher_id)
        )
        return result.scalar()


class GenreCRUD:
    """CRUD operations for Genre entity"""
    
    @staticmethod
    async def get_genres(
        db: AsyncSession, 
        skip: int = 0, 
        limit: int = 100,
        search: Optional[str] = None
    ) -> Sequence[Genre]:
        """Get list of genres with optional search"""
        query = select(Genre)
        
        if search:
            query = query.where(Genre.name.ilike(f"%{search}%"))
            
        query = query.offset(skip).limit(limit).order_by(Genre.name)
        result = await db.execute(query)
        return result.scalars().all()

    @staticmethod
    async def get_genres_count(
        db: AsyncSession,
        search: Optional[str] = None
    ) -> int:
        """Get total count of genres"""
        query = select(func.count(Genre.id))
        
        if search:
            query = query.where(Genre.name.ilike(f"%{search}%"))
            
        result = await db.execute(query)
        return result.scalar()

    @staticmethod
    async def create_genre(db: AsyncSession, genre: GenreCreate) -> Genre:
        """Create a new genre"""
        db_genre = Genre(**genre.model_dump())
        db.add(db_genre)
        await db.commit()
        await db.refresh(db_genre)
        return db_genre

    @staticmethod
    async def get_genre(db: AsyncSession, genre_id: int) -> Optional[Genre]:
        """Get genre by ID with related manga"""
        query = select(Genre).options(
            selectinload(Genre.manga)
        ).where(Genre.id == genre_id)
        result = await db.execute(query)
        return result.scalar_one_or_none()

    @staticmethod
    async def get_genre_by_name(db: AsyncSession, name: str) -> Optional[Genre]:
        """Get genre by exact name"""
        query = select(Genre).where(Genre.name == name)
        result = await db.execute(query)
        return result.scalar_one_or_none()

    @staticmethod
    async def update_genre(
        db: AsyncSession, 
        genre_id: int, 
        genre: GenreCreate
    ) -> Optional[Genre]:
        """Update genre"""
        query = update(Genre).where(Genre.id == genre_id).values(**genre.model_dump())
        result = await db.execute(query)
        if result.rowcount == 0:
            return None
        await db.commit()
        return await GenreCRUD.get_genre(db, genre_id)

    @staticmethod
    async def delete_genre(db: AsyncSession, genre_id: int) -> bool:
        """Delete genre (check for manga relationships first)"""
        # Check if genre has manga relationships
        manga_count = await db.execute(
            select(func.count(manga_genres.c.manga_id))
            .where(manga_genres.c.genre_id == genre_id)
        )
        
        if manga_count.scalar() > 0:
            return False  # Cannot delete genre with manga relationships
            
        query = delete(Genre).where(Genre.id == genre_id)
        result = await db.execute(query)
        await db.commit()
        return result.rowcount > 0

    @staticmethod
    async def get_genre_manga_count(db: AsyncSession, genre_id: int) -> int:
        """Get count of manga for this genre"""
        result = await db.execute(
            select(func.count(manga_genres.c.manga_id))
            .where(manga_genres.c.genre_id == genre_id)
        )
        return result.scalar()

    @staticmethod
    async def get_popular_genres(db: AsyncSession, limit: int = 20) -> List[Dict[str, Any]]:
        """Get genres ordered by manga count"""
        query = text("""
            SELECT 
                g.id,
                g.name,
                COUNT(mg.manga_id) as manga_count,
                AVG(m.rating) as avg_rating
            FROM genres g
            LEFT JOIN manga_genres mg ON g.id = mg.genre_id
            LEFT JOIN manga m ON mg.manga_id = m.id
            GROUP BY g.id, g.name
            ORDER BY manga_count DESC, avg_rating DESC NULLS LAST
            LIMIT :limit
        """)
        
        result = await db.execute(query, {'limit': limit})
        return [dict(row._mapping) for row in result.fetchall()]


class TagCRUD:
    """CRUD operations for Tag entity"""
    
    @staticmethod
    async def get_tags(
        db: AsyncSession, 
        skip: int = 0, 
        limit: int = 100,
        search: Optional[str] = None
    ) -> Sequence[Tag]:
        """Get list of tags with optional search"""
        query = select(Tag)
        
        if search:
            query = query.where(Tag.name.ilike(f"%{search}%"))
            
        query = query.offset(skip).limit(limit).order_by(Tag.name)
        result = await db.execute(query)
        return result.scalars().all()

    @staticmethod
    async def get_tags_count(
        db: AsyncSession,
        search: Optional[str] = None
    ) -> int:
        """Get total count of tags"""
        query = select(func.count(Tag.id))
        
        if search:
            query = query.where(Tag.name.ilike(f"%{search}%"))
            
        result = await db.execute(query)
        return result.scalar()

    @staticmethod
    async def create_tag(db: AsyncSession, tag: TagCreate) -> Tag:
        """Create a new tag"""
        db_tag = Tag(**tag.model_dump())
        db.add(db_tag)
        await db.commit()
        await db.refresh(db_tag)
        return db_tag

    @staticmethod
    async def get_tag(db: AsyncSession, tag_id: int) -> Optional[Tag]:
        """Get tag by ID with related manga"""
        query = select(Tag).options(
            selectinload(Tag.manga)
        ).where(Tag.id == tag_id)
        result = await db.execute(query)
        return result.scalar_one_or_none()

    @staticmethod
    async def get_tag_by_name(db: AsyncSession, name: str) -> Optional[Tag]:
        """Get tag by exact name"""
        query = select(Tag).where(Tag.name == name)
        result = await db.execute(query)
        return result.scalar_one_or_none()

    @staticmethod
    async def update_tag(
        db: AsyncSession, 
        tag_id: int, 
        tag: TagCreate
    ) -> Optional[Tag]:
        """Update tag"""
        query = update(Tag).where(Tag.id == tag_id).values(**tag.model_dump())
        result = await db.execute(query)
        if result.rowcount == 0:
            return None
        await db.commit()
        return await TagCRUD.get_tag(db, tag_id)

    @staticmethod
    async def delete_tag(db: AsyncSession, tag_id: int) -> bool:
        """Delete tag (check for manga relationships first)"""
        # Check if tag has manga relationships
        manga_count = await db.execute(
            select(func.count(manga_tags.c.manga_id))
            .where(manga_tags.c.tag_id == tag_id)
        )
        
        if manga_count.scalar() > 0:
            return False  # Cannot delete tag with manga relationships
            
        query = delete(Tag).where(Tag.id == tag_id)
        result = await db.execute(query)
        await db.commit()
        return result.rowcount > 0

    @staticmethod
    async def get_tag_manga_count(db: AsyncSession, tag_id: int) -> int:
        """Get count of manga for this tag"""
        result = await db.execute(
            select(func.count(manga_tags.c.manga_id))
            .where(manga_tags.c.tag_id == tag_id)
        )
        return result.scalar()

    @staticmethod
    async def get_popular_tags(db: AsyncSession, limit: int = 50) -> List[Dict[str, Any]]:
        """Get tags ordered by manga count"""
        query = text("""
            SELECT 
                t.id,
                t.name,
                COUNT(mt.manga_id) as manga_count,
                AVG(m.rating) as avg_rating
            FROM tags t
            LEFT JOIN manga_tags mt ON t.id = mt.tag_id
            LEFT JOIN manga m ON mt.manga_id = m.id
            GROUP BY t.id, t.name
            ORDER BY manga_count DESC, avg_rating DESC NULLS LAST
            LIMIT :limit
        """)
        
        result = await db.execute(query, {'limit': limit})
        return [dict(row._mapping) for row in result.fetchall()]


class MangaCoverCRUD:
    """CRUD operations for MangaCover entity"""
    
    @staticmethod
    async def get_manga_covers(db: AsyncSession, manga_id: int) -> Sequence[MangaCover]:
        """Get all covers for a manga"""
        query = select(MangaCover).where(MangaCover.manga_id == manga_id).order_by(MangaCover.type)
        result = await db.execute(query)
        return result.scalars().all()

    @staticmethod
    async def create_manga_cover(db: AsyncSession, cover: MangaCoverCreate) -> MangaCover:
        """Create a new manga cover"""
        db_cover = MangaCover(**cover.model_dump())
        db.add(db_cover)
        await db.commit()
        await db.refresh(db_cover)
        return db_cover

    @staticmethod
    async def get_manga_cover(db: AsyncSession, cover_id: int) -> Optional[MangaCover]:
        """Get cover by ID"""
        query = select(MangaCover).where(MangaCover.id == cover_id)
        result = await db.execute(query)
        return result.scalar_one_or_none()

    @staticmethod
    async def update_manga_cover(
        db: AsyncSession, 
        cover_id: int, 
        cover_data: MangaCoverCreate
    ) -> Optional[MangaCover]:
        """Update manga cover"""
        update_dict = cover_data.model_dump(exclude={'manga_id'})  # Don't update manga_id
        query = update(MangaCover).where(MangaCover.id == cover_id).values(**update_dict)
        result = await db.execute(query)
        if result.rowcount == 0:
            return None
        await db.commit()
        return await MangaCoverCRUD.get_manga_cover(db, cover_id)

    @staticmethod
    async def delete_manga_cover(db: AsyncSession, cover_id: int) -> bool:
        """Delete manga cover"""
        query = delete(MangaCover).where(MangaCover.id == cover_id)
        result = await db.execute(query)
        await db.commit()
        return result.rowcount > 0


class MangaSecondaryTitleCRUD:
    """CRUD operations for MangaSecondaryTitle entity"""
    
    @staticmethod
    async def get_manga_secondary_titles(db: AsyncSession, manga_id: int) -> Sequence[MangaSecondaryTitle]:
        """Get all secondary titles for a manga"""
        query = select(MangaSecondaryTitle).where(
            MangaSecondaryTitle.manga_id == manga_id
        ).order_by(MangaSecondaryTitle.language_code, MangaSecondaryTitle.type)
        result = await db.execute(query)
        return result.scalars().all()

    @staticmethod
    async def create_manga_secondary_title(
        db: AsyncSession, 
        title: MangaSecondaryTitleCreate
    ) -> MangaSecondaryTitle:
        """Create a new manga secondary title"""
        db_title = MangaSecondaryTitle(**title.model_dump())
        db.add(db_title)
        await db.commit()
        await db.refresh(db_title)
        return db_title

    @staticmethod
    async def get_manga_secondary_title(db: AsyncSession, title_id: int) -> Optional[MangaSecondaryTitle]:
        """Get secondary title by ID"""
        query = select(MangaSecondaryTitle).where(MangaSecondaryTitle.id == title_id)
        result = await db.execute(query)
        return result.scalar_one_or_none()

    @staticmethod
    async def update_manga_secondary_title(
        db: AsyncSession, 
        title_id: int, 
        title_data: MangaSecondaryTitleCreate
    ) -> Optional[MangaSecondaryTitle]:
        """Update manga secondary title"""
        update_dict = title_data.model_dump(exclude={'manga_id'})  # Don't update manga_id
        query = update(MangaSecondaryTitle).where(MangaSecondaryTitle.id == title_id).values(**update_dict)
        result = await db.execute(query)
        if result.rowcount == 0:
            return None
        await db.commit()
        return await MangaSecondaryTitleCRUD.get_manga_secondary_title(db, title_id)

    @staticmethod
    async def delete_manga_secondary_title(db: AsyncSession, title_id: int) -> bool:
        """Delete manga secondary title"""
        query = delete(MangaSecondaryTitle).where(MangaSecondaryTitle.id == title_id)
        result = await db.execute(query)
        await db.commit()
        return result.rowcount > 0


class MangaLinkCRUD:
    """CRUD operations for MangaLink entity"""
    
    @staticmethod
    async def get_manga_links(db: AsyncSession, manga_id: int) -> Sequence[MangaLink]:
        """Get all links for a manga"""
        query = select(MangaLink).where(MangaLink.manga_id == manga_id).order_by(MangaLink.link_type)
        result = await db.execute(query)
        return result.scalars().all()

    @staticmethod
    async def create_manga_link(db: AsyncSession, link: MangaLinkCreate) -> MangaLink:
        """Create a new manga link"""
        db_link = MangaLink(**link.model_dump())
        db.add(db_link)
        await db.commit()
        await db.refresh(db_link)
        return db_link

    @staticmethod
    async def get_manga_link(db: AsyncSession, link_id: int) -> Optional[MangaLink]:
        """Get link by ID"""
        query = select(MangaLink).where(MangaLink.id == link_id)
        result = await db.execute(query)
        return result.scalar_one_or_none()

    @staticmethod
    async def update_manga_link(
        db: AsyncSession, 
        link_id: int, 
        link_data: MangaLinkCreate
    ) -> Optional[MangaLink]:
        """Update manga link"""
        update_dict = link_data.model_dump(exclude={'manga_id'})  # Don't update manga_id
        query = update(MangaLink).where(MangaLink.id == link_id).values(**update_dict)
        result = await db.execute(query)
        if result.rowcount == 0:
            return None
        await db.commit()
        return await MangaLinkCRUD.get_manga_link(db, link_id)

    @staticmethod
    async def delete_manga_link(db: AsyncSession, link_id: int) -> bool:
        """Delete manga link"""
        query = delete(MangaLink).where(MangaLink.id == link_id)
        result = await db.execute(query)
        await db.commit()
        return result.rowcount > 0


class StatisticsCRUD:
    """Advanced statistics and analytics operations"""
    
    @staticmethod
    async def get_database_stats(db: AsyncSession) -> Dict[str, Any]:
        """Get overall database statistics"""
        stats_query = text("""
            SELECT 
                (SELECT COUNT(*) FROM manga) as total_manga,
                (SELECT COUNT(*) FROM authors) as total_authors,
                (SELECT COUNT(*) FROM artists) as total_artists,
                (SELECT COUNT(*) FROM publishers) as total_publishers,
                (SELECT COUNT(*) FROM genres) as total_genres,
                (SELECT COUNT(*) FROM tags) as total_tags,
                (SELECT AVG(rating) FROM manga WHERE rating IS NOT NULL) as avg_rating,
                (SELECT COUNT(*) FROM manga WHERE rating >= 8.0) as high_rated_manga,
                (SELECT MAX(year) FROM manga WHERE year IS NOT NULL) as latest_year,
                (SELECT MIN(year) FROM manga WHERE year IS NOT NULL) as earliest_year
        """)
        
        result = await db.execute(stats_query)
        row = result.fetchone()
        return dict(row._mapping)

    @staticmethod
    async def get_year_distribution(db: AsyncSession) -> List[Dict[str, Any]]:
        """Get manga distribution by year"""
        query = text("""
            SELECT 
                year,
                COUNT(*) as count,
                AVG(rating) as avg_rating
            FROM manga 
            WHERE year IS NOT NULL
            GROUP BY year
            ORDER BY year DESC
        """)
        
        result = await db.execute(query)
        return [dict(row._mapping) for row in result.fetchall()]


    @staticmethod
    async def get_rating_distribution(db: AsyncSession) -> List[Dict[str, Any]]:
        """Get manga distribution by rating ranges"""
        query = text("""
            SELECT 
                CASE 
                    WHEN rating >= 9.0 THEN '9.0+'
                    WHEN rating >= 8.0 THEN '8.0-8.9'
                    WHEN rating >= 7.0 THEN '7.0-7.9'
                    WHEN rating >= 6.0 THEN '6.0-6.9'
                    WHEN rating >= 5.0 THEN '5.0-5.9'
                    ELSE 'Below 5.0'
                END as rating_range,
                COUNT(*) as count
            FROM manga 
            WHERE rating IS NOT NULL
            GROUP BY rating_range
            ORDER BY rating_range DESC
        """)
        
        result = await db.execute(query)
        return [dict(row._mapping) for row in result.fetchall()]
