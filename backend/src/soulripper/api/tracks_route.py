from fastapi import Depends, APIRouter

from sqlalchemy.ext.asyncio import AsyncSession
from soulripper.database.repositories.tracks_repository import TracksRepository
from soulripper.database.models.tracks import Tracks

from soulripper.api.deps import get_session

router = APIRouter()

@router.get("/tracks/{track_id}")
async def get_track(track_id: int, session: AsyncSession = Depends(get_session)):
    track: Tracks = await TracksRepository.get_track_from_id(session, track_id)

    if not track:
        return {"error": "Track not found"}

    return {
        "id": track.id,
        "title": track.title,
        "album": track.album,
        "filepath":track.filepath
    }