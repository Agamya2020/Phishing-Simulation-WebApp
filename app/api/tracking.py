"""Tracking endpoints for phishing simulation campaigns."""

import logging

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import (
    Response,
    RedirectResponse,
    HTMLResponse,
)

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.models.models import (
    Campaign,
    CampaignEvent,
    User,
)

router = APIRouter(
    prefix="/track",
    tags=["tracking"]
)

logger = logging.getLogger(__name__)


# 1x1 transparent GIF

PIXEL_GIF = (
    b"GIF89a"
    b"\x01\x00\x01\x00"
    b"\x80\xff\x00"
    b"\xff\xff\xff"
    b"\x00\x00\x00"
    b"!\xf9\x04\x00"
    b"\x00\x00\x00\x00"
    b",\x00\x00\x00\x00"
    b"\x01\x00\x01\x00"
    b"\x00"
    b"\x02\x02D\x01\x00;"
)


async def validate_campaign_target(
    campaign_id: str,
    user_id: str,
    db: AsyncSession,
):
    """
    Confirm that:
    - campaign exists
    - user exists
    - user belongs to the campaign
    """

    campaign_result = await db.execute(
        select(Campaign)
        .where(Campaign.id == campaign_id)
    )

    campaign = (
        campaign_result
        .scalar_one_or_none()
    )

    if not campaign:

        raise HTTPException(
            status_code=404,
            detail="Campaign not found"
        )

    user_result = await db.execute(
        select(User)
        .where(User.id == user_id)
    )

    user = (
        user_result
        .scalar_one_or_none()
    )

    if not user:

        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    if user.id not in (
        campaign.target_user_ids or []
    ):

        raise HTTPException(
            status_code=404,
            detail="Invalid campaign target"
        )

    return campaign, user


async def record_event_once(
    campaign: Campaign,
    user: User,
    event_type: str,
    counter_field: str | None,
    db: AsyncSession,
):
    """
    Record an event only once for a user/campaign.

    This prevents repeated refreshes from artificially
    increasing campaign statistics.
    """

    result = await db.execute(

        select(CampaignEvent)

        .where(

            CampaignEvent.campaign_id
            == campaign.id,

            CampaignEvent.user_id
            == user.id,

            CampaignEvent.event_type
            == event_type,

        )
    )

    existing = result.scalar_one_or_none()

    if existing:

        return False

    event = CampaignEvent(

        campaign_id=campaign.id,

        user_id=user.id,

        user_email=user.email,

        event_type=event_type,

    )

    db.add(event)

    if counter_field:

        current_value = (
            getattr(
                campaign,
                counter_field
            )
            or 0
        )

        setattr(
            campaign,
            counter_field,
            current_value + 1
        )

    await db.commit()

    return True


# =========================================================
# OPEN TRACKING
# =========================================================


@router.get(
    "/open/{campaign_id}/{user_id}"
)
async def track_open(
    campaign_id: str,
    user_id: str,
    db: AsyncSession = Depends(get_db),
):

    try:

        campaign, user = (
            await validate_campaign_target(
                campaign_id,
                user_id,
                db
            )
        )

        recorded = await record_event_once(

            campaign=campaign,

            user=user,

            event_type="opened",

            counter_field="open_count",

            db=db,

        )

        if recorded:

            logger.info(
                "[OPEN] campaign=%s user=%s",
                campaign_id,
                user_id
            )

    except HTTPException:

        # Do not expose tracking errors inside email clients.
        pass

    except Exception as exc:

        await db.rollback()

        logger.exception(
            "track_open error: %s",
            exc
        )

    return Response(

        content=PIXEL_GIF,

        media_type="image/gif",

        headers={

            "Cache-Control":
                "no-store, no-cache, must-revalidate, max-age=0",

            "Pragma":
                "no-cache",

            "Expires":
                "0",

        }
    )


# =========================================================
# CLICK TRACKING
# =========================================================


@router.get(
    "/click/{campaign_id}/{user_id}"
)
async def track_click(
    campaign_id: str,
    user_id: str,
    db: AsyncSession = Depends(get_db),
):

    campaign, user = (
        await validate_campaign_target(
            campaign_id,
            user_id,
            db
        )
    )

    await record_event_once(

        campaign=campaign,

        user=user,

        event_type="clicked",

        counter_field="click_count",

        db=db,

    )

    logger.info(
        "[CLICK] campaign=%s user=%s",
        campaign_id,
        user_id
    )

    return RedirectResponse(

        url=(
            f"/track/landing/"
            f"{campaign_id}/"
            f"{user_id}"
        ),

        status_code=302

    )


# =========================================================
# SIMULATED LANDING PAGE
# =========================================================


