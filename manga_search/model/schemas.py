from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, List, Any, Literal
from datetime import datetime
from decimal import Decimal


class BaseSchema(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
        # 🔧 Critical: Disable arbitrary types validation for SQLAlchemy objects
        arbitrary_types_allowed=True,
        # Use orjson for better performance
        json_encoders={
            datetime: lambda v: v.isoformat() if v else None,
            Decimal: lambda v: float(v) if v is not None else None
        }
    )

# Basic schemas without circular references
class AuthorBase(BaseSchema):
    name: str

class AuthorCreate(AuthorBase):
    pass

class AuthorSimple(AuthorBase):
    """Simple author schema without manga relationship to avoid circular refs"""
    id: int
    created_at: datetime

class ArtistBase(BaseSchema):
    name: str

class ArtistCreate(ArtistBase):
    pass

class ArtistSimple(ArtistBase):
    """Simple artist schema without manga relationship"""
    id: int
    created_at: datetime

class PublisherBase(BaseSchema):
    name: str

class PublisherCreate(PublisherBase):
    pass

class PublisherSimple(PublisherBase):
    """Simple publisher schema without manga relationship"""
    id: int
    created_at: datetime

class GenreBase(BaseSchema):
    name: str

class GenreCreate(GenreBase):
    pass

class GenreSimple(GenreBase):
    """Simple genre schema without manga relationship"""
    id: int
    created_at: datetime

class TagBase(BaseSchema):
    name: str

class TagCreate(TagBase):
    pass

class TagSimple(TagBase):
    """Simple tag schema without manga relationship"""
    id: int
    created_at: datetime

class MangaCoverBase(BaseSchema):
    type: str
    url: str
    width: Optional[int] = None
    height: Optional[int] = None

class MangaCoverCreate(MangaCoverBase):
    manga_id: int

class MangaCover(MangaCoverBase):
    id: int
    manga_id: int
    created_at: datetime

class MangaSecondaryTitleBase(BaseSchema):
    language_code: str
    title: str
    type: Optional[str] = None
    note: Optional[str] = None

class MangaSecondaryTitleCreate(MangaSecondaryTitleBase):
    manga_id: int

class MangaSecondaryTitle(MangaSecondaryTitleBase):
    id: int
    manga_id: int

class MangaLinkBase(BaseSchema):
    url: str
    link_type: Optional[str] = None

class MangaLinkCreate(MangaLinkBase):
    manga_id: int

class MangaLink(MangaLinkBase):
    id: int
    manga_id: int
    created_at: datetime

# Main Manga schemas
class MangaBase(BaseSchema):
    title: str
    native_title: Optional[str] = None
    romanized_title: Optional[str] = None
    description: Optional[str] = None
    year: Optional[int] = None
    status: Optional[str] = None
    is_licensed: bool = False
    has_anime: bool = False
    anime: Optional[Any] = None
    content_rating: Optional[str] = None
    type: str = 'manga'
    rating: Optional[Decimal] = None
    final_volume: Optional[float] = None
    final_chapter: Optional[float] = None
    total_chapters: Optional[str] = None

class MangaCreate(MangaBase):
    author_ids: Optional[List[int]] = Field(default_factory=list)
    artist_ids: Optional[List[int]] = Field(default_factory=list)
    publisher_ids: Optional[List[int]] = Field(default_factory=list)
    genre_ids: Optional[List[int]] = Field(default_factory=list)
    tag_ids: Optional[List[int]] = Field(default_factory=list)

class MangaUpdate(BaseSchema):
    title: Optional[str] = None
    native_title: Optional[str] = None
    romanized_title: Optional[str] = None
    description: Optional[str] = None
    year: Optional[int] = None
    status: Optional[str] = None
    is_licensed: Optional[bool] = None
    has_anime: Optional[bool] = None
    anime: Optional[Any] = None
    content_rating: Optional[str] = None
    type: Optional[str] = None
    rating: Optional[Decimal] = None
    final_volume: Optional[float] = None
    final_chapter: Optional[float] = None
    total_chapters: Optional[str] = None
    author_ids: Optional[List[int]] = None
    artist_ids: Optional[List[int]] = None
    publisher_ids: Optional[List[int]] = None
    genre_ids: Optional[List[int]] = None
    tag_ids: Optional[List[int]] = None

