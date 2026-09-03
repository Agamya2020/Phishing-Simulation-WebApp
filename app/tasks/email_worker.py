"""Email dispatch background task."""

import html
import logging
from datetime import datetime, timezone

from sqlalchemy import select

from app.models.models import Campaign, User, Template, CampaignEvent
from app.core.mailer import send_email
from app.core.config import settings
from app.core.db import AsyncSessionLocal

logger = logging.getLogger(__name__)


def build_email_html(
    template: Template,
    user: User,
    campaign: Campaign,
    tracking_url: str
) -> str:
    """
    Compile the phishing simulation email.

    Important:
    - User/template content is HTML escaped.
    - A campaign-specific tracking link is inserted.
    - A 1x1 tracking pixel records opens.
    """

    body_text = template.body or ""

    # Replace placeholders before escaping
    body_text = body_text.replace("[Employee Name]", user.name)
    body_text = body_text.replace("[Name]", user.name)
    body_text = body_text.replace("[name]", user.name)

    # Escape any HTML coming from template/user data
    safe_body = html.escape(body_text)
    safe_campaign_name = html.escape(campaign.name)
    safe_user_name = html.escape(user.name)

    click_url = (
        f"{tracking_url.rstrip('/')}"
        f"/track/click/{campaign.id}/{user.id}"
    )

    open_pixel_url = (
        f"{tracking_url.rstrip('/')}"
        f"/track/open/{campaign.id}/{user.id}"
    )

    # Convert lines into paragraphs.
    # Lines beginning with → become the tracked CTA button.
    rendered_lines = []

    for line in safe_body.splitlines():
        line = line.strip()

        if not line:
            continue

        if line.startswith("→"):
            button_text = line.lstrip("→").strip() or "Continue"

            rendered_lines.append(
                f"""
                <p style="margin:24px 0;">
                    <a
                        href="{click_url}"
                        style="
                            display:inline-block;
                            padding:12px 20px;
                            background:#1a73e8;
                            color:#ffffff;
                            text-decoration:none;
                            border-radius:5px;
                            font-weight:bold;
                        "
                    >
                        {button_text}
                    </a>
                </p>
                """
            )

        else:
            rendered_lines.append(
                f'<p style="margin-bottom:16px;">{line}</p>'
            )

    rendered_body = "\n".join(rendered_lines)

    return f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>{html.escape(template.subject)}</title>
</head>

<body
    style="
        font-family:Arial,sans-serif;
        font-size:14px;
        color:#333;
        max-width:600px;
        margin:40px auto;
        padding:20px;
    "
>

<div
    style="
        border:1px solid #e0e0e0;
        border-radius:8px;
        padding:32px;
    "
>

    <p
        style="
            font-size:11px;
            color:#999;
            margin-bottom:24px;
        "
    >
        ⚠️ <strong>PHISHGUARD SIMULATION</strong>
        — Security awareness training email.
    </p>

    {rendered_body}

    <p
        style="
            font-size:12px;
            color:#aaa;
            margin-top:32px;
        "
    >
        Campaign: {safe_campaign_name}
    </p>

</div>

<img
    src="{open_pixel_url}"
    width="1"
    height="1"
    alt=""
    style="display:none;"
/>

</body>
</html>
"""


async def dispatch_campaign_emails(campaign_id: str):
    """
    Background task used for dispatching campaign emails.

    A new database session is created inside the worker instead of
    reusing the FastAPI request session.
    """

    async with AsyncSessionLocal() as db:

        try:

            # --------------------------------------------------
            # Load campaign
            # --------------------------------------------------

            result = await db.execute(
                select(Campaign)
                .where(Campaign.id == campaign_id)
            )

            campaign = result.scalar_one_or_none()

            if not campaign:
                logger.error(
                    "Campaign %s not found",
                    campaign_id
                )
                return

            campaign.status = "active"
            await db.commit()

            # --------------------------------------------------
            # Load template
            # --------------------------------------------------

            if not campaign.template_id:
                logger.error(
                    "Campaign %s has no template",
                    campaign_id
                )
                campaign.status = "failed"
                await db.commit()
                return

            result = await db.execute(
                select(Template)
                .where(
                    Template.id == campaign.template_id
                )
            )

            template = result.scalar_one_or_none()

            if not template:
                logger.error(
                    "Template not found for campaign %s",
                    campaign_id
                )
                campaign.status = "failed"
                await db.commit()
                return

            # --------------------------------------------------
            # Validate targets
            # --------------------------------------------------

            if not campaign.target_user_ids:

                logger.warning(
                    "Campaign %s has no target users",
                    campaign_id
                )
                campaign.status = "failed"
                await db.commit()
                return

            # --------------------------------------------------
            # Load users
            # --------------------------------------------------

            result = await db.execute(
                select(User)
                .where(
                    User.id.in_(
                        campaign.target_user_ids
                    )
                )
            )

            users = result.scalars().all()

            logger.info(
                "Dispatching campaign '%s' to %s users",
                campaign.name,
                len(users)
            )

            # --------------------------------------------------
            # Tracking base URL
            # --------------------------------------------------

            tracking_url = (
                settings.TRACKING_BASE_URL
                .rstrip("/")
            )

            successful = 0
            failed = 0

            # --------------------------------------------------
            # Send emails
            # --------------------------------------------------

            for user in users:

                try:

                    email_html = build_email_html(
                        template=template,
                        user=user,
                        campaign=campaign,
                        tracking_url=tracking_url,
                    )

                    await send_email(
                        to_email=user.email,
                        to_name=user.name,
                        subject=template.subject,
                        html_body=email_html,
                        sender=template.sender,
                    )

                    # Avoid duplicate "sent" events
                    existing = await db.execute(
                        select(CampaignEvent)
                        .where(
                            CampaignEvent.campaign_id
                            == campaign.id,

                            CampaignEvent.user_id
                            == user.id,

                            CampaignEvent.event_type
                            == "sent",
                        )
                    )

                    existing_event = (
                        existing.scalar_one_or_none()
                    )

                    if not existing_event:

                        event = CampaignEvent(
                            campaign_id=campaign.id,
                            user_id=user.id,
                            user_email=user.email,
                            event_type="sent",
                        )

                        db.add(event)

                    successful += 1

                    logger.info(
                        "Sent campaign email to %s",
                        user.email
                    )

                except Exception as exc:

                    failed += 1

                    logger.exception(
                        "Failed sending campaign %s to %s: %s",
                        campaign.id,
                        user.email,
                        exc
                    )

            # --------------------------------------------------
            # Update campaign
            # --------------------------------------------------

            # Keep target_count as number of selected targets.
            campaign.target_count = len(users)

            if successful:
                template.uses = (
                    template.uses or 0
                ) + 1
                campaign.last_sent_at = datetime.now(timezone.utc)

            campaign.status = (
                "completed"
                if successful > 0
                else "failed"
            )

            await db.commit()

            logger.info(
                "Campaign '%s' dispatched: %s sent, %s failed",
                campaign.name,
                successful,
                failed,
            )

        except Exception:

            await db.rollback()

            logger.exception(
                "Campaign dispatch failed for %s",
                campaign_id
            )

            raise
