import sqlalchemy as sqla
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

class TrackTags(Base):
    __tablename__ = "track_tags"

    id:                 Mapped[int]           = mapped_column(sqla.Integer, primary_key=True)
    track_id:           Mapped[int]           = mapped_column(sqla.Integer, sqla.ForeignKey("tracks.id", ondelete="CASCADE"), index=True, nullable=False)
    tag_id:             Mapped[int]           = mapped_column(sqla.Integer, sqla.ForeignKey("tags.id", ondelete="CASCADE"), index=True, nullable=False)
    row_created_at:     Mapped[sqla.DateTime] = mapped_column(sqla.DateTime, nullable=False, server_default=sqla.func.now())
    row_updated_at:     Mapped[sqla.DateTime] = mapped_column(sqla.DateTime, nullable=False, server_default=sqla.func.now(), onupdate=sqla.func.now())
    track                                     = relationship("Tracks", back_populates="track_tags")
    tag                                       = relationship("Tags", back_populates="track_tags")

    __table_args__ = (
        sqla.UniqueConstraint("track_id", "tag_id", name="uq_track_tag"),
    )

    def __repr__(self):
        return (
            f"TrackTags(id={self.id}, "
            f"track_id={self.track_id}, "
            f"tag_id={self.tag_id}, "
            f"row_created_at={self.row_created_at}, "
            f"row_updated_at={self.row_updated_at})>"
        )