from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.security import require_admin
from app.models.models import (
    SenderIdentity,
    SenderDomain,
)
from app.schemas.schemas import (
    SenderIdentityCreate,
    SenderIdentityOut,
    SenderIdentityUpdate,
)

router = APIRouter(
    prefix="/senders",
    tags=["senders"],
    dependencies=[Depends(require_admin)],
)


@router.get("", response_model=list[SenderIdentityOut])
async def list_senders(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(SenderIdentity).order_by(SenderIdentity.created_at.desc())
    )
    return result.scalars().all()


@router.post("", response_model=SenderIdentityOut)
async def create_sender(
    payload: SenderIdentityCreate,
    db: AsyncSession = Depends(get_db),
):
    email = str(payload.email).lower().strip()
    domain = email.split("@", 1)[1]

    existing = await db.execute(
        select(SenderIdentity).where(
            SenderIdentity.email == email
        )
    )

    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=409,
            detail="Sender email already exists",
        )

    domain_result = await db.execute(
        select(SenderDomain).where(
            SenderDomain.domain == domain,
            SenderDomain.status == "verified",
            SenderDomain.is_active.is_(True),
        )
    )

    verified_domain = domain_result.scalar_one_or_none()

    if not verified_domain:
        raise HTTPException(
            status_code=400,
            detail=(
                "The sender domain is not verified. "
                "Add and verify the domain first."
            ),
        )

    sender = SenderIdentity(
        name=payload.name.strip(),
        email=email,
        domain=domain,
        domain_id=verified_domain.id,
        is_verified=True,
        is_active=True,
    )

    db.add(sender)
    await db.commit()
    await db.refresh(sender)

    return sender


@router.patch("/{sender_id}", response_model=SenderIdentityOut)
async def update_sender(
    sender_id: int,
    payload: SenderIdentityUpdate,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(SenderIdentity).where(SenderIdentity.id == sender_id)
    )

    sender = result.scalar_one_or_none()

    if not sender:
        raise HTTPException(
            status_code=404,
            detail="Sender identity not found",
        )

    values = payload.model_dump(exclude_none=True)

    for field, value in values.items():
        setattr(sender, field, value)

    await db.commit()
    await db.refresh(sender)

    return sender


@router.delete("/{sender_id}")
async def delete_sender(
    sender_id: int,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(SenderIdentity).where(SenderIdentity.id == sender_id)
    )

    sender = result.scalar_one_or_none()

    if not sender:
        raise HTTPException(
            status_code=404,
            detail="Sender identity not found",
        )

    await db.execute(
        delete(SenderIdentity).where(SenderIdentity.id == sender_id)
    )

    await db.commit()

    return {"ok": True}
