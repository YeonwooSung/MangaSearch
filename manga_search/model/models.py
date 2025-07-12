from sqlalchemy import (
    Column, Integer, BigInteger, String, Text, Boolean, 
    DECIMAL, Float, TIMESTAMP, ForeignKey, JSON, Table, MetaData
)
from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy.sql import func

# Create metadata and base
metadata = MetaData()
Base = declarative_base(metadata=metadata)

# ============================================================================
# ASSOCIATION TABLES (Many-to-Many Relationships)
# ============================================================================

# 🔧 Define association tables BEFORE model classes
manga_authors = Table(
    'manga_authors',
    Base.metadata,
    Column('manga_id', BigInteger, ForeignKey('manga.id', ondelete='CASCADE'), primary_key=True),
    Column('author_id', Integer, ForeignKey('authors.id', ondelete='CASCADE'), primary_key=True)
)

manga_artists = Table(
    'manga_artists',
    Base.metadata,
    Column('manga_id', BigInteger, ForeignKey('manga.id', ondelete='CASCADE'), primary_key=True),
    Column('artist_id', Integer, ForeignKey('artists.id', ondelete='CASCADE'), primary_key=True)
)

manga_publishers = Table(
    'manga_publishers',
    Base.metadata,
    Column('manga_id', BigInteger, ForeignKey('manga.id', ondelete='CASCADE'), primary_key=True),
    Column('publisher_id', Integer, ForeignKey('publishers.id', ondelete='CASCADE'), primary_key=True)
)

manga_genres = Table(
    'manga_genres',
    Base.metadata,
    Column('manga_id', BigInteger, ForeignKey('manga.id', ondelete='CASCADE'), primary_key=True),
    Column('genre_id', Integer, ForeignKey('genres.id', ondelete='CASCADE'), primary_key=True)
)

manga_tags = Table(
    'manga_tags',
    Base.metadata,
    Column('manga_id', BigInteger, ForeignKey('manga.id', ondelete='CASCADE'), primary_key=True),
    Column('tag_id', Integer, ForeignKey('tags.id', ondelete='CASCADE'), primary_key=True)
)

# ============================================================================
# MODEL CLASSES
# ============================================================================

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

    # 🔧 Use Table objects directly (not strings) for secondary parameter
    authors = relationship(
        "Author", 
        secondary=manga_authors,  # ✅ Table object, not string
        back_populates="manga",
        lazy="selectin"
    )
    artists = relationship(
        "Artist", 
        secondary=manga_artists,
        back_populates="manga",
        lazy="selectin"
    )
    publishers = relationship(
        "Publisher", 
        secondary=manga_publishers,
        back_populates="manga",
        lazy="selectin"
    )
    genres = relationship(
        "Genre", 
        secondary=manga_genres,
        back_populates="manga",
        lazy="selectin"
    )
    tags = relationship(
        "Tag", 
        secondary=manga_tags,
        back_populates="manga",
        lazy="selectin"
    )
    
    # One-to-many relationships
    covers = relationship(
        "MangaCover", 
        back_populates="manga",
        lazy="selectin",
        cascade="all, delete-orphan"
    )
    secondary_titles = relationship(
        "MangaSecondaryTitle", 
        back_populates="manga",
        lazy="selectin",
        cascade="all, delete-orphan"
    )
    links = relationship(
        "MangaLink", 
        back_populates="manga",
        lazy="selectin",
        cascade="all, delete-orphan"
    )

class Author(Base):
    __tablename__ = "authors"

    id = Column(Integer, primary_key=True)
    name = Column(Text, nullable=False, unique=True)
    created_at = Column(TIMESTAMP(timezone=True), default=func.current_timestamp())

    # Many-to-many back reference
    manga = relationship(
        "Manga", 
        secondary=manga_authors,
        back_populates="authors",
        lazy="selectin"
    )

class Artist(Base):
    __tablename__ = "artists"

    id = Column(Integer, primary_key=True)
    name = Column(Text, nullable=False, unique=True)
    created_at = Column(TIMESTAMP(timezone=True), default=func.current_timestamp())

    manga = relationship(
        "Manga", 
        secondary=manga_artists,
        back_populates="artists",
        lazy="selectin"
    )

class Publisher(Base):
    __tablename__ = "publishers"

    id = Column(Integer, primary_key=True)
    name = Column(Text, nullable=False, unique=True)
    created_at = Column(TIMESTAMP(timezone=True), default=func.current_timestamp())

    manga = relationship(
        "Manga", 
        secondary=manga_publishers,
        back_populates="publishers",
        lazy="selectin"
    )

class Genre(Base):
    __tablename__ = "genres"

    id = Column(Integer, primary_key=True)
    name = Column(Text, nullable=False, unique=True)
    created_at = Column(TIMESTAMP(timezone=True), default=func.current_timestamp())

    manga = relationship(
        "Manga", 
        secondary=manga_genres,
        back_populates="genres",
        lazy="selectin"
    )

class Tag(Base):
    __tablename__ = "tags"

    id = Column(Integer, primary_key=True)
    name = Column(Text, nullable=False, unique=True)
    created_at = Column(TIMESTAMP(timezone=True), default=func.current_timestamp())

    manga = relationship(
        "Manga", 
        secondary=manga_tags,
        back_populates="tags",
        lazy="selectin"
    )

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
