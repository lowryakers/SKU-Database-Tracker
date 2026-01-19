"""API routes for SKU management with NSF certification support."""

from fastapi import APIRouter, Depends, HTTPException, status, Response
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
import io

from app.database.connection import get_db
from app.models.sku import SKU, Ingredient
from app.schemas import (
    SKUCreate,
    SKUUpdate,
    SKUResponse,
    SKUSummary,
    SKUExportRequest,
    ShareSKURequest,
    IngredientCreate,
    IngredientResponse,
)
from app.services.export import ExportService

router = APIRouter(prefix="/api/v1", tags=["skus"])


@router.post("/skus", response_model=SKUResponse, status_code=status.HTTP_201_CREATED)
async def create_sku(
    sku_data: SKUCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new SKU with all NSF certification fields."""
    # Check if SKU code already exists
    result = await db.execute(select(SKU).where(SKU.sku_code == sku_data.sku_code))
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"SKU with code '{sku_data.sku_code}' already exists"
        )

    sku = SKU(**sku_data.model_dump())
    db.add(sku)
    await db.commit()
    await db.refresh(sku)
    return sku


@router.get("/skus", response_model=list[SKUSummary])
async def list_skus(
    skip: int = 0,
    limit: int = 100,
    category: str = None,
    nsf_status: str = None,
    requires_nsf: bool = None,
    active_only: bool = True,
    db: AsyncSession = Depends(get_db)
):
    """
    List all SKUs with pagination and filtering.

    Filters:
    - category: Filter by product category
    - nsf_status: Filter by NSF certification status
    - requires_nsf: Filter by NSF requirement
    - active_only: Show only active products (default: True)
    """
    query = select(SKU)

    if active_only:
        query = query.where(SKU.is_active == True)
    if category:
        query = query.where(SKU.category == category)
    if nsf_status:
        query = query.where(SKU.nsf_certification_status == nsf_status)
    if requires_nsf is not None:
        query = query.where(SKU.requires_nsf_certification == requires_nsf)

    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    skus = result.scalars().all()
    return skus


@router.get("/skus/{sku_id}", response_model=SKUResponse)
async def get_sku(
    sku_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get a specific SKU by ID with all details."""
    result = await db.execute(
        select(SKU)
        .options(selectinload(SKU.ingredients_list))
        .where(SKU.id == sku_id)
    )
    sku = result.scalar_one_or_none()
    if not sku:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"SKU with id {sku_id} not found"
        )
    return sku


@router.put("/skus/{sku_id}", response_model=SKUResponse)
async def update_sku(
    sku_id: int,
    sku_data: SKUUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update an existing SKU."""
    result = await db.execute(select(SKU).where(SKU.id == sku_id))
    sku = result.scalar_one_or_none()
    if not sku:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"SKU with id {sku_id} not found"
        )

    # Update only provided fields
    update_data = sku_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(sku, field, value)

    await db.commit()
    await db.refresh(sku)
    return sku


@router.delete("/skus/{sku_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_sku(
    sku_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Delete a SKU."""
    result = await db.execute(select(SKU).where(SKU.id == sku_id))
    sku = result.scalar_one_or_none()
    if not sku:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"SKU with id {sku_id} not found"
        )

    await db.delete(sku)
    await db.commit()


# Ingredient Management
@router.post("/skus/{sku_id}/ingredients", response_model=IngredientResponse, status_code=status.HTTP_201_CREATED)
async def add_ingredient(
    sku_id: int,
    ingredient_data: IngredientCreate,
    db: AsyncSession = Depends(get_db)
):
    """Add an ingredient to a SKU."""
    # Verify SKU exists
    result = await db.execute(select(SKU).where(SKU.id == sku_id))
    sku = result.scalar_one_or_none()
    if not sku:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"SKU with id {sku_id} not found"
        )

    ingredient = Ingredient(sku_id=sku_id, **ingredient_data.model_dump())
    db.add(ingredient)
    await db.commit()
    await db.refresh(ingredient)
    return ingredient


