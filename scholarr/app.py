"""Main FastAPI application factory for Scholarr."""

import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from scholarr.api.v1.router import router as v1_router
from scholarr.core.config import settings
from scholarr.signalr import ConnectionManager

logger = logging.getLogger(__name__)

# Template engine — looks in scholarr/templates/
TEMPLATE_DIR = os.path.join(os.path.dirname(__file__), "templates")
templates = Jinja2Templates(directory=TEMPLATE_DIR)
# Make the API key and settings available to all templates
templates.env.globals["api_key"] = ""  # Will be updated in create_app()


async def startup_event():
    """Initialize on application startup."""
    logger.info("Scholarr starting up (v0.1.0)")

    # Run Alembic migrations if available
    try:
        from scholarr.db.migrations import run_migrations
        await run_migrations()
        logger.info("Database migrations completed")
    except Exception as e:
        logger.warning(f"Could not run migrations: {e}")

    # Initialize background scheduler
    if settings.enable_scheduler:
        try:
            from scholarr.services.scheduler import scheduler
            scheduler.start()
            logger.info("Background scheduler started")
        except Exception as e:
            logger.error(f"Failed to start scheduler: {e}")

    # Start file watcher for inbox monitoring
    if settings.enable_file_watcher:
        try:
            from scholarr.services.file_watcher import file_watcher
            await file_watcher.start()
            logger.info("File watcher started")
        except Exception as e:
            logger.error(f"Failed to start file watcher: {e}")


