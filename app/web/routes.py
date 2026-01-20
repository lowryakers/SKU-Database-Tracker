"""Web routes for HTML interface."""

from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.connection import get_db
from app.models.sku import SKU

router = APIRouter(include_in_schema=False)  # Exclude from API docs
templates = Jinja2Templates(directory="app/templates")


@router.get("/", response_class=HTMLResponse)
async def dashboard(request: Request, db: AsyncSession = Depends(get_db)):
    """Main dashboard page."""
    # Get statistics
    result = await db.execute(select(SKU))
    all_skus = result.scalars().all()

    total_skus = len(all_skus)
    active_skus = sum(1 for sku in all_skus if sku.is_active)
    requires_nsf = sum(1 for sku in all_skus if sku.requires_nsf_certification)

    # Count by NSF status
    nsf_stats = {}
    for sku in all_skus:
        status = sku.nsf_certification_status or "Not Started"
        nsf_stats[status] = nsf_stats.get(status, 0) + 1

    # Count by certification type
    cert_types = {}
    for sku in all_skus:
        if sku.nsf_certification_type:
            cert_types[sku.nsf_certification_type] = cert_types.get(sku.nsf_certification_type, 0) + 1

    stats = {
        "total_skus": total_skus,
        "active_skus": active_skus,
        "inactive_skus": total_skus - active_skus,
        "requires_nsf_certification": requires_nsf,
        "nsf_status_breakdown": nsf_stats,
        "certification_types": cert_types
    }

    return templates.TemplateResponse(
        "dashboard.html",
        {"request": request, "stats": stats}
    )


@router.get("/skus", response_class=HTMLResponse)
async def list_skus_page(
    request: Request,
    category: str = None,
    product_line: str = None,
    nsf_status: str = None,
    search: str = None,
    db: AsyncSession = Depends(get_db)
):
    """SKU list page with filtering."""
    query = select(SKU).where(SKU.is_active == True)

    if category:
        query = query.where(SKU.category == category)
    if product_line:
        query = query.where(SKU.product_line == product_line)
    if nsf_status:
        query = query.where(SKU.nsf_certification_status == nsf_status)
    if search:
        query = query.where(
            (SKU.sku_code.ilike(f"%{search}%")) |
            (SKU.name.ilike(f"%{search}%"))
        )

    result = await db.execute(query)
    skus = result.scalars().all()

    # Get unique values for filters
    all_skus = await db.execute(select(SKU))
    all_skus_list = all_skus.scalars().all()
    categories = set(sku.category for sku in all_skus_list if sku.category)
    product_lines = set(sku.product_line for sku in all_skus_list if sku.product_line)

    return templates.TemplateResponse(
        "sku_list.html",
        {
            "request": request,
            "skus": skus,
            "categories": sorted(categories),
            "product_lines": sorted(product_lines),
            "selected_category": category,
            "selected_product_line": product_line,
            "selected_nsf_status": nsf_status
        }
    )


@router.get("/skus/new", response_class=HTMLResponse)
async def new_sku_page(request: Request):
    """Step-by-step wizard for creating a new SKU."""
    return templates.TemplateResponse(
        "sku_wizard.html",
        {"request": request}
    )


@router.get("/skus/{sku_id}/edit", response_class=HTMLResponse)
async def edit_sku_page(request: Request, sku_id: int, db: AsyncSession = Depends(get_db)):
    """Page for editing an existing SKU."""
    result = await db.execute(select(SKU).where(SKU.id == sku_id))
    sku = result.scalar_one_or_none()

    if not sku:
        return templates.TemplateResponse(
            "error.html",
            {"request": request, "message": f"SKU with ID {sku_id} not found"},
            status_code=404
        )

    return templates.TemplateResponse(
        "sku_form.html",
        {"request": request, "sku": sku, "action": "Update"}
    )


@router.get("/skus/nsf", response_class=HTMLResponse)
async def nsf_skus_page(request: Request, db: AsyncSession = Depends(get_db)):
    """Page showing SKUs that require NSF certification."""
    result = await db.execute(
        select(SKU).where(SKU.requires_nsf_certification == True)
    )
    skus = result.scalars().all()

    return templates.TemplateResponse(
        "nsf_certification.html",
        {"request": request, "skus": skus}
    )


@router.get("/export", response_class=HTMLResponse)
async def export_page(request: Request, db: AsyncSession = Depends(get_db)):
    """Export data page."""
    result = await db.execute(select(SKU))
    skus = result.scalars().all()

    # Get unique certification types
    cert_types = set(sku.nsf_certification_type for sku in skus if sku.nsf_certification_type)

    return templates.TemplateResponse(
        "export.html",
        {"request": request, "skus": skus, "cert_types": sorted(cert_types)}
    )


@router.get("/validation", response_class=HTMLResponse)
async def validation_guide_page(request: Request):
    """NSF compliance validation guide page."""
    return templates.TemplateResponse(
        "validation_guide.html",
        {"request": request}
    )