@router.get("/skus/{sku_id}/ingredients", response_model=list[IngredientResponse])
async def list_ingredients(
    sku_id: int,
    db: AsyncSession = Depends(get_db)
):
    """List all ingredients for a SKU."""
    result = await db.execute(
        select(Ingredient)
        .where(Ingredient.sku_id == sku_id)
        .order_by(Ingredient.display_order)
    )
    ingredients = result.scalars().all()
    return ingredients


@router.delete("/ingredients/{ingredient_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_ingredient(
    ingredient_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Delete an ingredient."""
    result = await db.execute(select(Ingredient).where(Ingredient.id == ingredient_id))
    ingredient = result.scalar_one_or_none()
    if not ingredient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Ingredient with id {ingredient_id} not found"
        )

    await db.delete(ingredient)
    await db.commit()


# Export Endpoints
@router.post("/skus/export/excel")
async def export_skus_excel(
    export_request: SKUExportRequest,
    db: AsyncSession = Depends(get_db)
):
    """Export SKUs to Excel format for NSF submission."""
    query = select(SKU).options(selectinload(SKU.ingredients_list))

    if export_request.sku_ids:
        query = query.where(SKU.id.in_(export_request.sku_ids))
    if export_request.certification_type:
        query = query.where(SKU.nsf_certification_type == export_request.certification_type)

    result = await db.execute(query)
    skus = result.scalars().all()

    if not skus:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No SKUs found matching the criteria"
        )

    excel_data = ExportService.export_to_excel(
        skus,
        include_ingredients=export_request.include_ingredients,
        include_internal_notes=export_request.include_internal_notes
    )

    return StreamingResponse(
        io.BytesIO(excel_data),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename=sku_export.xlsx"}
    )


@router.post("/skus/export/pdf")
async def export_skus_pdf(
    export_request: SKUExportRequest,
    db: AsyncSession = Depends(get_db)
):
    """Export SKUs to PDF format for NSF submission."""
    query = select(SKU).options(selectinload(SKU.ingredients_list))

    if export_request.sku_ids:
        query = query.where(SKU.id.in_(export_request.sku_ids))
    if export_request.certification_type:
        query = query.where(SKU.nsf_certification_type == export_request.certification_type)

    result = await db.execute(query)
    skus = result.scalars().all()

    if not skus:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No SKUs found matching the criteria"
        )

    pdf_data = ExportService.export_to_pdf(
        skus,
        include_ingredients=export_request.include_ingredients,
        include_internal_notes=export_request.include_internal_notes
    )

    return StreamingResponse(
        io.BytesIO(pdf_data),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=sku_export.pdf"}
    )


@router.post("/skus/export/csv")
async def export_skus_csv(
    export_request: SKUExportRequest,
    db: AsyncSession = Depends(get_db)
):
    """Export SKUs to CSV format."""
    query = select(SKU)

    if export_request.sku_ids:
        query = query.where(SKU.id.in_(export_request.sku_ids))
    if export_request.certification_type:
        query = query.where(SKU.nsf_certification_type == export_request.certification_type)

    result = await db.execute(query)
    skus = result.scalars().all()

    if not skus:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No SKUs found matching the criteria"
        )

    csv_data = ExportService.export_to_csv(
        skus,
        include_internal_notes=export_request.include_internal_notes
    )

    return Response(
        content=csv_data,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=sku_export.csv"}
    )


# Statistics Endpoint
@router.get("/skus/stats/summary")
async def get_stats(db: AsyncSession = Depends(get_db)):
    """Get SKU statistics and NSF certification overview."""
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

    return {
        "total_skus": total_skus,
        "active_skus": active_skus,
        "inactive_skus": total_skus - active_skus,
        "requires_nsf_certification": requires_nsf,
        "nsf_status_breakdown": nsf_stats,
        "certification_types": cert_types
    }
