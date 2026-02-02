import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from src.api.routes import router
from src.api.claude_routes import router as claude_router, get_key_storage as get_claude_key_storage
from src.api.generate_routes import router as generate_router
from src.api.openai_routes import router as openai_router, get_openai_key_storage
from src.api.gemini_routes import router as gemini_router, get_gemini_key_storage
from src.api.image_routes import router as image_router
from src.api.linkedin_routes import router as linkedin_router
from src.api.error_handlers import register_error_handlers
from src.middleware.rate_limiter import RateLimitMiddleware, RateLimitConfig
from src.middleware.security_headers import SecurityHeadersMiddleware, SecurityHeadersConfig
from src.middleware.session_middleware import SessionMiddleware
from src.services.session_manager import get_session_manager
from src.tasks.cleanup import get_cleanup_task

load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler for startup and shutdown events."""
    # Startup: Configure and start the cleanup task
    cleanup_task = get_cleanup_task()

    # Register key storages for cleanup on session expiry
    cleanup_task.add_key_storage(get_claude_key_storage())
    cleanup_task.add_key_storage(get_openai_key_storage())
    cleanup_task.add_key_storage(get_gemini_key_storage())

    # Start the background cleanup task (runs every hour)
    await cleanup_task.start()

    yield

    # Shutdown: Stop the cleanup task
    await cleanup_task.stop()


app = FastAPI(
    title="LinkedIn Content Generator API",
    description="Analyze GitHub projects and generate LinkedIn post content",
    version="1.0.0",
    lifespan=lifespan,
)

# Register secure error handlers
register_error_handlers(app)

# CORS origins - explicitly configured for security
cors_origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

# Add production frontend URL from environment (required for deployment)
frontend_url = os.getenv("FRONTEND_URL")
if frontend_url:
    cors_origins.append(frontend_url)

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rate limiting configuration from environment or defaults
rate_limit_config = RateLimitConfig(
    auth_limit=int(os.getenv("RATE_LIMIT_AUTH", "100")),
    auth_window_seconds=60,
    generation_limit=int(os.getenv("RATE_LIMIT_GENERATION", "20")),
    generation_window_seconds=60,
)
app.add_middleware(RateLimitMiddleware, config=rate_limit_config)

# Security headers - HSTS disabled in development
is_development = os.getenv("ENVIRONMENT", "development").lower() == "development"
security_config = SecurityHeadersConfig(
    include_hsts=not is_development
)
app.add_middleware(SecurityHeadersMiddleware, config=security_config)

# Session middleware - validates session expiry and returns 401 for expired sessions
app.add_middleware(SessionMiddleware, session_manager=get_session_manager())

app.include_router(router, prefix="/api")
app.include_router(claude_router, prefix="/api")
app.include_router(generate_router, prefix="/api")
app.include_router(openai_router, prefix="/api")
app.include_router(gemini_router, prefix="/api")
app.include_router(image_router, prefix="/api")
app.include_router(linkedin_router, prefix="/api")


@app.get("/")
async def root():
    return {"message": "LinkedIn Content Generator API", "docs": "/docs"}
