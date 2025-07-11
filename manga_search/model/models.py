from sqlalchemy import (
    Column, Integer, BigInteger, String, Text, Boolean, 
    DECIMAL, Float, TIMESTAMP, ForeignKey, JSON
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from manga_search.infra.database import Base


class Manga(Base):
    __tablename__ = "manga"

    id = Column(BigInteger, primary_key=True)
    state = Column(String(20), nullable=False, default='active')
    merged_with = Column(BigInteger, ForeignKey('manga.id'))
    title = Column(Text, nullable=False)
    native_title = Column(Text)
    romanized_title = Column(Text)
    description = Column(Text)
    year = Column(Integer)
    status = Column(String(20))
    is_licensed = Column(Boolean, default=False)
    has_anime = Column(Boolean, default=False)
    anime = Column(JSON)
    content_rating = Column(String(20))
    type = Column(String(20), nullable=False, default='manga')
    rating = Column(DECIMAL(3, 1))
    final_volume = Column(Float)
    final_chapter = Column(Float)
    total_chapters = Column(Text)
    last_updated_at = Column(TIMESTAMP(timezone=True), default=func.current_timestamp())
    created_at = Column(TIMESTAMP(timezone=True), default=func.current_timestamp())
    updated_at = Column(TIMESTAMP(timezone=True), default=func.current_timestamp())

    # Relationships
    authors = relationship("Author", secondary="manga_authors", back_populates="manga")
    artists = relationship("Artist", secondary="manga_artists", back_populates="manga")
    publishers = relationship("Publisher", secondary="manga_publishers", back_populates="manga")
    genres = relationship("Genre", secondary="manga_genres", back_populates="manga")
    tags = relationship("Tag", secondary="manga_tags", back_populates="manga")
    covers = relationship("MangaCover", back_populates="manga")
    secondary_titles = relationship("MangaSecondaryTitle", back_populates="manga")
    links = relationship("MangaLink", back_populates="manga")

class Author(Base):
    __tablename__ = "authors"

    id = Column(Integer, primary_key=True)
    name = Column(Text, nullable=False, unique=True)
    created_at = Column(TIMESTAMP(timezone=True), default=func.current_timestamp())

    manga = relationship("Manga", secondary="manga_authors", back_populates="authors")

class Artist(Base):
    __tablename__ = "artists"

    id = Column(Integer, primary_key=True)
    name = Column(Text, nullable=False, unique=True)
    created_at = Column(TIMESTAMP(timezone=True), default=func.current_timestamp())

    manga = relationship("Manga", secondary="manga_artists", back_populates="artists")

class Publisher(Base):
    __tablename__ = "publishers"

    id = Column(Integer, primary_key=True)
    name = Column(Text, nullable=False, unique=True)
    created_at = Column(TIMESTAMP(timezone=True), default=func.current_timestamp())

    manga = relationship("Manga", secondary="manga_publishers", back_populates="publishers")

class Genre(Base):
    __tablename__ = "genres"

    id = Column(Integer, primary_key=True)
    name = Column(Text, nullable=False, unique=True)
    created_at = Column(TIMESTAMP(timezone=True), default=func.current_timestamp())

    manga = relationship("Manga", secondary="manga_genres", back_populates="genres")

class Tag(Base):
    __tablename__ = "tags"

    id = Column(Integer, primary_key=True)
    name = Column(Text, nullable=False, unique=True)
    created_at = Column(TIMESTAMP(timezone=True), default=func.current_timestamp())

    manga = relationship("Manga", secondary="manga_tags", back_populates="tags")

class MangaCover(Base):
    __tablename__ = "manga_covers"

    id = Column(Integer, primary_key=True)
    manga_id = Column(BigInteger, ForeignKey('manga.id', ondelete='CASCADE'), nullable=False)
    type = Column(String(20), nullable=False)
    url = Column(Text, nullable=False)
    width = Column(Integer)
    height = Column(Integer)
    created_at = Column(TIMESTAMP(timezone=True), default=func.current_timestamp())

    manga = relationship("Manga", back_populates="covers")

class MangaSecondaryTitle(Base):
    __tablename__ = "manga_secondary_titles"

    id = Column(Integer, primary_key=True)
    manga_id = Column(BigInteger, ForeignKey('manga.id', ondelete='CASCADE'), nullable=False)
    language_code = Column(String(5), nullable=False)
    title = Column(Text, nullable=False)
    type = Column(String(20))
    note = Column(Text)

    manga = relationship("Manga", back_populates="secondary_titles")

class MangaLink(Base):
    __tablename__ = "manga_links"

    id = Column(Integer, primary_key=True)
    manga_id = Column(BigInteger, ForeignKey('manga.id', ondelete='CASCADE'), nullable=False)
    url = Column(Text, nullable=False)
    link_type = Column(String(50))
    created_at = Column(TIMESTAMP(timezone=True), default=func.current_timestamp())

    manga = relationship("Manga", back_populates="links")
