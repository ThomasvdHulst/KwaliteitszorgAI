"""FastAPI application entry point."""

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.config import get_settings

# Configureer logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

settings = get_settings()

app = FastAPI(
    title=settings.api_title,
    version=settings.api_version,
    description=settings.api_description,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# CORS middleware - expliciet configureren welke headers toegestaan zijn
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["X-API-Key", "Content-Type", "Accept"],
    expose_headers=["X-Request-ID"],
)

# Import routes na app initialisatie om circulaire imports te voorkomen
from api.routes import chat, eisen, health  # noqa: E402

# Include routers
app.include_router(health.router)
app.include_router(eisen.router)
app.include_router(chat.router)


@app.on_event("startup")
async def startup_event():
    """Log configuratie bij opstarten."""
    logger.info("OnSpectAI API v%s gestart", settings.api_version)
    logger.info("Model: %s", settings.model_name)
    logger.info("Database: %s", settings.database_path)
    logger.info("CORS origins: %s", settings.cors_origins_list)

    if not settings.api_key:
        logger.warning(
            "WAARSCHUWING: Geen API key geconfigureerd! "
            "De API draait in development mode zonder authenticatie."
        )


@app.get("/", include_in_schema=False)
async def root():
    """Root endpoint redirect to docs."""
    return {
        "message": "OnSpectAI API",
        "version": settings.api_version,
        "docs": "/docs",
        "health": "/health",
    }
