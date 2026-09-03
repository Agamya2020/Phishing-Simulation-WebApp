"""Users, Groups, Templates, Departments CRUD routers."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from app.core.db import get_db
from app.core.security import require_admin
from app.models.models import User, Group, Template, Department
from app.schemas.schemas import (
    UserOut, UserCreate, UserUpdate,
    GroupOut, GroupCreate,
    TemplateOut, TemplateCreate, TemplateUpdate,
    DepartmentOut, DepartmentCreate,
)

# ─── Users ─────────────────────────────────────────────────────────────────────
users_router = APIRouter(
    prefix="/users",
    tags=["users"],
    dependencies=[
        Depends(require_admin)
    ],
)


@users_router.get("", response_model=list[UserOut])
async def list_users(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).order_by(User.name))
    return result.scalars().all()


@users_router.get("/{user_id}", response_model=UserOut)
async def get_user(user_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@users_router.post("", response_model=UserOut)
async def create_user(payload: UserCreate, db: AsyncSession = Depends(get_db)):
    user = User(**payload.model_dump())
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


@users_router.patch("/{user_id}", response_model=UserOut)
async def update_user(user_id: str, payload: UserUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(user, field, value)
    await db.commit()
    await db.refresh(user)
    return user


@users_router.delete("/{user_id}")
async def delete_user(user_id: str, db: AsyncSession = Depends(get_db)):
    await db.execute(delete(User).where(User.id == user_id))
    await db.commit()
    return {"ok": True}


# ─── Groups ────────────────────────────────────────────────────────────────────
groups_router = APIRouter(
    prefix="/groups",
    tags=["groups"],
    dependencies=[
        Depends(require_admin)
    ],
)


@groups_router.get("", response_model=list[GroupOut])
async def list_groups(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Group).order_by(Group.name))
    return result.scalars().all()


@groups_router.post("", response_model=GroupOut)
async def create_group(payload: GroupCreate, db: AsyncSession = Depends(get_db)):
    group = Group(**payload.model_dump())
    db.add(group)
    await db.commit()
    await db.refresh(group)
    return group


@groups_router.patch("/{group_id}", response_model=GroupOut)
async def update_group(group_id: str, payload: GroupCreate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Group).where(Group.id == group_id))
    group = result.scalar_one_or_none()
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    for field, value in payload.model_dump(exclude_none=True).items():
        setattr(group, field, value)
    await db.commit()
    await db.refresh(group)
    return group


@groups_router.delete("/{group_id}")
async def delete_group(group_id: str, db: AsyncSession = Depends(get_db)):
    await db.execute(delete(Group).where(Group.id == group_id))
    await db.commit()
    return {"ok": True}


# ─── Templates ─────────────────────────────────────────────────────────────────
templates_router = APIRouter(
    prefix="/templates",
    tags=["templates"],
    dependencies=[
        Depends(require_admin)
    ],
)


@templates_router.get("", response_model=list[TemplateOut])
async def list_templates(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Template).order_by(Template.created_at.desc()))
    return result.scalars().all()


@templates_router.get("/{template_id}", response_model=TemplateOut)
async def get_template(template_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Template).where(Template.id == template_id))
    template = result.scalar_one_or_none()
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    return template


@templates_router.post("", response_model=TemplateOut)
async def create_template(payload: TemplateCreate, db: AsyncSession = Depends(get_db)):
    template = Template(**payload.model_dump())
    db.add(template)
    await db.commit()
    await db.refresh(template)
    return template


@templates_router.patch("/{template_id}", response_model=TemplateOut)
async def update_template(template_id: str, payload: TemplateUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Template).where(Template.id == template_id))
    template = result.scalar_one_or_none()
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(template, field, value)
    await db.commit()
    await db.refresh(template)
    return template


@templates_router.delete("/{template_id}")
async def delete_template(template_id: str, db: AsyncSession = Depends(get_db)):
    await db.execute(delete(Template).where(Template.id == template_id))
    await db.commit()
    return {"ok": True}


# ─── Departments ───────────────────────────────────────────────────────────────
departments_router = APIRouter(
    prefix="/departments",
    tags=["departments"],
    dependencies=[
        Depends(require_admin)
    ],
)


@departments_router.get("", response_model=list[DepartmentOut])
async def list_departments(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Department).order_by(Department.name))
    return result.scalars().all()


@departments_router.post("", response_model=DepartmentOut)
async def create_department(payload: DepartmentCreate, db: AsyncSession = Depends(get_db)):
    dept = Department(**payload.model_dump())
    db.add(dept)
    await db.commit()
    await db.refresh(dept)
    return dept


@departments_router.delete("/{dept_id}")
async def delete_department(dept_id: str, db: AsyncSession = Depends(get_db)):
    await db.execute(delete(Department).where(Department.id == dept_id))
    await db.commit()
    return {"ok": True}
