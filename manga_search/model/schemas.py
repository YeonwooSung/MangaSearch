from pydantic import BaseModel, ConfigDict
from typing import Optional, List, Any
from datetime import datetime
from decimal import Decimal


class BaseSchema(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
        json_encoders={
            datetime: lambda v: v.isoformat(),
            Decimal: lambda v: float(v) if v is not None else None
        },
        # Use orjson for better performance
        json_schema_extra={
            "example": {}
        }
    )


# Basic schemas
class AuthorBase(BaseSchema):
    name: str

class AuthorCreate(AuthorBase):
    pass

class Author(AuthorBase):
    id: int
    created_at: datetime

class ArtistBase(BaseSchema):
    name: str

class ArtistCreate(ArtistBase):
    pass

class Artist(ArtistBase):
    id: int
    created_at: datetime

class PublisherBase(BaseSchema):
    name: str

class PublisherCreate(PublisherBase):
    pass

class Publisher(PublisherBase):
    id: int
    created_at: datetime

class GenreBase(BaseSchema):
    name: str

class GenreCreate(GenreBase):
    pass

class Genre(GenreBase):
    id: int
    created_at: datetime

class TagBase(BaseSchema):
    name: str

class TagCreate(TagBase):
    pass

class Tag(TagBase):
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

# Manga schemas
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
    author_ids: Optional[List[int]] = []
    artist_ids: Optional[List[int]] = []
    publisher_ids: Optional[List[int]] = []
    genre_ids: Optional[List[int]] = []
    tag_ids: Optional[List[int]] = []

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
    id: int
    state: str
    merged_with: Optional[int] = None
    last_updated_at: datetime
    created_at: datetime
    updated_at: datetime
    authors: List[Author] = []
    artists: List[Artist] = []
    publishers: List[Publisher] = []
    genres: List[Genre] = []
    tags: List[Tag] = []
    covers: List[MangaCover] = []
    secondary_titles: List[MangaSecondaryTitle] = []
    links: List[MangaLink] = []

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
