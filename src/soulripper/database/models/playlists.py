import sqlalchemy as sqla
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional

from .base import Base

# table with info about every single playlist in the library
class Playlists(Base):
    __tablename__ = "playlists"

    id:                     Mapped[int] = mapped_column(sqla.Integer, primary_key=True)
    name:                   Mapped[str] = mapped_column(sqla.String, nullable=False)
    description:            Mapped[str] = mapped_column(sqla.String, nullable=True)
    spotify_id:             Mapped[Optional[str]] = mapped_column(sqla.String, nullable=True, unique=True)
    playlist_hash:          Mapped[Optional[str]] = mapped_column(sqla.String(64), nullable=True)
    row_created_at:         Mapped[sqla.DateTime] = mapped_column(sqla.DateTime, nullable=False, server_default=sqla.func.now())
    row_updated_at:         Mapped[sqla.DateTime] = mapped_column(sqla.DateTime, nullable=False, server_default=sqla.func.now(), onupdate=sqla.func.now())
    playlist_tracks       = relationship("PlaylistTracks", back_populates="playlist", cascade="all, delete-orphan")

    __table_args__ = (
        sqla.Index("idx_playlists_name", sqla.text("LOWER(name)")),
    )

    def __repr__(self):
        return (
            f"<Playlist(id={self.id}, "
            f"spotify_id='{self.spotify_id}', "
            f"name='{self.name}', "
            f"description='{self.description}', "
            f"playlist_hash='{self.playlist_hash}', "
            f"row_created_at='{self.row_created_at}', "
            f"row_updated_at='{self.row_updated_at}')>"
        )