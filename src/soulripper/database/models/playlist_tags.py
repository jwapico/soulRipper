import sqlalchemy as sqla
from sqlalchemy.orm import relationship, Mapped, mapped_column

from .base import Base

class PlaylistTags(Base):
    __tablename__ = "playlist_tags"

    id:             Mapped[int]           = mapped_column(sqla.Integer, primary_key=True)
    playlist_id:    Mapped[int]           = mapped_column(sqla.Integer, sqla.ForeignKey("playlists.id", ondelete="CASCADE"), index=True, nullable=False)
    tag_id:         Mapped[int]           = mapped_column(sqla.Integer, sqla.ForeignKey("tags.id", ondelete="CASCADE"), index=True, nullable=False)
    row_created_at: Mapped[sqla.DateTime] = mapped_column(sqla.DateTime, nullable=False, server_default=sqla.func.now())
    row_updated_at: Mapped[sqla.DateTime] = mapped_column(sqla.DateTime, nullable=False, server_default=sqla.func.now(), onupdate=sqla.func.now())
    playlist                              = relationship("Playlists", back_populates="playlist_tags")
    tag                                   = relationship("Tags", back_populates="playlist_tags")

    __table_args__ = (
        sqla.UniqueConstraint("playlist_id", "tag_id", name="uq_playlist_tag"),
    )

    def __repr__(self):
        return (
            f"PlaylistTags(id={self.id}, "
            f"playlist_id={self.playlist_id}, "
            f"tag_id={self.tag_id}, "
            f"row_created_at={self.row_created_at}, "
            f"row_updated_at={self.row_updated_at})>"
        )