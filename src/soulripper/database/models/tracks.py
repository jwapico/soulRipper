import sqlalchemy as sqla
from sqlalchemy.orm import mapped_column, relationship, Mapped
from typing import Optional

from .base import Base

# table with info about every single track and file in the library
# TODO: add downloaded_with column to indicate whether the track was downloaded with slskd or yt-dlp
class Tracks(Base):
    __tablename__ = "tracks"

    id:               Mapped[int] = mapped_column(sqla.Integer, primary_key=True)
    title:            Mapped[str] = mapped_column(sqla.String, nullable=False)
    spotify_id:       Mapped[Optional[str]] = mapped_column(sqla.String, nullable=True, unique=True)
    filepath:         Mapped[Optional[str]] = mapped_column(sqla.String, nullable=True, unique=True)
    album:            Mapped[Optional[str]] = mapped_column(sqla.String, nullable=True)
    release_date:     Mapped[Optional[str]] = mapped_column(sqla.String, nullable=True)
    comments:         Mapped[Optional[str]] = mapped_column(sqla.String, nullable=True)
    explicit:         Mapped[Optional[bool]] = mapped_column(sqla.Boolean, nullable=True)
    row_created_at:   Mapped[sqla.DateTime] = mapped_column(sqla.DateTime, nullable=False, server_default=sqla.func.now())
    row_updated_at:   Mapped[sqla.DateTime] = mapped_column(sqla.DateTime, nullable=False, server_default=sqla.func.now(), onupdate=sqla.func.now())
    playlist_tracks = relationship("PlaylistTracks", back_populates="track", cascade="all, delete-orphan")
    track_artists   = relationship("TrackArtists", back_populates="track", cascade="all, delete-orphan")
    track_tags      = relationship("TrackTags", back_populates="track", cascade="all, delete-orphan")

    __table_args__ = (
        sqla.Index("idx_tracks_title_album", "title", "album"),
        sqla.Index("idx_tracks_title_lower", sqla.text("LOWER(title)")),
        sqla.Index("idx_tracks_album_lower", sqla.text("LOWER(album)")),
        sqla.Index("idx_tracks_missing_files", "title", sqlite_where=(sqla.text("filepath IS NULL"))),
    )

    def __repr__(self):
        return (
            f"<Track(id={self.id}, "
            f"spotify_id='{self.spotify_id}', "
            f"filepath='{self.filepath}', "
            f"title='{self.title}', "
            f"album='{self.album}', "
            f"release_date='{self.release_date}', "
            f"explicit={self.explicit}, "
            f"comments='{self.comments}', "
            f"row_created_at='{self.row_created_at}', "
            f"row_updated_at='{self.row_updated_at}')>"
        )