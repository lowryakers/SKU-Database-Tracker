"""SKU database model with NSF certification support."""

from datetime import datetime, date
from sqlalchemy import String, Integer, Float, DateTime, Text, Date, Boolean, JSON, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models import Base


class SKU(Base):
    """
    Enhanced SKU (Stock Keeping Unit) model with NSF certification support.

    Supports NSF Certified for Sport and general NSF certification requirements.
    """

    __tablename__ = "skus"

    # Primary identification
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    sku_code: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)

    # Basic product information
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    brand_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    product_type: Mapped[str | None] = mapped_column(String(100), nullable=True)  # Dietary Supplement, Food, etc.
    category: Mapped[str | None] = mapped_column(String(100), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Inventory tracking
    quantity: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    unit_price: Mapped[float | None] = mapped_column(Float, nullable=True)
    storage_location: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Product specifications
    net_content: Mapped[str | None] = mapped_column(String(100), nullable=True)  # e.g., "500mg", "60 capsules"
    serving_size: Mapped[str | None] = mapped_column(String(100), nullable=True)
    servings_per_container: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Formulation & ingredients (stored as JSON array)
    ingredients: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    # Format: [{"name": "Vitamin C", "amount": "500mg", "source": "Ascorbic Acid", "percent_dv": "556%"}]

    formulation_details: Mapped[str | None] = mapped_column(Text, nullable=True)
    allergens: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Manufacturing information
    manufacturer_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    manufacturer_facility: Mapped[str | None] = mapped_column(String(255), nullable=True)
    manufacturer_address: Mapped[str | None] = mapped_column(Text, nullable=True)
    manufacturer_city: Mapped[str | None] = mapped_column(String(100), nullable=True)
    manufacturer_state: Mapped[str | None] = mapped_column(String(100), nullable=True)
    manufacturer_country: Mapped[str | None] = mapped_column(String(100), nullable=True)
    manufacturer_facility_id: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # Batch/lot tracking
    lot_number: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    batch_number: Mapped[str | None] = mapped_column(String(100), nullable=True)
    manufacturing_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    expiration_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    # Supplier information
    supplier_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    supplier_contact: Mapped[str | None] = mapped_column(String(255), nullable=True)
    supplier_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    supplier_phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    supplier_address: Mapped[str | None] = mapped_column(Text, nullable=True)

    # NSF Certification information
    nsf_certification_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    # Options: "NSF Certified for Sport", "NSF/ANSI 173", "NSF 229", "NSF 527", "NSF 372", etc.

    nsf_certification_status: Mapped[str | None] = mapped_column(String(50), nullable=True)
    # Options: "Not Started", "In Progress", "Certified", "Expired", "Pending Renewal"

    nsf_certification_number: Mapped[str | None] = mapped_column(String(100), nullable=True)
    nsf_certification_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    nsf_expiration_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    nsf_next_audit_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    nsf_last_test_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    nsf_banned_substances_tested: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    nsf_test_results: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Label claims and intended use
    label_claims: Mapped[str | None] = mapped_column(Text, nullable=True)
    intended_use: Mapped[str | None] = mapped_column(Text, nullable=True)
    directions_for_use: Mapped[str | None] = mapped_column(Text, nullable=True)
    warnings: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Documentation links/paths
    sds_document_url: Mapped[str | None] = mapped_column(String(500), nullable=True)  # Safety Data Sheet
    coa_document_url: Mapped[str | None] = mapped_column(String(500), nullable=True)  # Certificate of Analysis
    label_image_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    additional_documents: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    # Format: [{"name": "Lab Report", "url": "https://...", "type": "pdf"}]

    # Contact information
    primary_contact_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    primary_contact_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    primary_contact_phone: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # Sharing and collaboration
    shared_with: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    # Format: [{"email": "partner@example.com", "role": "vendor", "shared_date": "2025-01-19"}]

    # Additional notes
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    internal_notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Status flags
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    requires_nsf_certification: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Tagging and grouping
    tags: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    # Format: ["sports-nutrition", "pre-workout", "nsf-certified"]

    product_line: Mapped[str | None] = mapped_column(String(255), nullable=True)
    # e.g., "Premium Series", "Budget Line", "Professional Grade"

    # File attachments
    bom_file_path: Mapped[str | None] = mapped_column(String(500), nullable=True)  # Bill of Materials
    artwork_file_path: Mapped[str | None] = mapped_column(String(500), nullable=True)  # Product artwork

    # Completion tracking for multi-step wizard
    completion_status: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    # Format: {"basic_info": "complete", "manufacturing": "incomplete", "nsf": "skipped"}

    completion_percentage: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    # 0-100 percentage of completed fields

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # Relationships
    ingredients_list = relationship("Ingredient", back_populates="sku", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<SKU(sku_code='{self.sku_code}', name='{self.name}', nsf_status='{self.nsf_certification_status}')>"


class Ingredient(Base):
    """Individual ingredient in a SKU formulation."""

    __tablename__ = "ingredients"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    sku_id: Mapped[int] = mapped_column(Integer, ForeignKey("skus.id"), nullable=False, index=True)

    # Ingredient details
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    amount: Mapped[str | None] = mapped_column(String(100), nullable=True)  # e.g., "500mg"
    unit: Mapped[str | None] = mapped_column(String(50), nullable=True)  # e.g., "mg", "g", "IU"
    source: Mapped[str | None] = mapped_column(String(255), nullable=True)  # e.g., "Ascorbic Acid"
    percent_daily_value: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # Supplier information for this ingredient
    ingredient_supplier: Mapped[str | None] = mapped_column(String(255), nullable=True)
    cas_number: Mapped[str | None] = mapped_column(String(50), nullable=True)  # Chemical Abstracts Service number

    # Order in formulation
    display_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Flags
    is_active_ingredient: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_allergen: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # Relationship back to SKU
    sku = relationship("SKU", back_populates="ingredients_list")

    def __repr__(self) -> str:
        return f"<Ingredient(name='{self.name}', amount='{self.amount}')>"