@router.get(
    "/landing/{campaign_id}/{user_id}",
    response_class=HTMLResponse
)
async def phishing_landing_page(
    campaign_id: str,
    user_id: str,
    db: AsyncSession = Depends(get_db),
):

    campaign, user = (
        await validate_campaign_target(
            campaign_id,
            user_id,
            db
        )
    )

    page = f"""
<!DOCTYPE html>

<html>

<head>

<meta charset="UTF-8">

<meta
    name="viewport"
    content="width=device-width, initial-scale=1"
>

<title>Corporate Sign In</title>

<style>

body {{
    margin: 0;
    background: #f5f6f8;
    font-family: Arial, sans-serif;
}}

.container {{
    max-width: 420px;
    margin: 80px auto;
}}

.card {{
    background: white;
    border-radius: 8px;
    padding: 36px;
    box-shadow:
        0 3px 18px
        rgba(0,0,0,.10);
}}

h2 {{
    margin-top: 0;
}}

label {{
    display: block;
    margin-top: 18px;
    margin-bottom: 6px;
}}

input {{
    width: 100%;
    box-sizing: border-box;
    padding: 11px;
    border: 1px solid #bbb;
    border-radius: 5px;
}}

button {{
    width: 100%;
    padding: 12px;
    border: 0;
    border-radius: 5px;
    background: #1769e0;
    color: white;
    font-weight: bold;
    margin-top: 24px;
    cursor: pointer;
}}

.help {{
    color: #777;
    font-size: 12px;
    margin-top: 20px;
}}

</style>

</head>

<body>

<div class="container">

<div class="card">

<h2>Corporate Account</h2>

<p>
Hello {user.name},
please verify your account to continue.
</p>

<form
    method="post"
    action="/track/creds/{campaign.id}/{user.id}"
>

<label>Email address</label>

<!--
IMPORTANT:

There is deliberately NO name="" attribute.

Therefore the value entered here is NOT submitted
to the backend.
-->

<input
    type="email"
    autocomplete="off"
    placeholder="name@company.com"
    required
>

<label>Password</label>

<!--
Again there is deliberately no name="" attribute.

The password therefore never leaves the browser.
-->

<input
    type="password"
    autocomplete="off"
    placeholder="Password"
    required
>

<button type="submit">
Sign in
</button>

</form>

<p class="help">
Corporate identity verification service
</p>

</div>

</div>

</body>

</html>
"""

    return HTMLResponse(
        content=page
    )


# =========================================================
# FORM SUBMISSION
# =========================================================


@router.post(
    "/creds/{campaign_id}/{user_id}"
)
async def track_creds(
    campaign_id: str,
    user_id: str,
    db: AsyncSession = Depends(get_db),
):

    campaign, user = (
        await validate_campaign_target(
            campaign_id,
            user_id,
            db
        )
    )

    await record_event_once(

        campaign=campaign,

        user=user,

        event_type="creds_entered",

        counter_field="creds_count",

        db=db,

    )

    logger.info(
        "[SIMULATION SUBMISSION] "
        "campaign=%s user=%s",
        campaign_id,
        user_id
    )

    return HTMLResponse(
        content="""
<!DOCTYPE html>

<html>

<head>

<meta charset="UTF-8">

<meta
    name="viewport"
    content="width=device-width, initial-scale=1"
>

<title>Phishing Simulation</title>

<style>

body {
    background: #f5f7fa;
    font-family: Arial, sans-serif;
    margin: 0;
}

.wrapper {
    max-width: 700px;
    margin: 70px auto;
    padding: 25px;
}

.card {
    background: white;
    border-radius: 10px;
    padding: 40px;
    box-shadow:
        0 3px 18px
        rgba(0,0,0,.10);
}

h1 {
    margin-top: 0;
}

.tip {
    background: #f2f5f9;
    padding: 16px;
    margin-top: 15px;
    border-radius: 6px;
}

</style>

</head>

<body>

<div class="wrapper">

<div class="card">

<h1>
This was a phishing simulation
</h1>

<p>
You submitted the simulated sign-in form.
No password or login information was collected.
</p>

<h3>
What should you check next time?
</h3>

<div class="tip">
<strong>Sender:</strong>
Verify the sender address before trusting the message.
</div>

<div class="tip">
<strong>Urgency:</strong>
Be cautious when an email pressures you to act immediately.
</div>

<div class="tip">
<strong>Links:</strong>
Inspect links before opening them.
</div>

<div class="tip">
<strong>Credentials:</strong>
Do not enter corporate credentials after following
an unexpected email link.
</div>

<div class="tip">
<strong>Report suspicious messages:</strong>
Use your organisation's phishing-reporting procedure
when something looks suspicious.
</div>

</div>

</div>

</body>

</html>
"""
    )


# =========================================================
# REPORT PHISHING
# =========================================================


@router.post(
    "/report/{campaign_id}/{user_id}"
)
async def track_report(
    campaign_id: str,
    user_id: str,
    db: AsyncSession = Depends(get_db),
):

    campaign, user = (
        await validate_campaign_target(
            campaign_id,
            user_id,
            db
        )
    )

    await record_event_once(

        campaign=campaign,

        user=user,

        event_type="reported",

        counter_field="report_count",

        db=db,

    )

    logger.info(
        "[REPORT] campaign=%s user=%s",
        campaign_id,
        user_id
    )

    return {
        "ok": True,
        "message":
            "Phishing simulation reported successfully"
    }
