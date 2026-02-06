"""FastAPI application configuration.

Main FastAPI app instance and configuration.
"""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from ytb_dual_subtitles.api.routes import downloads, files, player, categories
from ytb_dual_subtitles.core.database import init_database
from ytb_dual_subtitles.core.settings import get_settings
from ytb_dual_subtitles.models import ApiResponse, ErrorCodes


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup and shutdown."""
    # Startup: Initialize database
    await init_database()
    print("✅ 数据库初始化完成")
    yield
    # Shutdown: Cleanup if needed
    print("🔄 应用关闭")

# Get settings
settings = get_settings()

# Create FastAPI application instance
app = FastAPI(
    title="YouTube Dual Subtitles System",
    description="API for downloading YouTube videos and generating dual-language subtitles",
    version="0.1.0",
    lifespan=lifespan,
)

# Configure CORS for frontend access
# Build allowed origins list from settings
allowed_origins = [
    settings.frontend_url,  # Configured frontend URL
    "http://localhost:5173", "http://127.0.0.1:5173",  # Vite dev server default port
    "http://localhost:3000", "http://127.0.0.1:3000",  # Alternative frontend port
    "http://localhost:3001", "http://127.0.0.1:3001",  # Alternative frontend port
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global exception handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Handle HTTP exceptions with unified response format."""
    error_code = ErrorCodes.INTERNAL_ERROR

    if exc.status_code == 400:
        error_code = ErrorCodes.VALIDATION_ERROR
    elif exc.status_code == 404:
        error_code = ErrorCodes.NOT_FOUND
    elif exc.status_code == 403:
        error_code = ErrorCodes.PERMISSION_DENIED

    response = ApiResponse.error_response(
        error_code=error_code,
        error_msg=exc.detail
    )

    return JSONResponse(
        status_code=exc.status_code,
        content=response.model_dump()
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Handle request validation errors with unified response format."""
    response = ApiResponse.error_response(
        error_code=ErrorCodes.VALIDATION_ERROR,
        error_msg=f"Validation error: {str(exc)}"
    )

    return JSONResponse(
        status_code=422,
        content=response.model_dump()
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle general exceptions with unified response format."""
    response = ApiResponse.error_response(
        error_code=ErrorCodes.INTERNAL_ERROR,
        error_msg="Internal server error"
    )

    return JSONResponse(
        status_code=500,
        content=response.model_dump()
    )


# Include API routes
app.include_router(downloads.router, prefix="/api", tags=["downloads"])
app.include_router(files.router, prefix="/api", tags=["files"])
app.include_router(player.router, prefix="/api/player", tags=["player"])
app.include_router(categories.router, prefix="/api", tags=["categories"])


@app.get("/", response_model=ApiResponse[dict[str, str]])
async def root() -> ApiResponse[dict[str, str]]:
    """Root endpoint for health check."""
    data = {"message": "YouTube Dual Subtitles System API", "status": "healthy"}
    return ApiResponse.success_response(data=data)


@app.get("/health", response_model=ApiResponse[dict[str, str]])
async def health_check() -> ApiResponse[dict[str, str]]:
    """Health check endpoint."""
    data = {"status": "healthy", "version": "0.1.0"}
    return ApiResponse.success_response(data=data)