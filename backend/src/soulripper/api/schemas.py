from pydantic import BaseModel
from typing import Optional, List

class TrackResponse(BaseModel):
    id: int
    title: Optional[str]
    artists: Optional[List[str]]
    filepath: Optional[str]
    album: Optional[str]
    release_date: Optional[str]
    date_added: Optional[str]
    comments: Optional[str]
    explicit: Optional[bool]
    spotify_id: Optional[str]

    class Config:
        from_attributes = True

class PlaylistTracksResponse(BaseModel):
    playlist_id: int
    spotify_id: Optional[str]
    name: str
    description: Optional[str]
    tracks: List[TrackResponse]

class DownloadRequest(BaseModel):
    query: str

# this needs to be refactored out the download_track function in orchestrator should return a trackresponse with metadata
class DownloadResponse(BaseModel):
    filepath: Optional[str] = None
    error: Optional[str] = None