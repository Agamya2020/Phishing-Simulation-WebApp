"""Email dispatch background task."""
import json
import logging
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.models import Campaign, User, Template, CampaignEvent
from app.core.mailer import send_email
from app.core.config import settings

logger = logging.getLogger(__name__)


def build_email_html(template: Template, user: User, campaign: Campaign, tracking_url: str) -> str:
    """Compile the template body, inject tracking pixel and rewrite phishing link."""
    body_text = template.body
    body_text = body_text.replace("[Employee Name]", user.name)
    body_text = body_text.replace("[Name]", user.name)
    body_text = body_text.replace("[name]", user.name)

    # Convert newlines to HTML paragraphs
    paragraphs = [f"<p>{line}</p>" for line in body_text.split("\n") if line.strip()]
    
    # Rewrite the phishing link to our tracking endpoint
    click_url = f"{tracking_url}/track/click/{campaign.id}/{user.id}"
    para_html = "\n".join(paragraphs)
    para_html = para_html.replace("→ ", f'<a href="{click_url}" style="color:#1a73e8;font-weight:bold;">→ ')
    # Close any open <a> tags after arrow links  
    para_html = para_html.replace("→ ", f'→ </a>')
    
    # Tracking pixel (open tracking)
    open_pixel = f'<img src="{tracking_url}/track/open/{campaign.id}/{user.id}" width="1" height="1" alt="" />'

    return f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8"></head>
<body style="font-family:Arial,sans-serif;font-size:14px;color:#333;max-width:600px;margin:40px auto;padding:20px;">
  <div style="border:1px solid #e0e0e0;border-radius:8px;padding:32px;">
    <p style="font-size:11px;color:#999;margin-bottom:24px;">
      ⚠️ <strong>PHISHGUARD SIMULATION</strong> — This is a security awareness training email. 
      Your actions are being tracked for training purposes.
    </p>
    {''.join(f'<p style="margin-bottom:16px;">{p}</p>' for p in body_text.split("\\n") if p.strip())}
    <br>
    <p style="font-size:12px;color:#aaa;margin-top:32px;">Campaign: {campaign.name} | Sent by PhishGuard</p>
  </div>
  {open_pixel}
</body>
</html>"""


async def dispatch_campaign_emails(campaign_id: str, db: AsyncSession):
    """Background task: fetch campaign + targets + template, send emails, record events."""
    try:
        # Load campaign
        result = await db.execute(select(Campaign).where(Campaign.id == campaign_id))
        campaign = result.scalar_one_or_none()
        if not campaign:
            logger.error(f"Campaign {campaign_id} not found")
            return

        # Load template
        template = None
        if campaign.template_id:
            result = await db.execute(select(Template).where(Template.id == campaign.template_id))
            template = result.scalar_one_or_none()

        if not template:
            logger.error(f"Template not found for campaign {campaign_id}")
            return

        # Load target users
        if not campaign.target_user_ids:
            logger.warning(f"Campaign {campaign_id} has no target users")
            return

        result = await db.execute(select(User).where(User.id.in_(campaign.target_user_ids)))
        users = result.scalars().all()

        logger.info(f"Dispatching campaign '{campaign.name}' to {len(users)} users")

        tracking_url = settings.TRACKING_BASE_URL
        sent_count = 0

        for user in users:
            try:
                html = build_email_html(template, user, campaign, tracking_url)
                await send_email(
                    to_email=user.email,
                    to_name=user.name,
                    subject=template.subject,
                    html_body=html,
                )

                # Record 'sent' event
                event = CampaignEvent(
                    campaign_id=campaign_id,
                    user_id=user.id,
                    user_email=user.email,
                    event_type="sent",
                )
                db.add(event)
                sent_count += 1
                logger.info(f"  ✓ Sent to {user.email}")

            except Exception as e:
                logger.error(f"  ✗ Failed to send to {user.email}: {e}")

        # Update campaign status → active, update template use count
        campaign.status = "active"
        campaign.target_count = sent_count
        template.uses = (template.uses or 0) + 1

        await db.commit()
        logger.info(f"Campaign '{campaign.name}' dispatched: {sent_count}/{len(users)} emails sent")

    except Exception as e:
        logger.error(f"dispatch_campaign_emails error: {e}")
        await db.rollback()
        raise
