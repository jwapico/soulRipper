from typing import Optional, List, Tuple
import sqlalchemy as sqla
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from ..models import Tracks, Artists, TrackArtists
from ..schemas import TrackData

logger = logging.getLogger(__name__)

class TracksRepository():
    @classmethod
    async def add_track(cls, sql_session: AsyncSession, track_data: TrackData) -> Tracks:
        """
        Adds a new track to the Tracks table. if an existing track is found it will update the trackdata

        Args: 
            sql_session (sqlalchemy.ext.asyncio.AsyncSession): Your open SQLAlchemy Session
            track_data (TrackData): The TrackData of the track you want to add

        Returns:
            Optional[Tracks]: The new ORM Tracks row, or None
        """

        # if there is an existing track, modify it with the new data return that row
        existing_track = await cls.get_existing_track(sql_session, track_data)
        if existing_track:
            await cls.modify_track(sql_session, track_data, existing_track.id)
            return existing_track
        
        # create add and flush the new Track
        track = Tracks(
            spotify_id=track_data.spotify_id,
            filepath=track_data.filepath,
            title=track_data.title,
            album=track_data.album,
            release_date=track_data.release_date,
            explicit=track_data.explicit,
            comments=track_data.comments
        )

        sql_session.add(track)
        await sql_session.flush()

        # add artists to the Artist table if they don't already exist, and add associations to the TrackArtist table
        if track_data.artists != []:
            await cls.add_track_artists(sql_session, track, track_data.artists)

        return track
    
    @classmethod 
    async def add_track_artists(cls, sql_session: AsyncSession, track_row: Tracks,  artists: List[Tuple[str, Optional[str]]]):
        for name, spotify_id in artists:
            stmt = sqla.select(Artists).where(Artists.name == name)
            artist = (await sql_session.execute(stmt)).scalar_one_or_none()

            # if there is not already an Artists row with an identical name, create it
            if artist is None:
                artist = Artists(name=name, spotify_id=spotify_id)
                sql_session.add(artist)
                await sql_session.flush()
            elif artist.spotify_id is None and spotify_id is not None:
                artist.spotify_id = spotify_id

            # add the association
            track_artist_assoc = TrackArtists(track_id=track_row.id, artist_id=artist.id)
            sql_session.add(track_artist_assoc)

        await sql_session.flush()

    @classmethod
    async def modify_track(cls, sql_session: AsyncSession, new_track_data: TrackData, track_id: Optional[int] = None) -> None:
        """
        Modifies a track in the Tracks table with new TrackData

        Args: 
            sql_session (sqlalchemy.ext.asyncio.AsyncSession): Your open SQLAlchemy Session
            track_id (int): The ID of the track you want to modify
            new_track_data (TrackData): The new TrackData of the track you want to modify

        Returns:
            None
        """

        # get the existing track, update its fields with the new data if its there, and flush
        if track_id:
            target_track = await cls.get_track_from_id(sql_session, track_id)
        else:
            target_track = await cls.get_existing_track(sql_session, new_track_data)

        if target_track:
            target_track.spotify_id = new_track_data.spotify_id if new_track_data.spotify_id is not None else target_track.spotify_id
            target_track.filepath = new_track_data.filepath if new_track_data.filepath is not None else target_track.filepath
            target_track.title = new_track_data.title if new_track_data.title is not None else target_track.title
            target_track.album = new_track_data.album if new_track_data.album is not None else target_track.album
            target_track.release_date = new_track_data.release_date if new_track_data.release_date is not None else target_track.release_date
            target_track.explicit = new_track_data.explicit if new_track_data.explicit is not None else target_track.explicit
            target_track.comments = new_track_data.comments if new_track_data.comments is not None else target_track.comments
            await sql_session.flush()
        else:
            logger.warning("Couldn't find the track you were trying to modify")

    @classmethod
    async def remove_track(cls, sql_session: AsyncSession, track_id: int) -> bool :
        """
        Removes a track from the Tracks table 

        Args: 
            sql_session (sqlalchemy.ext.asyncio.AsyncSession): Your open SQLAlchemy Session
            track_id (int): The ID of the track you want to remove

        Returns:
            bool: Whether or not the track was successfully removed
        """

        # get the track, delete it, and flush
        target_track = await cls.get_track_from_id(sql_session, track_id)

        if target_track:
            await sql_session.delete(target_track)
            logger.info(f"Successfully removed the track with id: {track_id}")
            return True
        else:
            logger.warning(f"Could not find the track you were trying to remove, track_id = {track_id}")
            return False
    
    @classmethod
    async def get_track_from_id(cls, sql_session: AsyncSession, track_id: int) -> Optional[Tracks]:
        """
        Gets an ORM Tracks row from a track id

        Args: 
            sql_session (sqlalchemy.ext.asyncio.AsyncSession): Your open SQLAlchemy Session
            track_id (int): The ID of the Track you want to retrieve

        Returns:
            Optional[Tracks]: The ORM Tracks row, or None
        """

        stmt = sqla.select(Tracks).where(Tracks.id == track_id)
        result = await sql_session.execute(stmt)
        return result.scalars().first()
        
    @classmethod
    async def search_tracks_by_title(cls, sql_session: AsyncSession, track_title: str) -> Optional[List[Tracks]]:
        """
        Gets an ORM Tracks row from a track title

        Args: 
            sql_session (sqlalchemy.ext.asyncio.AsyncSession): Your open SQLAlchemy Session
            track_id (int): The ID of the Track you want to retrieve

        Returns:
            Optional[Tracks]: The ORM Tracks row, or None
        """

        stmt = sqla.select(Tracks).where(Tracks.title.ilike(f"%{track_title}%"))
        result = await sql_session.execute(stmt)
        return list(result.scalars().all())
        
    @classmethod
    async def get_existing_track(cls, session: AsyncSession, track: TrackData) -> Optional[Tracks]:
        """
        Checks for an existing track in the Tracks table matching the provided TrackData, searching by spotify_id, filepath, and title/album in that order

        Args:
            session (sqlalchemy.ext.asyncio.AsyncSession): Your open SQLAlchemy Session
            track (TrackData): The TrackData of the track you want to check for

        Returns:
            Optional[Tracks]: The matching ORM Tracks row, or None
        """

        if track.spotify_id is not None:
            stmt = sqla.select(Tracks).where(Tracks.spotify_id == track.spotify_id)
            result = await session.execute(stmt)
            existing = result.scalars().first()
            if existing:
                return existing
        
        if track.filepath is not None:
            stmt = sqla.select(Tracks).where(Tracks.filepath == track.filepath)
            result = await session.execute(stmt)
            existing = result.scalars().first()
            if existing:
                return existing
        
        if track.title is not None and track.album is not None:
            stmt = sqla.select(Tracks).where(
                (Tracks.title == track.title) & 
                (Tracks.album == track.album)
            )
            result = await session.execute(stmt)
            return result.scalars().first()
        
        return None