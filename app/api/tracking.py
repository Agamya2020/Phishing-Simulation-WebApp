"""Tracking endpoints: open pixel + click redirect."""
import json
import logging
from fastapi import APIRouter, Depends
from fastapi.responses import Response, RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from app.core.db import get_db
from app.models.models import Campaign, CampaignEvent

router = APIRouter(prefix="/track", tags=["tracking"])
logger = logging.getLogger(__name__)

# 1x1 transparent GIF
PIXEL_GIF = b"GIF89a\x01\x00\x01\x00\x80\xff\x00\xff\xff\xff\x00\x00\x00!\xf9\x04\x00\x00\x00\x00\x00,\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;"


@router.get("/open/{campaign_id}/{user_id}")
async def track_open(campaign_id: str, user_id: str, db: AsyncSession = Depends(get_db)):
    """Record email-open event and return a 1x1 tracking pixel."""
    try:
        event = CampaignEvent(
            campaign_id=campaign_id,
            user_id=user_id,
            user_email="",
            event_type="opened",
        )
        db.add(event)
        await db.execute(
            update(Campaign)
            .where(Campaign.id == campaign_id)
            .values(open_count=Campaign.open_count + 1)
        )
        await db.commit()
        logger.info(f"[OPEN] campaign={campaign_id} user={user_id}")
    except Exception as e:
        logger.error(f"track_open error: {e}")
    return Response(content=PIXEL_GIF, media_type="image/gif")


@router.get("/click/{campaign_id}/{user_id}")
async def track_click(campaign_id: str, user_id: str, db: AsyncSession = Depends(get_db)):
    """Record click event and redirect to the phishing landing page."""
    try:
        event = CampaignEvent(
            campaign_id=campaign_id,
            user_id=user_id,
            user_email="",
            event_type="clicked",
        )
        db.add(event)
        await db.execute(
            update(Campaign)
            .where(Campaign.id == campaign_id)
            .values(click_count=Campaign.click_count + 1)
        )
        await db.commit()
        logger.info(f"[CLICK] campaign={campaign_id} user={user_id}")
    except Exception as e:
        logger.error(f"track_click error: {e}")
    return RedirectResponse(url=f"/landing/{campaign_id}/{user_id}")


@router.post("/report/{campaign_id}/{user_id}")
async def track_report(campaign_id: str, user_id: str, db: AsyncSession = Depends(get_db)):
    """Record report event (user reported the phishing email)."""
    try:
        event = CampaignEvent(
            campaign_id=campaign_id,
            user_id=user_id,
            user_email="",
            event_type="reported",
        )
        db.add(event)
        await db.execute(
            update(Campaign)
            .where(Campaign.id == campaign_id)
            .values(report_count=Campaign.report_count + 1)
        )
        await db.commit()
        logger.info(f"[REPORT] campaign={campaign_id} user={user_id}")
    except Exception as e:
        logger.error(f"track_report error: {e}")
    return {"ok": True}


@router.post("/creds/{campaign_id}/{user_id}")
async def track_creds(campaign_id: str, user_id: str, db: AsyncSession = Depends(get_db)):
    """Record credentials-submitted event."""
    try:
        event = CampaignEvent(
            campaign_id=campaign_id,
            user_id=user_id,
            user_email="",
            event_type="creds_entered",
        )
        db.add(event)
        await db.execute(
            update(Campaign)
            .where(Campaign.id == campaign_id)
            .values(creds_count=Campaign.creds_count + 1)
        )
        await db.commit()
        logger.info(f"[CREDS] campaign={campaign_id} user={user_id}")
    except Exception as e:
        logger.error(f"track_creds error: {e}")
    return {"ok": True}
