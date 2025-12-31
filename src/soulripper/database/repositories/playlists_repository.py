import logging
from typing import Optional, List, Tuple
import datetime
import sqlalchemy as sqla
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import Playlists, PlaylistTracks, Tracks, Artists, TrackArtists
from ..schemas import TrackData, PlaylistData
from .tracks_repository import TracksRepository

logger = logging.getLogger(__name__)

class PlaylistsRepository():
    @classmethod
    async def add_playlist(cls, sql_session: AsyncSession, spotify_id: Optional[str], name: str, description: str) -> Playlists:
        """
        Adds a new row to the Playlists table

        Args: 
            sql_session (sqlalchemy.ext.asyncio.AsyncSession): Your open SQLAlchemy Session
            spotify_id (str): The Spotify ID of the playlist you want to add
            name (str): The name of the playlist you want to add
            description (str): The description of the playlist you want to add 

        Returns:
            Playlists: The new Playlists row
        """

        existing_playlist = None

        if spotify_id is not None:
            existing_playlist = await cls.get_playlist_by_spotify_id(sql_session=sql_session, spotify_id=spotify_id)
        if existing_playlist is None:
            existing_playlist = await cls.search_for_playlist_by_title(sql_session=sql_session, playlist_name=name)

        if existing_playlist:
            logger.info(f"Playlist with spotify_id: {spotify_id} or name: {name} already exists in the database, returning existing playlist")
            return existing_playlist

        # create, add, flush, and return the new playlist
        new_playlist = Playlists(
            spotify_id=spotify_id, 
            name=name, 
            description=description
        )

        sql_session.add(new_playlist)
        await sql_session.flush()

        return new_playlist

    @classmethod
    async def add_tracks_to_playlist(cls, sql_session: AsyncSession, playlist_track_data: List[Tuple[TrackData, datetime.datetime]], playlist_row: Playlists) -> None:
        """
        Adds a list of tracks (with their added timestamps) to the PlaylistTracks association table

        Args: 
            sql_session (sqlalchemy.ext.asyncio.AsyncSession): Your open SQLAlchemy Session
            playlist_track_data (List[Tuple[TrackData, datetime.datetime]]): The list of TrackData along with its data added
            playlist_row (Playlists): The ORM Playlists row you want to add the tracks to

        Returns:
            None
        """

        # TODO: if playlist order changes we get duplicate entries

        # for each track in the playlist, add it to the Tracks table and create an association in the PlaylistTracks table
        for pos, (track_data, date_added) in enumerate(playlist_track_data):
            new_track: Tracks = await TracksRepository.add_track(sql_session, track_data)

            existing_assocs = (await sql_session.execute(sqla.select(PlaylistTracks).where(
                (PlaylistTracks.playlist_id == playlist_row.id) &
                (PlaylistTracks.track_id == new_track.id) &
                (PlaylistTracks.position == pos)
            ))).all()

            if not existing_assocs:
                sql_session.add(
                    PlaylistTracks(
                        playlist_id=playlist_row.id,
                        track_id=new_track.id,
                        added_at=date_added,
                        position=pos
                    )
                )

        await sql_session.flush()

    @classmethod
    async def get_playlist_by_spotify_id(cls, sql_session: AsyncSession, spotify_id: str) -> Optional[Playlists]:
        """
        Gets an ORM Playlists row from spotify_id

        Args: 
            sql_session (sqlalchemy.ext.asyncio.AsyncSession): Your open SQLAlchemy Session
            spotify_id (str): The Spotify ID of the playlist you want to look up

        Returns:
            Optional[Playlists]: The matching playlist row, or None
        """

        stmt = sqla.select(Playlists).where(Playlists.spotify_id == spotify_id)
        result = await sql_session.execute(stmt)
        return result.scalars().first()
        
    @classmethod
    async def search_for_playlist_by_title(cls, sql_session: AsyncSession, playlist_name: str) -> Optional[Playlists]:
        """
        Gets an ORM Playlists row searching by playlist name

        Args: 
            sql_session (sqlalchemy.ext.asyncio.AsyncSession): Your open SQLAlchemy Session
            playlist_name (str): The name of the playlist you want to look up

        Returns:
            Optional[Playlists]: The matching playlist row, or None
        """

        stmt = sqla.select(Playlists).where(Playlists.name == playlist_name)
        result = await sql_session.execute(stmt)
        return result.scalars().first()
    
    @classmethod
    async def get_playlist_track_rows(cls, sql_session: AsyncSession, playlist_id: int) -> Optional[List[PlaylistTracks]]:
        """
        Gets a list of ORM Playlists rows from a playlist

        Args: 
            sql_session (sqlalchemy.ext.asyncio.AsyncSession): Your open SQLAlchemy Session
            playlist_id (int): The ID of the playlist you want to retrieve all the Tracks from

        Returns:
            Optional[List[Playlists]]: A list of matching playlist rows, or None
        """

        stmt = sqla.select(PlaylistTracks).where(PlaylistTracks.playlist_id == playlist_id)
        result = await sql_session.execute(stmt)
        return list(result.scalars().all())

    @classmethod
    async def get_track_data(cls, sql_session: AsyncSession, playlist_id: int) -> List[TrackData]:
        """
        Gets a list of TrackData objects for all tracks in a playlist

        Args:
            sql_session (sqlalchemy.ext.asyncio.AsyncSession): Your open SQLAlchemy Session
            playlist_id (int): The ID of the playlist you want to retrieve all the Tracks from

        Returns:
            List[TrackData]: A list of TrackData objects for all tracks in the playlist
        """

        # get all tracks in the playlist along with their artists
        stmt = (
            sqla.select(
                Tracks,
                Artists,
                PlaylistTracks.track_id,
            )
            .join(Tracks, PlaylistTracks.track_id == Tracks.id)
            .outerjoin(TrackArtists, TrackArtists.track_id == Tracks.id)
            .outerjoin(Artists, Artists.id == TrackArtists.artist_id)
            .where(PlaylistTracks.playlist_id == playlist_id)
            .order_by(PlaylistTracks.position)
        )
        
        rows = (await sql_session.execute(stmt)).all()
        tracks: list[TrackData] = []
        current_pt_id = None
        current_track = None

        # build the TrackData obj and group artists under their respective tracks
        for track, artist, pt_id in rows:
            # each artist is in a seperate row, so we need to group them using PlaylistTracks.track_id
            if pt_id != current_pt_id:
                current_track = TrackData(
                    filepath=track.filepath,
                    spotify_id=track.spotify_id,
                    title=track.title,
                    album=track.album,
                    release_date=track.release_date,
                    explicit=track.explicit,
                    comments=track.comments,
                    artists=[]
                )
                tracks.append(current_track)
                current_pt_id = pt_id

            if artist:
                assert current_track is not None
                current_track.artists.append(
                    (artist.name, artist.spotify_id)
                )

        return tracks

    @classmethod
    async def get_all_playlists(cls, sql_session: AsyncSession) -> List[PlaylistData]:
        """
        Gets a list of all playlists in the database

        Args:
            sql_session (sqlalchemy.ext.asyncio.AsyncSession): Your open SQLAlchemy Session

        Returns:
            List[PlaylistData]: A list of PlaylistData objects for all playlists in the database
        """

        result = await sql_session.execute(sqla.select(Playlists))
        playlist_rows = result.scalars().all()

        playlists = []
        for playlist in playlist_rows:
            playlist_data = await cls.get_playlist_data(sql_session, playlist.id)
            playlists.append(playlist_data)

        return playlists
    
    @classmethod
    async def get_playlist_data(cls, sql_session: AsyncSession, playlist_id: int) -> Optional[PlaylistData]:
        """
        Gets a PlaylistData object for a given playlist

        Args:
            sql_session (sqlalchemy.ext.asyncio.AsyncSession): Your open SQLAlchemy
            playlist_id (int): The ID of the playlist you want to retrieve

        Returns:
            Optional[PlaylistData]: A PlaylistData object for the playlist, or None
        """

        stmt = sqla.select(Playlists).where(Playlists.id == playlist_id)
        result = await sql_session.execute(stmt)
        playlist_row = result.scalar_one_or_none()
        tracks = await cls.get_track_data(sql_session, playlist_id)

        if playlist_row:
            return PlaylistData(
                id=playlist_row.id,
                spotify_id=playlist_row.spotify_id,
                name=playlist_row.name,
                description=playlist_row.description,
                tracks=tracks
            )
