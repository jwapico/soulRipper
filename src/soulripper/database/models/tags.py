import sqlalchemy as sqla
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

class Tags(Base):
    __tablename__ = "tags"

    id:             Mapped[int]           = mapped_column(sqla.Integer, primary_key=True)
    name:           Mapped[str]           = mapped_column(sqla.String, nullable=False)
    row_created_at: Mapped[sqla.DateTime] = mapped_column(sqla.DateTime, nullable=False, server_default=sqla.func.now())
    row_updated_at: Mapped[sqla.DateTime] = mapped_column(sqla.DateTime, nullable=False, server_default=sqla.func.now(), onupdate=sqla.func.now())
    playlist_tags                         = relationship("PlaylistTags", back_populates="tag", cascade="all, delete-orphan")
    track_tags                            = relationship("TrackTags", back_populates="tag", cascade="all, delete-orphan")

    __table_args__ = (
        sqla.Index("uq_tags_name_lower", sqla.text("LOWER(name)"), unique=True),
    )

    def __repr__(self):
        return (
            f"<Tags(id={self.id}, "
            f"name={self.name}, "
            f"row_created_at='{self.row_created_at}', "
            f"row_updated_at='{self.row_updated_at}')>"
        )