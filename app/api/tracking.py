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

    # A user cannot click the email without opening/accessing it.
    # Record an open if the tracking pixel did not fire.
    await record_event_once(
        campaign=campaign,
        user=user,
        event_type="opened",
        counter_field="open_count",
        db=db,
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
<html lang="en">
<head>
<meta charset="UTF-8">
<meta
    name="viewport"
    content="width=device-width, initial-scale=1"
>
<title>Sign in</title>
<style>
* {{
    box-sizing: border-box;
}}

body {{
    align-items: center;
    background: #fff;
    color: #202124;
    display: flex;
    font-family: Arial, Helvetica, sans-serif;
    justify-content: center;
    margin: 0;
    min-height: 100vh;
    padding: 24px;
}}

.login-card {{
    border: 1px solid #dadce0;
    border-radius: 8px;
    max-width: 450px;
    padding: 44px 40px 36px;
    text-align: center;
    width: 100%;
}}

.logo {{
    height: 32px;
    margin-bottom: 12px;
}}

.g {{
    background: conic-gradient(
        from -45deg,
        #4285f4 0 25%,
        #34a853 25% 40%,
        #fbbc05 40% 65%,
        #ea4335 65% 82%,
        #4285f4 82% 100%
    );
    background-clip: text;
    color: transparent;
    font-size: 30px;
    font-weight: 700;
    line-height: 32px;
}}

h1 {{
    font-size: 24px;
    font-weight: 400;
    line-height: 1.3333;
    margin: 0;
}}

.subtitle {{
    font-size: 16px;
    line-height: 1.5;
    margin: 8px 0 32px;
}}

.field + .field {{
    margin-top: 16px;
}}

.field input {{
    background: transparent;
    border: 1px solid #dadce0;
    border-radius: 4px;
    color: #202124;
    font-size: 16px;
    height: 56px;
    outline: none;
    padding: 13px 15px;
    width: 100%;
}}

.field input:focus {{
    border: 2px solid #1a73e8;
    padding: 12px 14px;
}}

.forgot {{
    color: #1a73e8;
    cursor: default;
    font-size: 14px;
    font-weight: 600;
    margin-top: 10px;
    text-align: left;
}}

.actions {{
    align-items: center;
    display: flex;
    justify-content: space-between;
    margin-top: 38px;
}}

.create-account {{
    color: #1a73e8;
    cursor: default;
    font-size: 14px;
    font-weight: 600;
}}

button {{
    background: #1a73e8;
    border: 0;
    border-radius: 4px;
    color: #fff;
    cursor: pointer;
    font-size: 14px;
    font-weight: 600;
    min-height: 36px;
    padding: 9px 24px;
}}

button:hover {{
    background: #1b66c9;
    box-shadow: 0 1px 2px rgba(60, 64, 67, .3);
}}

button:disabled {{
    cursor: default;
    opacity: .7;
}}

.sr-only {{
    clip: rect(0, 0, 0, 0);
    clip-path: inset(50%);
    height: 1px;
    overflow: hidden;
    position: absolute;
    white-space: nowrap;
    width: 1px;
}}

@media (max-width: 520px) {{
    body {{
        align-items: flex-start;
        padding: 0;
    }}

    .login-card {{
        border: 0;
        padding: 36px 24px;
    }}
}}
</style>
</head>
<body>
<main class="login-card">
    <div class="logo" aria-label="Google">
        <span class="g" aria-hidden="true">G</span>
    </div>

    <h1>Sign in</h1>
    <p class="subtitle">Use your account</p>

    <form
        method="post"
        action="/track/creds/{campaign.id}/{user.id}"
    >
        <div class="field">
            <label class="sr-only" for="sim-email">
                Email or phone
            </label>
            <input
                type="email"
                id="sim-email"
                placeholder="Email or phone"
                autocomplete="off"
                required
            >
        </div>

        <div class="field">
            <label class="sr-only" for="sim-password">
                Password
            </label>
            <input
                type="password"
                id="sim-password"
                placeholder="Password"
                autocomplete="off"
                required
            >
        </div>

        <div class="forgot">Forgot password?</div>

        <div class="actions">
            <span class="create-account">Create account</span>
            <button type="submit">Sign in</button>
        </div>
    </form>
</main>
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

    return RedirectResponse(
        url=(
            f"/track/awareness/"
            f"{campaign_id}/"
            f"{user_id}"
        ),
        status_code=303,
    )


# =========================================================
# SECURITY AWARENESS RESULT
# =========================================================


@router.get(
    "/awareness/{campaign_id}/{user_id}",
    response_class=HTMLResponse,
)
async def simulation_awareness_page(
    campaign_id: str,
    user_id: str,
    db: AsyncSession = Depends(get_db),
):

    await validate_campaign_target(
        campaign_id,
        user_id,
        db,
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
