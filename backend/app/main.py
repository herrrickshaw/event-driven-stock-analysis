"""
FastAPI application factory and configuration.
"""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from config.settings import settings
from models import init_db
from routers import portfolio, risk, rebalance, alerts, reports
from utils import APIError, setup_logging, get_logger

logger = get_logger(__name__)


def create_app() -> FastAPI:
    """
    Create and configure FastAPI application.

    Returns:
        Configured FastAPI application
    """
    # Setup logging
    setup_logging()

    # Create app
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description="Event-driven stock analysis and portfolio management API",
        debug=settings.debug,
    )

    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Initialize database
    init_db()
    logger.info("Database initialized")

    # Register routers. Each router already declares its full path prefix
    # (e.g. "/api/alerts"), so no additional prefix is added here -- doing so
    # previously double-prefixed every route to "/api/api/...".
    app.include_router(portfolio.router)
    app.include_router(risk.router)
    app.include_router(rebalance.router)
    app.include_router(alerts.router)
    app.include_router(reports.router)

    logger.info("API routers registered")

    # Exception handlers
    @app.exception_handler(APIError)
    async def api_error_handler(request: Request, exc: APIError):
        """Handle API errors."""
        logger.error(f"API Error: {exc.detail}", extra={"path": request.url.path})
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail, "path": request.url.path},
        )

    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        """Handle unexpected exceptions."""
        logger.error(f"Unhandled exception: {str(exc)}", exc_info=exc)
        return JSONResponse(
            status_code=500,
            content={
                "detail": "Internal server error",
                "path": request.url.path,
            },
        )

    # Health check endpoint
    @app.get("/api/health", tags=["system"])
    async def health_check():
        """System health check endpoint."""
        return {
            "status": "ok",
            "app": settings.app_name,
            "version": settings.app_version,
        }

    # Root endpoint
    @app.get("/", tags=["system"])
    async def root():
        """Root endpoint with API information."""
        return {
            "app": settings.app_name,
            "version": settings.app_version,
            "docs": "/docs",
            "openapi": "/openapi.json",
        }

    @app.on_event("startup")
    async def startup_event():
        """Run on application startup."""
        logger.info(f"Starting {settings.app_name} v{settings.app_version}")
        logger.info(f"Database: {settings.database_url.split('@')[-1]}")

    @app.on_event("shutdown")
    async def shutdown_event():
        """Run on application shutdown."""
        logger.info(f"Shutting down {settings.app_name}")

    return app


# Create app instance
app = create_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
