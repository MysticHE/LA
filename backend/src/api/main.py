import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from src.api.routes import router
from src.api.claude_routes import router as claude_router
from src.api.generate_routes import router as generate_router
from src.api.openai_routes import router as openai_router
from src.middleware.rate_limiter import RateLimitMiddleware, RateLimitConfig
from src.middleware.security_headers import SecurityHeadersMiddleware, SecurityHeadersConfig

load_dotenv()

app = FastAPI(
    title="LinkedIn Content Generator API",
    description="Analyze GitHub projects and generate LinkedIn post content",
    version="1.0.0",
)

# CORS origins - add your Render frontend URL here
cors_origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

# Add production frontend URL from environment
frontend_url = os.getenv("FRONTEND_URL")
if frontend_url:
    cors_origins.append(frontend_url)

# Allow all origins in development (when ALLOW_ALL_ORIGINS is set)
if os.getenv("ALLOW_ALL_ORIGINS", "").lower() == "true":
    cors_origins = ["*"]

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

app.include_router(router, prefix="/api")
app.include_router(claude_router, prefix="/api")
app.include_router(generate_router, prefix="/api")
app.include_router(openai_router, prefix="/api")


@app.get("/")
async def root():
    return {"message": "LinkedIn Content Generator API", "docs": "/docs"}
