"""API routes for SKU management."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.connection import get_db
from app.models.sku import SKU
from app.schemas import SKUCreate, SKUUpdate, SKUResponse

router = APIRouter(prefix="/api/v1", tags=["skus"])


@router.post("/skus", response_model=SKUResponse, status_code=status.HTTP_201_CREATED)
async def create_sku(
    sku_data: SKUCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new SKU."""
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


@router.get("/skus", response_model=list[SKUResponse])
async def list_skus(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    """List all SKUs with pagination."""
    result = await db.execute(select(SKU).offset(skip).limit(limit))
    skus = result.scalars().all()
    return skus


@router.get("/skus/{sku_id}", response_model=SKUResponse)
async def get_sku(
    sku_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get a specific SKU by ID."""
    result = await db.execute(select(SKU).where(SKU.id == sku_id))
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
