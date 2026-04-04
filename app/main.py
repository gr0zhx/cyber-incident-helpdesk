"""FastAPI application entry point."""
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.routes import router
from app.utils.logger import configure_logging


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging()
    yield


app = FastAPI(
    title="Helpdesk Keamanan Siber Pusdatin",
    description="Sistem helpdesk multi-agent untuk pra-triase insiden keamanan siber",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(router)


@app.get("/")
def root() -> dict:
    return {"status": "ok"}


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "service": "helpdesk-api"}
