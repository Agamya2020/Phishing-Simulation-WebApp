from pathlib import Path

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from app.core.security import require_admin_page


BASE_DIR = Path(__file__).resolve().parent.parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))
router = APIRouter(tags=["admin-ui"])


@router.get("/admin", include_in_schema=False)
async def admin_root():
    return RedirectResponse(url="/admin/login", status_code=302)


@router.get(
    "/admin/login",
    response_class=HTMLResponse,
    include_in_schema=False,
)
async def admin_login(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="login.html",
        context={},
    )


@router.get(
    "/admin/dashboard",
    response_class=HTMLResponse,
    include_in_schema=False,
)
async def admin_dashboard(
    request: Request,
    admin: str = Depends(require_admin_page),
):
    return templates.TemplateResponse(
        request=request,
        name="dashboard.html",
        context={"admin_username": admin},
    )


@router.get(
    "/admin/campaigns",
    response_class=HTMLResponse,
    include_in_schema=False,
)
async def admin_campaigns(
    request: Request,
    admin: str = Depends(require_admin_page),
):
    return templates.TemplateResponse(
        request=request,
        name="campaigns.html",
        context={"admin_username": admin},
    )


@router.get(
    "/admin/templates",
    response_class=HTMLResponse,
    include_in_schema=False,
)
async def admin_templates(
    request: Request,
    admin: str = Depends(require_admin_page),
):
    return templates.TemplateResponse(
        request=request,
        name="templates.html",
        context={"admin_username": admin},
    )


@router.get(
    "/admin/users",
    response_class=HTMLResponse,
    include_in_schema=False,
)
async def admin_users(
    request: Request,
    admin: str = Depends(require_admin_page),
):
    return templates.TemplateResponse(
        request=request,
        name="users.html",
        context={"admin_username": admin},
    )


@router.get(
    "/admin/groups",
    response_class=HTMLResponse,
    include_in_schema=False,
)
async def admin_groups(
    request: Request,
    admin: str = Depends(require_admin_page),
):
    return templates.TemplateResponse(
        request=request,
        name="groups.html",
        context={"admin_username": admin},
    )


@router.get(
    "/admin/departments",
    response_class=HTMLResponse,
    include_in_schema=False,
)
async def admin_departments(
    request: Request,
    admin: str = Depends(require_admin_page),
):
    return templates.TemplateResponse(
        request=request,
        name="departments.html",
        context={"admin_username": admin},
    )


@router.get(
    "/admin/campaigns/{campaign_id}",
    response_class=HTMLResponse,
    include_in_schema=False,
)
async def admin_campaign_detail(
    request: Request,
    campaign_id: str,
    admin: str = Depends(require_admin_page),
):
    return templates.TemplateResponse(
        request=request,
        name="campaign_detail.html",
        context={
            "campaign_id": campaign_id,
            "admin_username": admin,
        },
    )


@router.get(
    "/admin/reports",
    response_class=HTMLResponse,
    include_in_schema=False,
)
async def admin_reports(
    request: Request,
    admin: str = Depends(require_admin_page),
):
    return templates.TemplateResponse(
        request=request,
        name="reports.html",
        context={"admin_username": admin},
    )
