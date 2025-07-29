"""Main FastAPI application entry point for RequestPayment system."""

import os
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from loguru import logger

from .api.v1.router import router as api_v1_router
from .core.config import get_settings
from .core.exceptions import setup_exception_handlers
from .services import file_manager


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Manage application lifespan events."""
    # Startup
    logger.info("Starting RequestPayment application...")

    # 初始化檔案管理服務（自動創建必要的目錄）
    logger.info("Initializing file storage directories...")
    file_manager._ensure_directories()
    logger.info("File storage directories initialized successfully")
    
    # 確保uploads目錄存在
    os.makedirs("uploads", exist_ok=True)
    os.makedirs("uploads/images", exist_ok=True)
    os.makedirs("uploads/temp", exist_ok=True)
    logger.info("All upload directories created successfully")

    # 創建靜態檔案目錄
    os.makedirs("static", exist_ok=True)

    logger.info("Application initialized successfully")

    yield

    # Shutdown
    logger.info("Shutting down RequestPayment application...")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application.

    Returns:
        FastAPI: The configured application instance.
    """
    settings = get_settings()

    app = FastAPI(
        title="RequestPayment API",
        description="A modern payment request handling system",
        version="0.1.0",
        docs_url="/docs",  # Enable docs for testing
        redoc_url="/redoc",  # Enable redoc for testing
        lifespan=lifespan,
    )

    # Add middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.get_cors_origins_list(),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Only add TrustedHostMiddleware in production
    if settings.environment != "test":
        app.add_middleware(
            TrustedHostMiddleware,
            allowed_hosts=settings.get_allowed_hosts_list(),
        )

    # Setup exception handlers
    setup_exception_handlers(app)

    # Mount static files
    app.mount("/static", StaticFiles(directory="static"), name="static")

    # Include routers
    app.include_router(
        api_v1_router,
        prefix="/api/v1",
        tags=["v1"]
    )

    @app.get("/health")
    async def health_check():
        """Health check endpoint."""
        return {"status": "healthy", "version": "0.1.0"}

    @app.get("/")
    async def read_index():
        """提供首頁"""
        return FileResponse('static/index.html')



    return app


# Create the application instance
app = create_app()


if __name__ == "__main__":
    import uvicorn

    settings = get_settings()
    uvicorn.run(
        "src.request_payment.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.environment == "development",
        log_level=settings.log_level.lower(),
    )
