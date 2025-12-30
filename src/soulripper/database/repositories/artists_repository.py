from sqlalchemy.ext.asyncio import AsyncSession
import sqlalchemy as sqla
from typing import List

from ..models import Artists, TrackArtists

class ArtistsRepository:
    @classmethod
    async def get_artists_for_track_id(cls, sql_session: AsyncSession, track_id: int) -> List[Artists]:
        """
        Gets a list of ORM Artist rows that were on a track with track_id 

        Args: 
            sql_session (sqlalchemy.ext.asyncio.AsyncSession): Your open SQLAlchemy Session
            track_id (int): The Tracks id that you want to retreive Artists for

        Returns:
            List[Artists]: A list of ORM Artists rows, or None
        """

        stmt = sqla.select(Artists).join(TrackArtists, TrackArtists.artist_id == Artists.id).where(TrackArtists.track_id == track_id)
        result = await sql_session.execute(stmt)
        return list(result.scalars().all())