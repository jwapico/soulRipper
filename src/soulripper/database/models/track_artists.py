import sqlalchemy as sqla
from sqlalchemy.orm import mapped_column, Mapped, relationship

from .base import Base

# association table that creates a simple many-to-many relationship between tracks and artists
class TrackArtists(Base):
    __tablename__ = "track_artists"

    id:                 Mapped[int] = mapped_column(sqla.Integer, primary_key=True, autoincrement=True)
    track_id:           Mapped[int] = mapped_column(sqla.Integer, sqla.ForeignKey("tracks.id", ondelete="CASCADE"), nullable=False, index=True)
    artist_id:          Mapped[int] = mapped_column(sqla.Integer, sqla.ForeignKey("artists.id", ondelete="CASCADE"), nullable=False, index=True)
    is_primary_artist:  Mapped[bool] = mapped_column(sqla.Boolean, default=True, nullable=False)
    row_created_at:     Mapped[sqla.DateTime] = mapped_column(sqla.DateTime, nullable=False, server_default=sqla.func.now())
    row_updated_at:     Mapped[sqla.DateTime] = mapped_column(sqla.DateTime, nullable=False, server_default=sqla.func.now(), onupdate=sqla.func.now())
    track             = relationship("Tracks", back_populates="track_artists")
    artist            = relationship("Artists", back_populates="track_artists")

    __table_args__ = (
        sqla.UniqueConstraint('track_id', 'artist_id', name='uq_track_artist'),
    )

    def __repr__(self):
        return (
            f"<TrackArtists(id={self.id}, "
            f"track_id={self.track_id}, "
            f"artist_id={self.artist_id}, "
            f"row_created_at='{self.row_created_at}', "
            f"row_updated_at='{self.row_updated_at}')>"
        )