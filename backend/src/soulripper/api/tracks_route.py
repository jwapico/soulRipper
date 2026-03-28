from fastapi import Depends, APIRouter, HTTPException, Request
from typing import List

from sqlalchemy.ext.asyncio import AsyncSession
from soulripper.database.repositories.tracks_repository import TracksRepository
from soulripper.database.models.tracks import Tracks
from soulripper.downloaders import DownloadOrchestrator

from soulripper.api.deps import get_session, get_download_orchestrator

router = APIRouter()

@router.get("/tracks")
async def get_all_tracks(session: AsyncSession = Depends(get_session)):
    tracks: List[Tracks] = await TracksRepository.get_all_tracks(session)
    return [
        {
            "id": track.id,
            "title": track.title,
            "album": track.album,
            "filepath": track.filepath,
            "explicit": track.explicit,
            "comments": track.comments,
            "release_date": track.release_date,
            "spotify_id": track.spotify_id,
        } for track in tracks
    ]

@router.get("/tracks/{track_id}")
async def get_track(track_id: int, session: AsyncSession = Depends(get_session)):
    track: Tracks = await TracksRepository.get_track_from_id(session, track_id)

    if not track:
        raise HTTPException(status_code=404, detail="Track not found")

    return {
        "id": track.id,
        "title": track.title,
        "album": track.album,
        "filepath":track.filepath
    }

@router.post("/tracks/download")
async def download_track(request: Request, download_orchestrator: DownloadOrchestrator = Depends(get_download_orchestrator)):
    body = await request.json()
    filepath = await download_orchestrator.download_track(search_query=body["query"])
    return {
        "filepath": filepath
    }