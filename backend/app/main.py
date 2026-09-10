"""
SIH26034 — Legal Metrology Compliance System
FastAPI Application Entry Point

Phase 1: Foundation with auth, inspections, and image upload.
Phase 2: OpenCV preprocessing + PaddleOCR analysis pipeline.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import sys

from app.core.runtime import verify_runtime
# Verify runtime very early before doing any complex imports
verify_runtime()

from app.core.config import settings
from app.core.exceptions import register_exception_handlers
from app.core.logging import logger
from app.api import auth, inspections, images, dashboard, analysis, product_info, compliance, reports, users

app = FastAPI(
    title="SIH26034 — Legal Metrology Compliance System",
    description=(
        "Software system to check compliance of Packaged Commodities under "
        "Legal Metrology (Packaged Commodities) Rules, 2011 by scanning "
        "products, images and labels."
    ),
    version="4.0.0-phase4",
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
app.include_router(product_info.router)
app.include_router(compliance.router)
app.include_router(reports.router)
app.include_router(users.router)


@app.get("/api/health", tags=["System"])
def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "version": "4.0.0-phase4"}


@app.on_event("startup")
def startup_event():
    logger.info("SIH26034 Legal Metrology Compliance System starting up...")
    logger.info(f"CORS origins: {settings.cors_origins_list}")
    logger.info(f"Upload directory: {settings.UPLOAD_DIR}")
    logger.info(f"Max upload size: {settings.MAX_UPLOAD_SIZE / (1024*1024):.0f}MB")

    # JWT warning
    if settings.JWT_SECRET == "change-this-to-a-long-random-secret-key":
        logger.warning("SECURITY WARNING: Using default JWT_SECRET. This is unsafe for production!")

    # Groq status
    if settings.GROQ_API_KEY:
        logger.info(f"Groq API config: Key is present. Model: {settings.GROQ_MODEL}")
    else:
        logger.warning("Groq API config: GROQ_API_KEY is not set. Falling back to Regex extraction only.")

    # PaddleOCR is now lazily initialized during the first analysis request.
    # Preloading on startup in constrained environments (like Render Free Tier with 512MB RAM)
    # caused OOM kills before the server could pass health checks.
    logger.info("PaddleOCR initialization deferred to first analysis request (lazy loading).")

