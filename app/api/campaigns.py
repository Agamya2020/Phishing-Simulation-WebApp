"""Campaigns router: create, list, update, delete, dispatch."""
from fastapi import APIRouter, Depends, BackgroundTasks, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from app.core.db import get_db
from app.models.models import Campaign, Group, User
from app.schemas.schemas import CampaignCreate, CampaignOut, CampaignUpdate
from app.tasks.email_worker import dispatch_campaign_emails

router = APIRouter(prefix="/campaigns", tags=["campaigns"])


@router.get("", response_model=list[CampaignOut])
async def list_campaigns(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Campaign).order_by(Campaign.created_at.desc()))
    return result.scalars().all()


@router.get("/{campaign_id}", response_model=CampaignOut)
async def get_campaign(campaign_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Campaign).where(Campaign.id == campaign_id))
    campaign = result.scalar_one_or_none()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    return campaign


@router.post("", response_model=CampaignOut)
async def create_campaign(
    payload: CampaignCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    # Resolve target users: start with explicitly selected users,
    # then add all members from selected groups not already included.
    target_ids = set(payload.target_user_ids)

    if payload.group_ids:
        result = await db.execute(select(Group).where(Group.id.in_(payload.group_ids)))
        groups = result.scalars().all()
        for g in groups:
            target_ids.update(g.member_ids or [])

    target_list = list(target_ids)

    campaign = Campaign(
        name=payload.name,
        description=payload.description,
        vector=payload.vector,
        template_id=payload.template_id,
        group_ids=payload.group_ids,
        target_user_ids=target_list,
        target_count=len(target_list),
        scheduled_at=payload.scheduled_at,
        send_immediately=payload.send_immediately,
        status="active" if payload.send_immediately else ("scheduled" if payload.scheduled_at else "draft"),
    )
    db.add(campaign)
    await db.commit()
    await db.refresh(campaign)

    # Enqueue email dispatch as a background task if send immediately
    if payload.send_immediately:
        background_tasks.add_task(dispatch_campaign_emails, campaign.id, db)

    return campaign


@router.patch("/{campaign_id}", response_model=CampaignOut)
async def update_campaign(campaign_id: str, payload: CampaignUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Campaign).where(Campaign.id == campaign_id))
    campaign = result.scalar_one_or_none()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    for field, value in payload.model_dump(exclude_none=True).items():
        setattr(campaign, field, value)
    await db.commit()
    await db.refresh(campaign)
    return campaign


@router.delete("/{campaign_id}")
async def delete_campaign(campaign_id: str, db: AsyncSession = Depends(get_db)):
    await db.execute(delete(Campaign).where(Campaign.id == campaign_id))
    await db.commit()
    return {"ok": True}


@router.post("/{campaign_id}/send", response_model=CampaignOut)
async def send_campaign_now(campaign_id: str, background_tasks: BackgroundTasks, db: AsyncSession = Depends(get_db)):
    """Trigger immediate dispatch for an existing draft/scheduled campaign."""
    result = await db.execute(select(Campaign).where(Campaign.id == campaign_id))
    campaign = result.scalar_one_or_none()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    campaign.status = "active"
    campaign.send_immediately = True
    await db.commit()
    await db.refresh(campaign)
    background_tasks.add_task(dispatch_campaign_emails, campaign.id, db)
    return campaign