class Manga(MangaBase):
    """Full manga schema with all relationships"""
    id: int
    state: str
    merged_with: Optional[int] = None
    last_updated_at: datetime
    created_at: datetime
    updated_at: datetime
    
    # 🔧 Use simple schemas to avoid circular references and lazy loading issues
    authors: List[AuthorSimple] = Field(default_factory=list)
    artists: List[ArtistSimple] = Field(default_factory=list)
    publishers: List[PublisherSimple] = Field(default_factory=list)
    genres: List[GenreSimple] = Field(default_factory=list)
    tags: List[TagSimple] = Field(default_factory=list)
    covers: List[MangaCover] = Field(default_factory=list)
    secondary_titles: List[MangaSecondaryTitle] = Field(default_factory=list)
    links: List[MangaLink] = Field(default_factory=list)

# Full schemas with manga relationships (for detailed views)
class Author(AuthorSimple):
    """Full author schema with manga relationship (for detailed author view)"""
    manga: List[MangaBase] = Field(default_factory=list)

class Artist(ArtistSimple):
    """Full artist schema with manga relationship"""
    manga: List[MangaBase] = Field(default_factory=list)

class Publisher(PublisherSimple):
    """Full publisher schema with manga relationship"""
    manga: List[MangaBase] = Field(default_factory=list)

class Genre(GenreSimple):
    """Full genre schema with manga relationship"""
    manga: List[MangaBase] = Field(default_factory=list)

class Tag(TagSimple):
    """Full tag schema with manga relationship"""
    manga: List[MangaBase] = Field(default_factory=list)


# Search result schemas
class MangaSearchResult(BaseSchema):
    manga_id: int
    title: str
    native_title: Optional[str]
    year: Optional[int]
    rating: Optional[Decimal]
    relevance_score: float

class SearchParams(BaseSchema):
    query: str
    limit: int = 20
    offset: int = 0
    min_rating: Optional[Decimal] = None
    max_rating: Optional[Decimal] = None
    year_from: Optional[int] = None
    year_to: Optional[int] = None
    genres: Optional[List[str]] = None
    status: Optional[str] = None
    content_rating: Optional[str] = None


class FuzzySearchParams(BaseModel):
    query: str
    search_fields: Optional[List[Literal["title", "description", "all"]]] = Field(
        default=["all"], 
        description="Fields to search in: title, description, or all"
    )
    fuzzy_distance: Optional[int] = Field(
        default=2, 
        ge=0, 
        le=5, 
        description="Maximum edit distance for fuzzy matching (0-5)"
    )
    boost_exact_matches: bool = Field(
        default=True, 
        description="Boost exact matches in results"
    )
    min_similarity: Optional[float] = Field(
        default=0.3, 
        ge=0.0, 
        le=1.0, 
        description="Minimum similarity score (0.0-1.0)"
    )
    limit: int = Field(default=20, ge=1, le=100)
    offset: int = Field(default=0, ge=0)
    
    # Additional filters
    min_rating: Optional[Decimal] = None
    max_rating: Optional[Decimal] = None
    year_from: Optional[int] = None
    year_to: Optional[int] = None
    status: Optional[str] = None
    content_rating: Optional[str] = None

class FuzzySearchResult(BaseModel):
    manga_id: int
    title: str
    native_title: Optional[str]
    romanized_title: Optional[str]
    description: Optional[str]
    year: Optional[int]
    rating: Optional[Decimal]
    status: Optional[str]
    relevance_score: float
    matched_fields: List[str]  # Which fields matched the query
    similarity_score: Optional[float] = None
