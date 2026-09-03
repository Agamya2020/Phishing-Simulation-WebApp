import asyncio
import logging
from datetime import datetime, timezone

from sqlalchemy import select

from app.core.db import AsyncSessionLocal
from app.models.models import Campaign
from app.tasks.email_worker import dispatch_campaign_emails


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

logger = logging.getLogger("phishguard.scheduler")

POLL_INTERVAL_SECONDS = 30


def parse_scheduled_time(value: str | None) -> datetime | None:
    if not value:
        return None

    try:
        cleaned = value.strip()
        if cleaned.endswith("Z"):
            cleaned = cleaned[:-1] + "+00:00"

        scheduled = datetime.fromisoformat(cleaned)
        if scheduled.tzinfo is None:
            scheduled = scheduled.replace(tzinfo=timezone.utc)

        return scheduled.astimezone(timezone.utc)
    except ValueError:
        logger.error("Invalid scheduled_at value: %s", value)
        return None


async def claim_due_campaigns() -> list[str]:
    now = datetime.now(timezone.utc)
    campaign_ids: list[str] = []

    async with AsyncSessionLocal() as db:
        try:
            result = await db.execute(
                select(Campaign)
                .where(Campaign.status == "scheduled")
                .with_for_update(skip_locked=True)
            )
            campaigns = result.scalars().all()

            for campaign in campaigns:
                scheduled_time = parse_scheduled_time(campaign.scheduled_at)
                if scheduled_time is None or scheduled_time > now:
                    continue

                campaign.status = "processing"
                campaign_ids.append(campaign.id)

            await db.commit()
        except Exception:
            await db.rollback()
            logger.exception("Failed checking scheduled campaigns")
            return []

    return campaign_ids


async def process_due_campaigns():
    campaign_ids = await claim_due_campaigns()
    if not campaign_ids:
        return

    logger.info("Found %s scheduled campaign(s)", len(campaign_ids))

    for campaign_id in campaign_ids:
        logger.info("Dispatching scheduled campaign %s", campaign_id)
        try:
            await dispatch_campaign_emails(campaign_id)
        except Exception:
            logger.exception("Campaign %s failed", campaign_id)

            async with AsyncSessionLocal() as db:
                result = await db.execute(
                    select(Campaign).where(Campaign.id == campaign_id)
                )
                campaign = result.scalar_one_or_none()
                if campaign:
                    campaign.status = "failed"
                    await db.commit()


async def scheduler_loop():
    logger.info("PhishGuard scheduler started")

    while True:
        try:
            await process_due_campaigns()
        except Exception:
            logger.exception("Unexpected scheduler error")

        await asyncio.sleep(POLL_INTERVAL_SECONDS)


async def main():
    await scheduler_loop()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Scheduler stopped")
