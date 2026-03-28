from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Request, Depends

from soulripper.downloaders import DownloadOrchestrator
from soulripper.database.services import SpotifySynchronizer

async def get_session(request: Request):
    sessionmaker = request.app.state.sessionmaker
    async with sessionmaker() as session:
        yield session

async def get_download_orchestrator(request: Request, session: AsyncSession = Depends(get_session)) -> DownloadOrchestrator:
    return DownloadOrchestrator(
        sql_session=session,
        app_params=request.app.state.app_params,
        soulseek_downloader=request.app.state.soulseek_downloader if request.app.state.soulseek_downloader else None,
        spotify_client=request.app.state.spotify_client if request.app.state.spotify_client else None,
        spotify_synchronizer=SpotifySynchronizer(session, request.app.state.spotify_client) if request.app.state.spotify_client else None
    )