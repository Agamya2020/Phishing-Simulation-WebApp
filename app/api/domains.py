import httpx

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.security import require_admin
from app.core.resend_domains import (
    create_resend_domain,
    get_resend_domain,
    verify_resend_domain,
    list_resend_domains,
)
from app.models.models import (
    SenderDomain,
    SenderIdentity,
)
from app.schemas.schemas import (
    SenderDomainCreate,
    SenderDomainOut,
)


router = APIRouter(
    prefix="/domains",
    tags=["domains"],
    dependencies=[Depends(require_admin)],
)


def normalize_domain(value: str) -> str:
    domain = value.strip().lower()

    domain = domain.removeprefix("https://")
    domain = domain.removeprefix("http://")
    domain = domain.rstrip("/")

    if "/" in domain:
        domain = domain.split("/", 1)[0]

    if not domain or "." not in domain:
        raise HTTPException(
            status_code=400,
            detail="Enter a valid domain name.",
        )

    return domain


def resend_error_detail(exc: httpx.HTTPStatusError) -> str:
    try:
        body = exc.response.json()

        if isinstance(body, dict):
            return (
                body.get("message")
                or body.get("error")
                or "Resend API request failed."
            )

    except Exception:
        pass

    return "Resend API request failed."


async def sync_sender_domain(
    db: AsyncSession,
    domain: SenderDomain,
):
    """
    Link existing sender identities to this domain and keep their
    verification state synchronized with the real domain status.
    """

    result = await db.execute(
        select(SenderIdentity).where(
            SenderIdentity.domain == domain.domain
        )
    )

    senders = result.scalars().all()

    domain_verified = (
        domain.status == "verified"
        and domain.is_active is True
    )

    for sender in senders:
        sender.domain_id = domain.id
        sender.is_verified = domain_verified

        if not domain_verified:
            sender.is_active = False


@router.get("", response_model=list[SenderDomainOut])
async def list_domains(
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(SenderDomain)
        .order_by(SenderDomain.created_at.desc())
    )

    return result.scalars().all()


@router.post("")
async def create_domain(
    payload: SenderDomainCreate,
    db: AsyncSession = Depends(get_db),
):
    domain_name = normalize_domain(payload.domain)

    existing = await db.execute(
        select(SenderDomain)
        .where(SenderDomain.domain == domain_name)
    )

    existing_domain = existing.scalar_one_or_none()

    if existing_domain:
        raise HTTPException(
            status_code=409,
            detail="Domain already exists.",
        )

    try:
        resend_data = await create_resend_domain(
            domain_name
        )

    except httpx.HTTPStatusError as exc:
        raise HTTPException(
            status_code=400,
            detail=resend_error_detail(exc),
        ) from exc

    except httpx.RequestError as exc:
        raise HTTPException(
            status_code=502,
            detail="Unable to contact Resend.",
        ) from exc

    resend_id = resend_data.get("id")

    if not resend_id:
        raise HTTPException(
            status_code=502,
            detail="Resend did not return a domain ID.",
        )

    resend_status = (
        resend_data.get("status")
        or "pending"
    )

    domain = SenderDomain(
        domain=domain_name,
        resend_domain_id=resend_id,
        status=resend_status,
        is_active=True,
    )

    db.add(domain)

    await db.commit()
    await db.refresh(domain)

    await sync_sender_domain(
        db,
        domain,
    )

    await db.commit()

    return {
        "domain": {
            "id": domain.id,
            "domain": domain.domain,
            "resend_domain_id": domain.resend_domain_id,
            "status": domain.status,
            "is_active": domain.is_active,
            "created_at": domain.created_at,
        },
        "resend": resend_data,
    }


