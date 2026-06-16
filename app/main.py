import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.core.db import engine, Base
from app.api.campaigns import router as campaigns_router
from app.api.tracking import router as tracking_router
from app.api.data import users_router, groups_router, templates_router, departments_router
from app.seed import seed
from app.core.db import AsyncSessionLocal

logging.basicConfig(level=logging.INFO)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create all tables on startup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    # Seed with mock data if needed
    async with AsyncSessionLocal() as db:
        await seed(db)
    yield
    await engine.dispose()


app = FastAPI(
    title="PhishGuard API",
    version="1.0.0",
    description="Backend for the PhishGuard Phishing Simulation Platform",
    lifespan=lifespan,
    redirect_slashes=False,
)

# Include all routers
app.include_router(campaigns_router, prefix="/api")
app.include_router(tracking_router)  # /track/* – no /api prefix for email links
app.include_router(users_router, prefix="/api")
app.include_router(groups_router, prefix="/api")
app.include_router(templates_router, prefix="/api")
app.include_router(departments_router, prefix="/api")


@app.get("/health")
async def health():
    return {"status": "ok", "service": "PhishGuard API"}
