import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from app.core.config import settings
from app.core.db import engine
from app.core.security import require_admin, require_csrf
from app.core.startup import log_environment, verify_database
from app.api.auth import router as auth_router
from app.api.campaigns import router as campaigns_router
from app.api.tracking import router as tracking_router
from app.api.data import users_router, groups_router, templates_router, departments_router
from app.web.routes import router as web_router

logging.basicConfig(level=logging.INFO)


@asynccontextmanager
async def lifespan(app: FastAPI):
    log_environment()
    try:
        await verify_database()
        yield
    finally:
        await engine.dispose()


app = FastAPI(
    title="PhishGuard API",
    version="1.0.0",
    description="Backend for the PhishGuard Phishing Simulation Platform",
    lifespan=lifespan,
    redirect_slashes=False,
    debug=settings.DEBUG,
)


@app.middleware("http")
async def csrf_protection(request: Request, call_next):
    protected_methods = {"POST", "PUT", "PATCH", "DELETE"}
    public_post_paths = {"/api/auth/login"}
    path = request.url.path

    if (
        request.method in protected_methods
        and path.startswith("/api/")
        and path not in public_post_paths
    ):
        try:
            admin = await require_admin(request)
            await require_csrf(request, admin)
        except HTTPException as exc:
            return JSONResponse(
                status_code=exc.status_code,
                content={"detail": exc.detail},
                headers=exc.headers,
            )

    return await call_next(request)


@app.middleware("http")
async def security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = (
        "camera=(), microphone=(), geolocation=()"
    )
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "script-src 'self'; "
        "style-src 'self' 'unsafe-inline'; "
        "img-src 'self' data:; "
        "font-src 'self'; "
        "connect-src 'self'; "
        "frame-ancestors 'none'; "
        "base-uri 'self'; "
        "form-action 'self'"
    )
    return response

app.mount(
    "/static",
    StaticFiles(directory=str(Path(__file__).resolve().parent / "static")),
    name="static",
)

# Include all routers
app.include_router(auth_router, prefix="/api")
app.include_router(campaigns_router, prefix="/api")
app.include_router(tracking_router)  # /track/* – no /api prefix for email links
app.include_router(users_router, prefix="/api")
app.include_router(groups_router, prefix="/api")
app.include_router(templates_router, prefix="/api")
app.include_router(departments_router, prefix="/api")
app.include_router(web_router)


@app.get("/health")
async def health():
    return {"status": "ok", "service": "PhishGuard API"}
