from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI
from contextlib import asynccontextmanager
import dotenv
import os

from soulripper.api import tracks_route
from soulripper.utils import AppParams, extract_app_params
from soulripper.api_clients import SpotifyClient, SpotifyUserData
from soulripper.downloaders import SoulseekDownloader

@asynccontextmanager
async def lifespan(app: FastAPI):
    config_filepath = __file__.replace("backend/src/soulripper/api/bringup.py", "config.yaml")
    app_params: AppParams = extract_app_params(config_filepath)
    
    app.state.app_params = app_params
    app.state.engine = create_async_engine(f"sqlite+aiosqlite:///{app_params.database_path}")
    app.state.sessionmaker = async_sessionmaker(
        app.state.engine,
        expire_on_commit=False,
        class_=AsyncSession
    )

    app.state.spotify_client = None
    app.state.spotify_synchronizer = None
    app.state.soulseek_downloader = None

    dotenv.load_dotenv()
    SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
    SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")
    SPOTIFY_REDIRECT_URI = os.getenv("SPOTIFY_REDIRECT_URI")
    if SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET and SPOTIFY_REDIRECT_URI:
        app.state.spotify_client = await SpotifyClient.init(SpotifyUserData(
            CLIENT_ID=SPOTIFY_CLIENT_ID, 
            CLIENT_SECRET=SPOTIFY_CLIENT_SECRET, 
            REDIRECT_URI=SPOTIFY_REDIRECT_URI, 
            SCOPE=app_params.spotify_scope
        ))

    SLSKD_API_KEY = os.getenv("SLSKD_API_KEY")
    if SLSKD_API_KEY:
        app.state.soulseek_downloader = SoulseekDownloader(SLSKD_API_KEY, app_params)

    yield

    await app.state.engine.dispose()

app = FastAPI(lifespan=lifespan)
app.include_router(tracks_route.router)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