@router.post("/import")
async def import_domain(
    payload: SenderDomainCreate,
    db: AsyncSession = Depends(get_db),
):
    domain_name = normalize_domain(payload.domain)

    existing = await db.execute(
        select(SenderDomain)
        .where(SenderDomain.domain == domain_name)
    )

    existing_domain = existing.scalar_one_or_none()

    try:
        resend_response = await list_resend_domains()

    except httpx.HTTPStatusError as exc:
        raise HTTPException(
            status_code=400,
            detail=resend_error_detail(exc),
        ) from exc

    except httpx.RequestError as exc:
        raise HTTPException(
            status_code=502,
            detail="Unable to contact Resend.",
        ) from exc

    resend_domains = resend_response.get("data", [])

    matched_domain = next(
        (
            item
            for item in resend_domains
            if str(item.get("name", "")).lower() == domain_name
        ),
        None,
    )

    if not matched_domain:
        raise HTTPException(
            status_code=404,
            detail=(
                "Domain was not found in the configured "
                "Resend account."
            ),
        )

    resend_id = matched_domain.get("id")

    if not resend_id:
        raise HTTPException(
            status_code=502,
            detail="Resend domain does not contain an ID.",
        )

    # Retrieve full details, including current DNS records.
    try:
        resend_data = await get_resend_domain(resend_id)

    except httpx.HTTPStatusError as exc:
        raise HTTPException(
            status_code=400,
            detail=resend_error_detail(exc),
        ) from exc

    except httpx.RequestError as exc:
        raise HTTPException(
            status_code=502,
            detail="Unable to contact Resend.",
        ) from exc

    status = (
        resend_data.get("status")
        or matched_domain.get("status")
        or "pending"
    )

    if existing_domain:
        existing_domain.resend_domain_id = resend_id
        existing_domain.status = status
        existing_domain.is_active = True

        await db.flush()

        await sync_sender_domain(
            db,
            existing_domain,
        )

        await db.commit()
        await db.refresh(existing_domain)

        return {
            "domain": {
                "id": existing_domain.id,
                "domain": existing_domain.domain,
                "resend_domain_id": existing_domain.resend_domain_id,
                "status": existing_domain.status,
                "is_active": existing_domain.is_active,
                "created_at": existing_domain.created_at,
            },
            "resend": resend_data,
            "repaired": True,
        }

    domain = SenderDomain(
        domain=domain_name,
        resend_domain_id=resend_id,
        status=status,
        is_active=True,
    )

    db.add(domain)

    await db.flush()

    await sync_sender_domain(
        db,
        domain,
    )

    await db.commit()
    await db.refresh(domain)

    return {
        "domain": {
            "id": domain.id,
            "domain": domain.domain,
            "resend_domain_id": domain.resend_domain_id,
            "status": domain.status,
            "is_active": domain.is_active,
            "created_at": domain.created_at,
        },
        "resend": resend_data,
        "repaired": False,
    }


@router.get("/{domain_id}")
async def get_domain(
    domain_id: int,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(SenderDomain)
        .where(SenderDomain.id == domain_id)
    )

    domain = result.scalar_one_or_none()

    if not domain:
        raise HTTPException(
            status_code=404,
            detail="Domain not found.",
        )

    if not domain.resend_domain_id:
        raise HTTPException(
            status_code=400,
            detail="Domain is not linked to Resend.",
        )

    try:
        resend_data = await get_resend_domain(
            domain.resend_domain_id
        )

    except httpx.HTTPStatusError as exc:
        raise HTTPException(
            status_code=400,
            detail=resend_error_detail(exc),
        ) from exc

    except httpx.RequestError as exc:
        raise HTTPException(
            status_code=502,
            detail="Unable to contact Resend.",
        ) from exc

    status = resend_data.get("status")

    if status:
        domain.status = status

        await db.flush()

        await sync_sender_domain(
            db,
            domain,
        )

        await db.commit()
        await db.refresh(domain)

    return {
        "domain": {
            "id": domain.id,
            "domain": domain.domain,
            "resend_domain_id": domain.resend_domain_id,
            "status": domain.status,
            "is_active": domain.is_active,
            "created_at": domain.created_at,
        },
        "resend": resend_data,
    }


@router.delete("/{domain_id}")
async def delete_domain(
    domain_id: int,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(SenderDomain).where(
            SenderDomain.id == domain_id
        )
    )

    domain = result.scalar_one_or_none()

    if not domain:
        raise HTTPException(
            status_code=404,
            detail="Domain not found.",
        )

    sender_result = await db.execute(
        select(SenderIdentity).where(
            SenderIdentity.domain_id == domain.id
        )
    )

    senders = sender_result.scalars().all()

    for sender in senders:
        sender.domain_id = None
        sender.is_verified = False
        sender.is_active = False

    await db.flush()
    await db.delete(domain)
    await db.commit()

    return {
        "ok": True,
        "message": (
            "Domain removed from PhishGuard. "
            "The domain was not deleted from Resend."
        ),
    }


@router.post("/{domain_id}/verify")
async def verify_domain(
    domain_id: int,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(SenderDomain)
        .where(SenderDomain.id == domain_id)
    )

    domain = result.scalar_one_or_none()

    if not domain:
        raise HTTPException(
            status_code=404,
            detail="Domain not found.",
        )

    if not domain.resend_domain_id:
        raise HTTPException(
            status_code=400,
            detail="Domain is not linked to Resend.",
        )

    try:
        await verify_resend_domain(
            domain.resend_domain_id
        )

        resend_data = await get_resend_domain(
            domain.resend_domain_id
        )

    except httpx.HTTPStatusError as exc:
        raise HTTPException(
            status_code=400,
            detail=resend_error_detail(exc),
        ) from exc

    except httpx.RequestError as exc:
        raise HTTPException(
            status_code=502,
            detail="Unable to contact Resend.",
        ) from exc

    domain.status = (
        resend_data.get("status")
        or "pending"
    )

    await db.flush()

    await sync_sender_domain(
        db,
        domain,
    )

    await db.commit()
    await db.refresh(domain)

    return {
        "domain": {
            "id": domain.id,
            "domain": domain.domain,
            "resend_domain_id": domain.resend_domain_id,
            "status": domain.status,
            "is_active": domain.is_active,
            "created_at": domain.created_at,
        },
        "resend": resend_data,
    }
