import sqlalchemy as sqla
from sqlalchemy.orm import relationship, Mapped, mapped_column
from typing import Optional

from .base import Base

# table with info about every single artist in the library
class Artists(Base):
    __tablename__ = "artists"

    id:                 Mapped[int] = mapped_column(sqla.Integer, primary_key=True)
    name:               Mapped[str] = mapped_column(sqla.String, nullable=False)
    spotify_id:         Mapped[Optional[str]] = mapped_column(sqla.String, nullable=True, unique=True)
    row_created_at:     Mapped[sqla.DateTime] = mapped_column(sqla.DateTime, nullable=False, server_default=sqla.func.now())
    row_updated_at:     Mapped[sqla.DateTime] = mapped_column(sqla.DateTime, nullable=False, server_default=sqla.func.now(), onupdate=sqla.func.now())
    track_artists     = relationship("TrackArtists", back_populates="artist", cascade="all, delete-orphan")

    __table_args__ = (
        sqla.Index("idx_artists_name", sqla.text("LOWER(name)")),
    )

    def __repr__(self):
        return (
            f"<Artist(id={self.id}, "
            f"name='{self.name}', "
            f"spotify_id='{self.spotify_id}', "
            f"row_created_at='{self.row_created_at}', "
            f"row_updated_at='{self.row_updated_at}')>"
        )