async def shutdown_event():
    """Cleanup on application shutdown."""
    logger.info("Scholarr shutting down")

    try:
        from scholarr.services.scheduler import scheduler
        if scheduler.running:
            scheduler.shutdown()
            logger.info("Background scheduler stopped")
    except Exception as e:
        logger.warning(f"Error stopping scheduler: {e}")

    try:
        from scholarr.services.file_watcher import file_watcher
        await file_watcher.stop()
        logger.info("File watcher stopped")
    except Exception as e:
        logger.warning(f"Error stopping file watcher: {e}")

    try:
        from scholarr.db.session import async_engine
        await async_engine.dispose()
        logger.info("Database connection closed")
    except Exception as e:
        logger.warning(f"Error closing database: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for FastAPI."""
    await startup_event()
    yield
    await shutdown_event()


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""

    app = FastAPI(
        title="Scholarr",
        version="0.1.0",
        description="Self-hosted academic file management system",
        lifespan=lifespan,
        redirect_slashes=False,
    )

    # Inject API key into all templates globally
    templates.env.globals["api_key"] = settings.api_key

    # Sentry error tracking (optional)
    if settings.sentry_dsn:
        import sentry_sdk
        sentry_sdk.init(
            dsn=settings.sentry_dsn,
            environment=settings.environment,
            traces_sample_rate=0.1,
        )

    # Security middleware — TrustedHost (skip in non-production to allow test client)
    if settings.environment == "production":
        app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.allowed_hosts)

    # CORS for API access
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Security headers on every response
    @app.middleware("http")
    async def add_security_headers(request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        if settings.environment == "production":
            response.headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains"
            )
        return response

    # --- API routes ---
    app.include_router(v1_router, prefix="/api/v1")

    # --- WebSocket for real-time updates ---
    connection_manager = ConnectionManager()

    @app.websocket("/ws")
    async def websocket_endpoint(websocket: WebSocket):
        await connection_manager.connect(websocket)
        try:
            while True:
                data = await websocket.receive_text()
                await websocket.send_text(data)
        except WebSocketDisconnect:
            await connection_manager.disconnect(websocket)
        except Exception as e:
            logger.error(f"WebSocket error: {e}")
            await connection_manager.disconnect(websocket)

    app.state.connection_manager = connection_manager

    # --- Static files (CSS, images) ---
    static_dir = os.path.join(os.path.dirname(__file__), "static")
    if os.path.exists(static_dir):
        app.mount("/static", StaticFiles(directory=static_dir), name="static")

    # --- Page routes (Jinja2 templates) ---
    @app.get("/", include_in_schema=False)
    async def index(request: Request):
        return templates.TemplateResponse("pages/dashboard.html", {"request": request})

    @app.get("/courses", include_in_schema=False)
    async def courses_page(request: Request):
        return templates.TemplateResponse("pages/courses.html", {"request": request})

    @app.get("/courses/add", include_in_schema=False)
    async def add_course_page(request: Request):
        return templates.TemplateResponse("pages/add_course.html", {"request": request})

    @app.get("/courses/{course_id}", include_in_schema=False)
    async def course_detail_page(request: Request, course_id: int):
        return templates.TemplateResponse(
            "pages/course_detail.html", {"request": request, "course_id": course_id}
        )

    @app.get("/academic-items", include_in_schema=False)
    async def academic_items_page(request: Request):
        return templates.TemplateResponse("pages/academic_items.html", {"request": request})

    @app.get("/semesters", include_in_schema=False)
    async def semesters_page(request: Request):
        return templates.TemplateResponse("pages/semesters.html", {"request": request})

    @app.get("/calendar", include_in_schema=False)
    async def calendar_page(request: Request):
        return templates.TemplateResponse("pages/calendar.html", {"request": request})

    @app.get("/activity", include_in_schema=False)
    async def activity_page(request: Request):
        return templates.TemplateResponse("pages/activity.html", {"request": request})

    @app.get("/library", include_in_schema=False)
    async def library_page(request: Request):
        return templates.TemplateResponse("pages/library.html", {"request": request})

    @app.get("/gpa", include_in_schema=False)
    async def gpa_page(request: Request):
        return templates.TemplateResponse("pages/gpa_calculator.html", {"request": request})

    @app.get("/system", include_in_schema=False)
    async def system_page(request: Request):
        return templates.TemplateResponse("pages/system.html", {"request": request})

    @app.get("/study-timer", include_in_schema=False)
    async def study_timer_page(request: Request):
        return templates.TemplateResponse("pages/study_timer.html", {"request": request})

    @app.get("/settings", include_in_schema=False)
    async def settings_page(request: Request):
        return templates.TemplateResponse("pages/settings.html", {"request": request})

    @app.get("/setup", include_in_schema=False)
    async def setup_page(request: Request):
        return templates.TemplateResponse("pages/first_run.html", {"request": request})

    # --- Health check ---
    @app.get("/health")
    async def health():
        return {"status": "ok", "version": "0.1.0"}

    # --- Exception handlers (proper HTTP status codes) ---
    from scholarr.core.exceptions import (
        ValidationException,
        NotFoundError,
        UnauthorizedError,
        ForbiddenError,
    )

    @app.exception_handler(ValidationException)
    async def validation_exception_handler(request: Request, exc: ValidationException):
        return JSONResponse(
            status_code=422,
            content={"detail": str(exc), "error_code": "validation_error"},
        )

    @app.exception_handler(NotFoundError)
    async def not_found_exception_handler(request: Request, exc: NotFoundError):
        return JSONResponse(
            status_code=404,
            content={"detail": str(exc), "error_code": "not_found"},
        )

    @app.exception_handler(UnauthorizedError)
    async def unauthorized_exception_handler(request: Request, exc: UnauthorizedError):
        return JSONResponse(
            status_code=401,
            content={"detail": str(exc), "error_code": "unauthorized"},
        )

    @app.exception_handler(ForbiddenError)
    async def forbidden_exception_handler(request: Request, exc: ForbiddenError):
        return JSONResponse(
            status_code=403,
            content={"detail": str(exc), "error_code": "forbidden"},
        )

    from fastapi.exceptions import RequestValidationError
    from starlette.exceptions import HTTPException as StarletteHTTPException

    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        if isinstance(exc, (RequestValidationError, StarletteHTTPException)):
            raise exc
        logger.error(f"Unhandled exception: {exc}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"detail": "An internal server error occurred", "error_code": "internal_error"},
        )

    logger.info("FastAPI application created successfully")
    return app


app = create_app()
