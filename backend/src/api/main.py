import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from src.api.routes import router
from src.api.claude_routes import router as claude_router
from src.api.generate_routes import router as generate_router

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

app.include_router(router, prefix="/api")
app.include_router(claude_router, prefix="/api")
app.include_router(generate_router, prefix="/api")


@app.get("/")
async def root():
    return {"message": "LinkedIn Content Generator API", "docs": "/docs"}
