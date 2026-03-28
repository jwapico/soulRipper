from pydantic import BaseModel
from typing import Optional

class TrackResponse(BaseModel):
    id: int
    title: Optional[str]
    filepath: Optional[str]
    album: Optional[str]
    release_date: Optional[str]
    comments: Optional[str]
    explicit: Optional[bool]
    spotify_id: Optional[str]

    class Config:
        from_attributes = True

class DownloadRequest(BaseModel):
    query: str

# this needs to be refactored out the download_track function in orchestrator should return a trackresponse with metadata
class DownloadResponse(BaseModel):
    filepath: Optional[str] = None
    error: Optional[str] = None