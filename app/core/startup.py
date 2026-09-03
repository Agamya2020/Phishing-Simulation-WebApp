import logging

from sqlalchemy import text

from app.core.config import settings
from app.core.db import engine


logger = logging.getLogger("phishguard.startup")


async def verify_database():
    async with engine.connect() as connection:
        await connection.execute(text("SELECT 1"))

    logger.info("Database connection verified")


def log_environment():
    logger.info("PhishGuard environment: %s", settings.APP_ENV)
