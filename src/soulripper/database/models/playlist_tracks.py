import sqlalchemy as sqla
from sqlalchemy.orm import relationship, mapped_column, Mapped
from typing import Optional

from .base import Base

# association table that creates a many-to-many relationship between playlists and tracks with extra attributes
class PlaylistTracks(Base):
    __tablename__ = "playlist_tracks"

    id:                 Mapped[int] = mapped_column(sqla.Integer, primary_key=True, autoincrement=True)
    playlist_id:        Mapped[int] = mapped_column(sqla.Integer, sqla.ForeignKey("playlists.id", ondelete="CASCADE"), nullable=False, index=True)
    track_id:           Mapped[int] = mapped_column(sqla.Integer, sqla.ForeignKey("tracks.id", ondelete="CASCADE"), nullable=False, index=True)
    position:           Mapped[int] = mapped_column(sqla.Integer, nullable=False)
    added_at:           Mapped[Optional[sqla.DateTime]] = mapped_column(sqla.DateTime, nullable=True)
    row_created_at:     Mapped[sqla.DateTime] = mapped_column(sqla.DateTime, nullable=False, server_default=sqla.func.now())
    row_updated_at:     Mapped[sqla.DateTime] = mapped_column(sqla.DateTime, nullable=False, server_default=sqla.func.now(), onupdate=sqla.func.now())
    playlist          = relationship("Playlists", back_populates="playlist_tracks")
    track             = relationship("Tracks", back_populates="playlist_tracks")

    __table_args__ = (
        sqla.UniqueConstraint('playlist_id', 'track_id', name='uq_playlist_track'),
        sqla.CheckConstraint("position >= 0", name="ck_playlist_tracks_position_nonnegative")
    )

    def __repr__(self):
        return (
            f"<PlaylistTrack(id={self.id}, "
            f"playlist_id={self.playlist_id}, "
            f"track_id={self.track_id}, "
            f"added_at='{self.added_at}', "
            f"row_created_at='{self.row_created_at}', "
            f"row_updated_at='{self.row_updated_at}')>"
        )
    
