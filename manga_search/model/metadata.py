from sqlalchemy import Table
from sqlalchemy import Column, Integer, BigInteger, ForeignKey

from manga_search.infra.database import Base


manga_authors = Table(
    'manga_authors', Base.metadata,
    Column('manga_id', BigInteger, ForeignKey('manga.id', ondelete='CASCADE'), primary_key=True),
    Column('author_id', Integer, ForeignKey('authors.id', ondelete='CASCADE'), primary_key=True)
)

manga_artists = Table(
    'manga_artists', Base.metadata,
    Column('manga_id', BigInteger, ForeignKey('manga.id', ondelete='CASCADE'), primary_key=True),
    Column('artist_id', Integer, ForeignKey('artists.id', ondelete='CASCADE'), primary_key=True)
)

manga_publishers = Table(
    'manga_publishers', Base.metadata,
    Column('manga_id', BigInteger, ForeignKey('manga.id', ondelete='CASCADE'), primary_key=True),
    Column('publisher_id', Integer, ForeignKey('publishers.id', ondelete='CASCADE'), primary_key=True)
)

manga_genres = Table(
    'manga_genres', Base.metadata,
    Column('manga_id', BigInteger, ForeignKey('manga.id', ondelete='CASCADE'), primary_key=True),
    Column('genre_id', Integer, ForeignKey('genres.id', ondelete='CASCADE'), primary_key=True)
)

manga_tags = Table(
    'manga_tags', Base.metadata,
    Column('manga_id', BigInteger, ForeignKey('manga.id', ondelete='CASCADE'), primary_key=True),
    Column('tag_id', Integer, ForeignKey('tags.id', ondelete='CASCADE'), primary_key=True)
)
