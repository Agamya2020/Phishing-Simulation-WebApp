import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Integer, Float, Boolean, DateTime, ForeignKey, Text, Enum as SaEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import ARRAY
from app.core.db import Base


def now_utc():
    return datetime.now(timezone.utc)


class Department(Base):
    __tablename__ = "departments"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: f"d{uuid.uuid4().hex[:8]}")
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    code: Mapped[str] = mapped_column(String(20), nullable=False)
    head: Mapped[str] = mapped_column(String(120), nullable=False)
    sub_depts: Mapped[int] = mapped_column(Integer, default=0)

    users: Mapped[list["User"]] = relationship("User", back_populates="department", lazy="select")
    groups: Mapped[list["Group"]] = relationship("Group", back_populates="department", lazy="select")


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: f"u{uuid.uuid4().hex[:8]}")
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    role: Mapped[str] = mapped_column(String(30), default="employee")
    department_id: Mapped[str] = mapped_column(String, ForeignKey("departments.id"), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="active")
    risk_score: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)
    last_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)

    department: Mapped["Department"] = relationship("Department", back_populates="users")


class Group(Base):
    __tablename__ = "groups"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: f"g{uuid.uuid4().hex[:8]}")
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    department_id: Mapped[str] = mapped_column(String, ForeignKey("departments.id"), nullable=True)
    member_ids: Mapped[list] = mapped_column(ARRAY(String), default=list)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc, onupdate=now_utc)

    department: Mapped["Department"] = relationship("Department", back_populates="groups")


class Template(Base):
    __tablename__ = "templates"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: f"t{uuid.uuid4().hex[:8]}")
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    category: Mapped[str] = mapped_column(String(100))
    vector: Mapped[str] = mapped_column(String(30), default="Email")
    subject: Mapped[str] = mapped_column(String(500), nullable=False)
    sender: Mapped[str] = mapped_column(String(300), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    uses: Mapped[int] = mapped_column(Integer, default=0)
    score: Mapped[int] = mapped_column(Integer, default=50)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)


class Campaign(Base):
    __tablename__ = "campaigns"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: f"c{uuid.uuid4().hex[:8]}")
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(30), default="draft")
    vector: Mapped[str] = mapped_column(String(30), default="Email")
    template_id: Mapped[str] = mapped_column(String, ForeignKey("templates.id"), nullable=True)
    group_ids: Mapped[list] = mapped_column(ARRAY(String), default=list)
    target_user_ids: Mapped[list] = mapped_column(ARRAY(String), default=list)
    target_count: Mapped[int] = mapped_column(Integer, default=0)
    open_count: Mapped[int] = mapped_column(Integer, default=0)
    click_count: Mapped[int] = mapped_column(Integer, default=0)
    report_count: Mapped[int] = mapped_column(Integer, default=0)
    creds_count: Mapped[int] = mapped_column(Integer, default=0)
    scheduled_at: Mapped[str] = mapped_column(String(30), default="")
    send_immediately: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)
    ended_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)

    template: Mapped["Template"] = relationship("Template", lazy="select")
    events: Mapped[list["CampaignEvent"]] = relationship("CampaignEvent", back_populates="campaign", lazy="select")


class CampaignEvent(Base):
    __tablename__ = "campaign_events"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: uuid.uuid4().hex)
    campaign_id: Mapped[str] = mapped_column(String, ForeignKey("campaigns.id"), nullable=False)
    user_id: Mapped[str] = mapped_column(String, ForeignKey("users.id"), nullable=True)
    user_email: Mapped[str] = mapped_column(String(255))
    event_type: Mapped[str] = mapped_column(String(50))  # sent, opened, clicked, reported, creds_entered
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)
    metadata_json: Mapped[str] = mapped_column(Text, default="{}")

    campaign: Mapped["Campaign"] = relationship("Campaign", back_populates="events")
