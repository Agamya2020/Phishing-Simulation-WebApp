from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


# ─── Department ────────────────────────────────────────────────────────────────

class DepartmentOut(BaseModel):
    id: str
    name: str
    code: str
    head: str
    sub_depts: int

    model_config = {"from_attributes": True}


class DepartmentCreate(BaseModel):
    name: str
    code: str
    head: str
    sub_depts: int = 0


# ─── User ──────────────────────────────────────────────────────────────────────

class UserOut(BaseModel):
    id: str
    name: str
    email: str
    role: str
    department_id: Optional[str] = None
    status: str
    risk_score: int
    created_at: datetime
    last_seen_at: datetime

    model_config = {"from_attributes": True}


class UserCreate(BaseModel):
    name: str
    email: str
    role: str = "employee"
    department_id: Optional[str] = None
    status: str = "active"


class UserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    role: Optional[str] = None
    department_id: Optional[str] = None
    status: Optional[str] = None
    risk_score: Optional[int] = None


# ─── Group ─────────────────────────────────────────────────────────────────────

class GroupOut(BaseModel):
    id: str
    name: str
    department_id: Optional[str] = None
    member_ids: list[str]
    updated_at: datetime

    model_config = {"from_attributes": True}


class GroupCreate(BaseModel):
    name: str
    department_id: Optional[str] = None
    member_ids: list[str] = []


# ─── Template ──────────────────────────────────────────────────────────────────

class TemplateOut(BaseModel):
    id: str
    name: str
    category: str
    vector: str
    subject: str
    sender: str
    body: str
    uses: int
    score: int
    created_at: datetime

    model_config = {"from_attributes": True}


class TemplateCreate(BaseModel):
    name: str
    category: str
    vector: str = "Email"
    subject: str
    sender: str
    body: str
    score: int = 50


# ─── Campaign ──────────────────────────────────────────────────────────────────

class CampaignOut(BaseModel):
    id: str
    name: str
    description: str
    status: str
    vector: str
    template_id: Optional[str] = None
    group_ids: list[str]
    target_user_ids: list[str]
    target_count: int
    open_count: int
    click_count: int
    report_count: int
    creds_count: int
    scheduled_at: str
    send_immediately: bool
    created_at: datetime
    ended_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class CampaignCreate(BaseModel):
    name: str
    description: str = ""
    vector: str = "Email"
    template_id: Optional[str] = None
    group_ids: list[str] = []
    target_user_ids: list[str] = []  # specific users selected from groups
    scheduled_at: str = ""
    send_immediately: bool = False


class CampaignUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    scheduled_at: Optional[str] = None


# ─── Campaign Event ────────────────────────────────────────────────────────────

class EventOut(BaseModel):
    id: str
    campaign_id: str
    user_id: Optional[str] = None
    user_email: str
    event_type: str
    timestamp: datetime

    model_config = {"from_attributes": True}
