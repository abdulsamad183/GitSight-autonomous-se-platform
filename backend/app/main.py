import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1.endpoints import auth, health, jobs, repositories, version
from app.core.config import get_settings
from app.core.logging import configure_logging
from app.middleware.request_logging import RequestLoggingMiddleware
from app.services.exceptions import (
    AnalysisError,
    AppError,
    AuthenticationError,
    ConflictError,
    ForbiddenError,
    IndexingError,
    LLMProviderError,
    NotFoundError,
    ToolPlannerError,
    ValidationError,
)

settings = get_settings()
configure_logging()
logger = logging.getLogger(__name__)

APP_ERROR_STATUS: dict[type[AppError], int] = {
    AuthenticationError: 401,
    ForbiddenError: 403,
    NotFoundError: 404,
    ConflictError: 409,
    ValidationError: 422,
    AnalysisError: 500,
    IndexingError: 500,
    LLMProviderError: 503,
    ToolPlannerError: 500,
}


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings.validate_production_settings()
    logger.info(
        "Starting %s v%s (env=%s, cookie_secure=%s)",
        settings.service_name,
        settings.version,
        settings.env,
        settings.cookie_secure,
    )
    yield
    logger.info("Shutting down %s", settings.service_name)


app = FastAPI(
    title=settings.service_name,
    version=settings.version,
    lifespan=lifespan,
    docs_url="/docs" if settings.is_development else None,
    redoc_url="/redoc" if settings.is_development else None,
    openapi_url="/openapi.json" if settings.is_development else None,
)

app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(AppError)
async def app_error_handler(_request: Request, exc: AppError) -> JSONResponse:
    status_code = 500
    for error_type, code in APP_ERROR_STATUS.items():
        if isinstance(exc, error_type):
            status_code = code
            break
    return JSONResponse(status_code=status_code, content={"detail": str(exc)})


@app.exception_handler(Exception)
async def unhandled_exception_handler(_request: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unhandled error: %s", exc)
    detail = str(exc) if settings.is_development else "Internal server error"
    return JSONResponse(status_code=500, content={"detail": detail})


app.include_router(health.router, tags=["health"])
app.include_router(version.router, prefix=settings.api_v1_prefix, tags=["version"])
app.include_router(auth.router, prefix=f"{settings.api_v1_prefix}/auth", tags=["auth"])
app.include_router(
    repositories.router,
    prefix=f"{settings.api_v1_prefix}/repositories",
    tags=["repositories"],
)
app.include_router(jobs.router, prefix=f"{settings.api_v1_prefix}/jobs", tags=["jobs"])
