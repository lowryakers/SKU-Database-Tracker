"""Database models package."""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Base class for all database models."""
    pass


from app.models.sku import SKU

__all__ = ["Base", "SKU"]
