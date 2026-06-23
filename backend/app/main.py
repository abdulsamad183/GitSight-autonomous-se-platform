import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.endpoints import auth, health, jobs, repositories, version
from app.core.config import get_settings
from app.core.logging import configure_logging
from app.middleware.request_logging import RequestLoggingMiddleware

settings = get_settings()
configure_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting %s v%s", settings.service_name, settings.version)
    yield
    logger.info("Shutting down %s", settings.service_name)


app = FastAPI(
    title=settings.service_name,
    version=settings.version,
    lifespan=lifespan,
)

app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, tags=["health"])
app.include_router(version.router, prefix=settings.api_v1_prefix, tags=["version"])
app.include_router(auth.router, prefix=f"{settings.api_v1_prefix}/auth", tags=["auth"])
app.include_router(
    repositories.router,
    prefix=f"{settings.api_v1_prefix}/repositories",
    tags=["repositories"],
)
app.include_router(jobs.router, prefix=f"{settings.api_v1_prefix}/jobs", tags=["jobs"])
