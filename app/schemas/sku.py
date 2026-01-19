"""Pydantic schemas for SKU data validation."""

from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class SKUBase(BaseModel):
    """Base SKU schema."""

    sku_code: str = Field(..., min_length=1, max_length=100, description="Unique SKU code")
    name: str = Field(..., min_length=1, max_length=255, description="Product name")
    description: str | None = Field(None, description="Product description")
    category: str | None = Field(None, max_length=100, description="Product category")
    quantity: int = Field(0, ge=0, description="Quantity in stock")
    unit_price: float | None = Field(None, ge=0, description="Price per unit")
    supplier: str | None = Field(None, max_length=255, description="Supplier name")
    location: str | None = Field(None, max_length=255, description="Storage location")


class SKUCreate(SKUBase):
    """Schema for creating a new SKU."""
    pass


class SKUUpdate(BaseModel):
    """Schema for updating an existing SKU."""

    sku_code: str | None = Field(None, min_length=1, max_length=100)
    name: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = None
    category: str | None = None
    quantity: int | None = Field(None, ge=0)
    unit_price: float | None = Field(None, ge=0)
    supplier: str | None = None
    location: str | None = None


class SKUResponse(SKUBase):
    """Schema for SKU responses."""

    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
