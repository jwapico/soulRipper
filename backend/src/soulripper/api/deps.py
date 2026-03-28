from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Request, Depends

from soulripper.downloaders import DownloadOrchestrator
from soulripper.database.services import SpotifySynchronizer

async def get_session(request: Request):
    sessionmaker = request.app.state.sessionmaker
    async with sessionmaker() as session:
        yield session

async def get_download_orchestrator(request: Request, session: AsyncSession = Depends(get_session)) -> DownloadOrchestrator:
    app = request.app
    download_orchestrator = DownloadOrchestrator(sql_session=session, app_params=app.state.app_params)

    if app.state.spotify_client:
        download_orchestrator.spotify_client = app.state.spotify_client
        download_orchestrator.spotify_synchronizer = SpotifySynchronizer(session, app.state.spotify_client)

    if app.state.soulseek_downloader:
        download_orchestrator.soulseek_downloader = app.state.soulseek_downloader

    return download_orchestrator