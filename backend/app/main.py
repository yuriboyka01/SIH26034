"""
SIH26034 — Legal Metrology Compliance System
FastAPI Application Entry Point

Phase 1: Foundation with auth, inspections, and image upload.
Phase 2: OpenCV preprocessing + PaddleOCR analysis pipeline.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.exceptions import register_exception_handlers
from app.core.logging import logger
from app.api import auth, inspections, images, dashboard, analysis

app = FastAPI(
    title="SIH26034 — Legal Metrology Compliance System",
    description=(
        "Software system to check compliance of Packaged Commodities under "
        "Legal Metrology (Packaged Commodities) Rules, 2011 by scanning "
        "products, images and labels."
    ),
    version="2.0.0-phase2",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register exception handlers
register_exception_handlers(app)

# Mount routers
app.include_router(auth.router)
app.include_router(inspections.router)
app.include_router(images.router)
app.include_router(dashboard.router)
app.include_router(analysis.router)


@app.get("/api/health", tags=["System"])
def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "version": "2.0.0-phase2"}


@app.on_event("startup")
def startup_event():
    logger.info("SIH26034 Legal Metrology Compliance System starting up...")
    logger.info(f"CORS origins: {settings.cors_origins_list}")
    logger.info(f"Upload directory: {settings.UPLOAD_DIR}")
    logger.info(f"Max upload size: {settings.MAX_UPLOAD_SIZE / (1024*1024):.0f}MB")

