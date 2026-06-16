"""Seed the database with mock data from the original Zustand store."""
import asyncio
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.core.db import AsyncSessionLocal
from app.models.models import Department, User, Group, Template, Campaign


async def seed(db: AsyncSession):
    # Only seed if DB is empty
    count = await db.execute(select(func.count()).select_from(Department))
    if count.scalar() > 0:
        return

    print("[SEED] Seeding database with mock data...")

    # Departments
    departments = [
        Department(id="d1", name="Finance", code="FIN", head="Sarah Mitchell", sub_depts=3),
        Department(id="d2", name="Engineering", code="ENG", head="Tom Harrison", sub_depts=5),
        Department(id="d3", name="Marketing", code="MKT", head="Jessica Park", sub_depts=2),
        Department(id="d4", name="Human Resources", code="HR", head="Marcus Johnson", sub_depts=2),
        Department(id="d5", name="Legal", code="LGL", head="Ana Rodriguez", sub_depts=1),
        Department(id="d6", name="Operations", code="OPS", head="David Chen", sub_depts=4),
        Department(id="d7", name="IT Security", code="ITS", head="Alice Johnson", sub_depts=3),
        Department(id="d8", name="Executive", code="EXEC", head="CEO Office", sub_depts=0),
    ]
    db.add_all(departments)

    # Users
    users = [
        User(id="u1", name="Alice Johnson", email="alice@corp.io", role="super_admin", department_id="d7", status="active", risk_score=22),
        User(id="u2", name="Bob Martinez", email="bob@corp.io", role="admin", department_id="d7", status="active", risk_score=35),
        User(id="u3", name="Carol Williams", email="carol@corp.io", role="employee", department_id="d1", status="active", risk_score=78),
        User(id="u4", name="David Chen", email="david@corp.io", role="employee", department_id="d3", status="active", risk_score=61),
        User(id="u5", name="Eva Rodriguez", email="eva@corp.io", role="employee", department_id="d4", status="active", risk_score=45),
        User(id="u6", name="Frank Thompson", email="frank@corp.io", role="employee", department_id="d2", status="active", risk_score=18),
        User(id="u7", name="Grace Kim", email="grace@corp.io", role="admin", department_id="d6", status="inactive", risk_score=29),
        User(id="u8", name="Henry Walsh", email="henry@corp.io", role="employee", department_id="d8", status="active", risk_score=89),
        User(id="u9", name="Iris Patel", email="iris@corp.io", role="employee", department_id="d1", status="active", risk_score=72),
        User(id="u10", name="James Kim", email="james@corp.io", role="employee", department_id="d2", status="active", risk_score=25),
        User(id="u11", name="Karen Lee", email="karen@corp.io", role="employee", department_id="d5", status="active", risk_score=40),
        User(id="u12", name="Liam Nguyen", email="liam@corp.io", role="employee", department_id="d6", status="active", risk_score=68),
    ]
    db.add_all(users)

    # Groups
    groups = [
        Group(id="g1", name="Finance Department", department_id="d1", member_ids=["u3", "u9"]),
        Group(id="g2", name="All Engineering", department_id="d2", member_ids=["u6", "u10"]),
        Group(id="g3", name="Senior Leadership", department_id="d8", member_ids=["u8", "u1"]),
        Group(id="g4", name="Remote Workers", department_id=None, member_ids=["u3", "u4", "u5", "u6", "u9", "u10", "u11", "u12"]),
        Group(id="g5", name="New Hires Q2 2026", department_id=None, member_ids=["u10", "u11", "u12"]),
    ]
    db.add_all(groups)

    # Templates
    templates = [
        Template(id="t1", name="IT Password Reset", category="Credential Harvest", vector="Email",
                 subject="⚠️ [URGENT] Your Password Expires in 24 Hours",
                 sender="IT Support <it-support@corp-helpdesk.net>",
                 body="Dear [Employee Name],\n\nOur security system has detected that your corporate password will expire in 24 hours. To avoid being locked out of company systems, you must reset your password immediately.\n\nPlease click the link below to verify your identity and update your credentials:\n\n→ Reset Password Now\n\nIf you do not reset your password before the deadline, your account will be suspended.\n\nIT Security Operations",
                 uses=14, score=82),
        Template(id="t2", name="FedEx Package Delivery", category="Link Click", vector="Email",
                 subject="FedEx: Your Package Could Not Be Delivered",
                 sender="FedEx Delivery <delivery@fedex-notifications.co>",
                 body="Hello,\n\nWe attempted to deliver your package (Tracking #: 7489-2847-9182) but were unable to complete the delivery.\n\nTo schedule redelivery or pick up your package, please verify your delivery address:\n\n→ Verify Address & Schedule Delivery\n\nThis link expires in 48 hours.\n\nFedEx Customer Service",
                 uses=22, score=65),
        Template(id="t3", name="CEO Wire Transfer", category="BEC", vector="Email",
                 subject="Confidential — Urgent Wire Transfer Required",
                 sender="CEO Office <ceo-office@company-executive.io>",
                 body="Hi [Name],\n\nI need you to process a confidential wire transfer immediately. I am in a board meeting and cannot take calls right now, so please handle this discreetly.\n\nTransfer Amount: $48,500\nRecipient: Global Consulting Partners\nAccount: 8472-9182-0034\n\nThis must be completed before 5PM today. Please confirm via email when done.\n\nDo not discuss this with anyone until the transfer is complete.\n\nThank you,\nJohn Smith, CEO",
                 uses=7, score=91),
        Template(id="t4", name="VPN Login Portal", category="Fake Login", vector="Browser",
                 subject="VPN Access Required: Click to Authenticate",
                 sender="IT Infrastructure <infra@secure-vpn-portal.net>",
                 body="Dear Team,\n\nOur VPN infrastructure has been upgraded. All employees must re-authenticate their credentials on the new portal to maintain remote access.\n\nPlease log in using your corporate credentials:\n\n→ Access VPN Portal\n\nYour current VPN access will be terminated at midnight if you do not complete this step.\n\nIT Infrastructure Team",
                 uses=11, score=88),
        Template(id="t5", name="HR Benefits Enrollment", category="Urgency", vector="Email",
                 subject="Open Enrollment Closes Tonight at Midnight",
                 sender="HR Benefits <benefits@hr-portal-update.com>",
                 body="Dear [Employee Name],\n\nThis is your final reminder: the 2026 benefits enrollment window closes TONIGHT at midnight.\n\nOur records show you have not yet completed your benefits selections. Failure to enroll will result in automatic enrollment in the base plan only.\n\nTo review your options and make changes:\n\n→ Access Benefits Portal Now\n\nHuman Resources\nBenefits Administration",
                 uses=33, score=58),
        Template(id="t6", name="Google Account Alert", category="Credential Harvest", vector="Email",
                 subject="Security Alert: New Sign-in to your Google Account",
                 sender="Google Security <security@google-accounts-verify.com>",
                 body="Hi [Name],\n\nA new sign-in to your Google Account was detected from a new device.\n\nDevice: Windows PC\nLocation: Lagos, Nigeria\nTime: [TIMESTAMP]\n\nIf this wasn't you, your account may be compromised. Secure it immediately:\n\n→ Secure My Account\n\nIf you recognize this activity, no action is needed.\n\nThe Google Team",
                 uses=18, score=71),
        Template(id="t7", name="Slack DM Impersonation", category="Social Eng.", vector="Browser",
                 subject="You have a pending message from @CEO",
                 sender="Slack Notifications <notifications@slack-direct.com>",
                 body="You have a new direct message from John Smith (CEO):\n\n\"Hey, can you hop on this quick link? I need your input on a sensitive matter before the board meeting. Time-sensitive.\"\n\n→ Open Slack Message\n\nSlack, Inc.",
                 uses=9, score=63),
        Template(id="t8", name="Mobile OTP Phish", category="MFA Bypass", vector="Mobile",
                 subject="SMS: Your authentication code has been requested",
                 sender="Corp Security <security@corp-mfa-verify.net>",
                 body="CORP-SECURITY: An authentication request was made for your account from a new device. If this was you, enter the code below to verify. If not, click the link to block access immediately:\n\nVerification Code: [CODE]\n\n→ Verify or Block Access",
                 uses=5, score=41),
    ]
    db.add_all(templates)

    # Campaigns
    campaigns = [
        Campaign(id="c1", name="Q2 Finance Phishing Drill", status="active", vector="Email", template_id="t1",
                 group_ids=["g1"], target_user_ids=["u3", "u9"], target_count=142, open_count=97,
                 click_count=33, report_count=17, creds_count=12, scheduled_at="2026-06-05",
                 description="Quarterly phishing simulation targeting Finance team."),
        Campaign(id="c2", name="IT Helpdesk Credential Harvest", status="active", vector="Email", template_id="t4",
                 group_ids=["g2"], target_user_ids=["u6", "u10"], target_count=89, open_count=63,
                 click_count=28, report_count=15, creds_count=8, scheduled_at="2026-06-03",
                 description="Simulation testing VPN credential harvesting."),
        Campaign(id="c3", name="CEO Fraud Awareness", status="scheduled", vector="Email", template_id="t3",
                 group_ids=["g3"], target_user_ids=["u8", "u1"], target_count=210, open_count=0,
                 click_count=0, report_count=0, creds_count=0, scheduled_at="2026-06-15",
                 description="BEC simulation targeting all staff."),
        Campaign(id="c4", name="Fake VPN Login Portal", status="completed", vector="Browser", template_id="t4",
                 group_ids=["g4"], target_user_ids=["u3","u4","u5","u6","u9","u10","u11","u12"],
                 target_count=315, open_count=258, click_count=138, report_count=48, creds_count=89,
                 scheduled_at="2026-05-20", description="Browser-based fake login portal simulation."),
        Campaign(id="c5", name="HR Benefits Update", status="completed", vector="Email", template_id="t5",
                 group_ids=["g1"], target_user_ids=["u3", "u9"], target_count=198, open_count=147,
                 click_count=55, report_count=42, creds_count=18, scheduled_at="2026-05-10",
                 description="HR urgency scenario."),
        Campaign(id="c6", name="Slack Impersonation Test", status="draft", vector="Browser", template_id="t7",
                 group_ids=["g2"], target_user_ids=["u6", "u10"], target_count=0, open_count=0,
                 click_count=0, report_count=0, creds_count=0, scheduled_at="",
                 description="Draft campaign for Slack CEO impersonation scenario."),
        Campaign(id="c7", name="Google Account Alert", status="completed", vector="Email", template_id="t6",
                 group_ids=["g5"], target_user_ids=["u10","u11","u12"], target_count=245, open_count=179,
                 click_count=89, report_count=54, creds_count=41, scheduled_at="2026-04-20",
                 description="Google account security alert phishing simulation."),
        Campaign(id="c8", name="Q1 All-Staff Awareness Drill", status="completed", vector="Email", template_id="t2",
                 group_ids=["g4"], target_user_ids=["u3","u4","u5","u6","u9","u10","u11","u12"],
                 target_count=847, open_count=610, click_count=262, report_count=289, creds_count=127,
                 scheduled_at="2026-03-01", description="Company-wide phishing awareness drill."),
    ]
    db.add_all(campaigns)

    await db.commit()
    print("[SEED] Database seeded successfully!")


async def run_seed():
    async with AsyncSessionLocal() as db:
        await seed(db)


if __name__ == "__main__":
    asyncio.run(run_seed())
