from fastapi import Depends, APIRouter, HTTPException, Request
from typing import List

from sqlalchemy.ext.asyncio import AsyncSession
from soulripper.database.repositories.tracks_repository import TracksRepository
from soulripper.database.models.tracks import Tracks
from soulripper.downloaders import DownloadOrchestrator
from soulripper.api.deps import get_session, get_download_orchestrator
from soulripper.api.schemas import TrackResponse, DownloadRequest, DownloadResponse

router = APIRouter()

@router.get("/tracks", response_model=List[TrackResponse])
async def get_all_tracks(session: AsyncSession = Depends(get_session)):
    tracks: List[Tracks] = await TracksRepository.get_all_tracks(session)
    return [TrackResponse.model_validate(track) for track in tracks]

@router.get("/tracks/{track_id}", response_model=TrackResponse)
async def get_track(track_id: int, session: AsyncSession = Depends(get_session)):
    track: Tracks = await TracksRepository.get_track_from_id(session, track_id)

    if not track:
        raise HTTPException(status_code=404, detail="Track not found")

    return TrackResponse.model_validate(track)

@router.post("/tracks/download", response_model=DownloadResponse)
async def download_track(request: DownloadRequest, download_orchestrator: DownloadOrchestrator = Depends(get_download_orchestrator)):
    try:
        filepath = await download_orchestrator.download_track(search_query=request.query)
        return DownloadResponse(filepath=filepath)
    except Exception as e:
        return DownloadResponse(error=str(e))