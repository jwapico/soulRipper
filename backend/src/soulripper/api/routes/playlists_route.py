from typing import List
import json

from sqlalchemy.ext.asyncio import AsyncSession
import sqlalchemy as sqla
from fastapi import APIRouter, Depends

from soulripper.api.schemas import PlaylistTracksResponse, TrackResponse
from soulripper.api.deps import get_session

router = APIRouter()

@router.get("/playlists", response_model=List[PlaylistTracksResponse])
async def get_all_playlists(session: AsyncSession = Depends(get_session)) -> List[PlaylistTracksResponse]:
    query = """
    SELECT 
        p.id AS playlist_id,
        p.spotify_id,
        p.name,
        p.description,
        json_group_array(
            json_object(
                'id', t.id,
                'title', t.title,
                'artists', (
                    SELECT json_group_array(a.name)
                    FROM track_artists ta
                    JOIN artists a ON ta.artist_id = a.id
                    WHERE ta.track_id = t.id
                ),
                'filepath', t.filepath,
                'album', t.album,
                'release_date', t.release_date,
                'date_added', pt.added_at,
                'comments', t.comments,
                'explicit', t.explicit,
                'spotify_id', t.spotify_id
            )
        ) AS tracks
    FROM playlists p
    LEFT JOIN playlist_tracks pt ON p.id = pt.playlist_id
    LEFT JOIN tracks t ON pt.track_id = t.id
    GROUP BY p.id;
    """

    result = await session.execute(sqla.text(query))
    rows = result.fetchall()

    playlists = []
    for row in rows:
        tracks_data = json.loads(row.tracks) if row.tracks else []
        tracks = [TrackResponse(**t) for t in tracks_data]
        playlists.append(PlaylistTracksResponse(
            playlist_id=row.playlist_id,
            spotify_id=row.spotify_id,
            name=row.name,
            description=row.description,
            tracks=tracks
        ))

    return playlists