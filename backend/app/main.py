from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from .config import get_settings
from .routers import auth, users, profile, entries, tags, catalogue, summaries, export

settings = get_settings()

limiter = Limiter(key_func=get_remote_address)

app = FastAPI(
    title="MediDiary API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router,      prefix="/api/v1/auth",      tags=["auth"])
app.include_router(users.router,     prefix="/api/v1/users",     tags=["users"])
app.include_router(profile.router,   prefix="/api/v1/profile",   tags=["profile"])
app.include_router(entries.router,   prefix="/api/v1/entries",   tags=["entries"])
app.include_router(tags.router,      prefix="/api/v1/tags",      tags=["tags"])
app.include_router(catalogue.router, prefix="/api/v1/catalogue", tags=["catalogue"])
app.include_router(summaries.router, prefix="/api/v1/summaries", tags=["summaries"])
app.include_router(export.router,    prefix="/api/v1/export",    tags=["export"])


@app.get("/health")
async def health():
    return {"status": "ok"}
