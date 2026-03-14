import logging

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.api.v1.router import api_router

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Uygulama başlatma ve kapatma işlemleri."""
    from app.core.database import engine, Base

    # Import all models so Base.metadata knows about them
    import app.models.patient  # noqa: F401
    import app.models.study  # noqa: F401
    import app.models.nodule  # noqa: F401
    import app.models.report  # noqa: F401
    import app.models.user  # noqa: F401

    # Development fallback: create tables if they don't exist.
    # Production should use: alembic upgrade head
    if settings.debug:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Veritabanı tabloları kontrol edildi (debug mode)")

    yield

    await engine.dispose()
    logger.info("Veritabanı bağlantısı kapatıldı")


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="AlpCAN — Akciğer Kanseri Erken Tespiti İçin YZ Karar Destek Platformu",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api/v1")


@app.get("/")
async def root():
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "status": "running",
    }
