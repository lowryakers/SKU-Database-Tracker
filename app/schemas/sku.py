"""Pydantic schemas for SKU data validation with NSF certification support."""

from datetime import datetime, date
from typing import Optional
from pydantic import BaseModel, Field, EmailStr, ConfigDict


class IngredientBase(BaseModel):
    """Base schema for ingredient."""

    name: str = Field(..., min_length=1, max_length=255, description="Ingredient name")
    amount: Optional[str] = Field(None, max_length=100, description="Amount (e.g., '500mg')")
    unit: Optional[str] = Field(None, max_length=50, description="Unit of measurement")
    source: Optional[str] = Field(None, max_length=255, description="Source/form (e.g., 'Ascorbic Acid')")
    percent_daily_value: Optional[str] = Field(None, max_length=50, description="% Daily Value")
    ingredient_supplier: Optional[str] = Field(None, max_length=255, description="Ingredient supplier")
    cas_number: Optional[str] = Field(None, max_length=50, description="CAS registry number")
    display_order: int = Field(0, description="Display order in formulation")
    is_active_ingredient: bool = Field(False, description="Is this an active ingredient?")
    is_allergen: bool = Field(False, description="Is this an allergen?")


class IngredientCreate(IngredientBase):
    """Schema for creating a new ingredient."""
    pass


class IngredientResponse(IngredientBase):
    """Schema for ingredient responses."""

    id: int
    sku_id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DocumentInfo(BaseModel):
    """Schema for document information."""

    name: str = Field(..., description="Document name")
    url: str = Field(..., description="Document URL or path")
    type: Optional[str] = Field(None, description="Document type (pdf, docx, etc.)")
    upload_date: Optional[str] = Field(None, description="Upload date")


class SharedWithInfo(BaseModel):
    """Schema for sharing information."""

    email: EmailStr = Field(..., description="Email of person/organization shared with")
    role: Optional[str] = Field(None, description="Role (vendor, partner, certifying_body, etc.)")
    shared_date: Optional[str] = Field(None, description="Date shared")
    access_level: Optional[str] = Field("view", description="Access level (view, edit)")


class SKUBase(BaseModel):
    """Base SKU schema with all NSF-required fields."""

    # Basic product information
    sku_code: str = Field(..., min_length=1, max_length=100, description="Unique SKU code")
    name: str = Field(..., min_length=1, max_length=255, description="Product name")
    brand_name: Optional[str] = Field(None, max_length=255, description="Brand name")
    product_type: Optional[str] = Field(None, max_length=100, description="Product type (Dietary Supplement, Food, etc.)")
    category: Optional[str] = Field(None, max_length=100, description="Product category")
    description: Optional[str] = Field(None, description="Product description")

    # Inventory tracking
    quantity: int = Field(0, ge=0, description="Quantity in stock")
    unit_price: Optional[float] = Field(None, ge=0, description="Price per unit")
    storage_location: Optional[str] = Field(None, max_length=255, description="Storage location")

    # Product specifications
    net_content: Optional[str] = Field(None, max_length=100, description="Net content (e.g., '500mg', '60 capsules')")
    serving_size: Optional[str] = Field(None, max_length=100, description="Serving size")
    servings_per_container: Optional[int] = Field(None, ge=1, description="Servings per container")

    # Formulation & ingredients
    formulation_details: Optional[str] = Field(None, description="Detailed formulation information")
    allergens: Optional[str] = Field(None, description="Allergen information")

    # Manufacturing information
    manufacturer_name: Optional[str] = Field(None, max_length=255, description="Manufacturer name")
    manufacturer_facility: Optional[str] = Field(None, max_length=255, description="Facility name")
    manufacturer_address: Optional[str] = Field(None, description="Full manufacturing address")
    manufacturer_city: Optional[str] = Field(None, max_length=100, description="City")
    manufacturer_state: Optional[str] = Field(None, max_length=100, description="State/Province")
    manufacturer_country: Optional[str] = Field(None, max_length=100, description="Country")
    manufacturer_facility_id: Optional[str] = Field(None, max_length=100, description="Facility ID number")

    # Batch/lot tracking
    lot_number: Optional[str] = Field(None, max_length=100, description="Lot number")
    batch_number: Optional[str] = Field(None, max_length=100, description="Batch number")
    manufacturing_date: Optional[date] = Field(None, description="Manufacturing date")
    expiration_date: Optional[date] = Field(None, description="Expiration date")

    # Supplier information
    supplier_name: Optional[str] = Field(None, max_length=255, description="Supplier name")
    supplier_contact: Optional[str] = Field(None, max_length=255, description="Supplier contact person")
    supplier_email: Optional[EmailStr] = Field(None, description="Supplier email")
    supplier_phone: Optional[str] = Field(None, max_length=50, description="Supplier phone")
    supplier_address: Optional[str] = Field(None, description="Supplier address")

    # NSF Certification information
    nsf_certification_type: Optional[str] = Field(
        None,
        max_length=100,
        description="NSF certification type (NSF Certified for Sport, NSF/ANSI 173, NSF 229, NSF 527, etc.)"
    )
    nsf_certification_status: Optional[str] = Field(
        None,
        max_length=50,
        description="Status (Not Started, In Progress, Certified, Expired, Pending Renewal)"
    )
    nsf_certification_number: Optional[str] = Field(None, max_length=100, description="NSF certification number")
    nsf_certification_date: Optional[date] = Field(None, description="NSF certification date")
    nsf_expiration_date: Optional[date] = Field(None, description="NSF expiration date")
    nsf_next_audit_date: Optional[date] = Field(None, description="Next NSF audit date")
    nsf_last_test_date: Optional[date] = Field(None, description="Last test date")
    nsf_banned_substances_tested: bool = Field(False, description="Banned substances tested (290+ for Sport)")
    nsf_test_results: Optional[str] = Field(None, description="Test results summary")

    # Label claims and intended use
    label_claims: Optional[str] = Field(None, description="Label claims")
    intended_use: Optional[str] = Field(None, description="Intended use")
    directions_for_use: Optional[str] = Field(None, description="Directions for use")
    warnings: Optional[str] = Field(None, description="Warnings and precautions")

    # Documentation URLs
    sds_document_url: Optional[str] = Field(None, max_length=500, description="Safety Data Sheet URL")
    coa_document_url: Optional[str] = Field(None, max_length=500, description="Certificate of Analysis URL")
    label_image_url: Optional[str] = Field(None, max_length=500, description="Product label image URL")

    # Contact information
    primary_contact_name: Optional[str] = Field(None, max_length=255, description="Primary contact name")
    primary_contact_email: Optional[EmailStr] = Field(None, description="Primary contact email")
    primary_contact_phone: Optional[str] = Field(None, max_length=50, description="Primary contact phone")

    # Additional notes
    notes: Optional[str] = Field(None, description="Public notes")
    internal_notes: Optional[str] = Field(None, description="Internal notes (not shared)")

    # Status flags
    is_active: bool = Field(True, description="Is product active?")
    requires_nsf_certification: bool = Field(False, description="Does this require NSF certification?")


class SKUCreate(SKUBase):
    """Schema for creating a new SKU."""
    pass


class SKUUpdate(BaseModel):
    """Schema for updating an existing SKU - all fields optional."""

    sku_code: Optional[str] = Field(None, min_length=1, max_length=100)
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    brand_name: Optional[str] = None
    product_type: Optional[str] = None
    category: Optional[str] = None
    description: Optional[str] = None
    quantity: Optional[int] = Field(None, ge=0)
    unit_price: Optional[float] = Field(None, ge=0)
    storage_location: Optional[str] = None
    net_content: Optional[str] = None
    serving_size: Optional[str] = None
    servings_per_container: Optional[int] = Field(None, ge=1)
    formulation_details: Optional[str] = None
    allergens: Optional[str] = None
    manufacturer_name: Optional[str] = None
    manufacturer_facility: Optional[str] = None
    manufacturer_address: Optional[str] = None
    manufacturer_city: Optional[str] = None
    manufacturer_state: Optional[str] = None
    manufacturer_country: Optional[str] = None
    manufacturer_facility_id: Optional[str] = None
    lot_number: Optional[str] = None
    batch_number: Optional[str] = None
    manufacturing_date: Optional[date] = None
    expiration_date: Optional[date] = None
    supplier_name: Optional[str] = None
    supplier_contact: Optional[str] = None
    supplier_email: Optional[EmailStr] = None
    supplier_phone: Optional[str] = None
    supplier_address: Optional[str] = None
    nsf_certification_type: Optional[str] = None
    nsf_certification_status: Optional[str] = None
    nsf_certification_number: Optional[str] = None
    nsf_certification_date: Optional[date] = None
    nsf_expiration_date: Optional[date] = None
    nsf_next_audit_date: Optional[date] = None
    nsf_last_test_date: Optional[date] = None
    nsf_banned_substances_tested: Optional[bool] = None
    nsf_test_results: Optional[str] = None
    label_claims: Optional[str] = None
    intended_use: Optional[str] = None
    directions_for_use: Optional[str] = None
    warnings: Optional[str] = None
    sds_document_url: Optional[str] = None
    coa_document_url: Optional[str] = None
    label_image_url: Optional[str] = None
    primary_contact_name: Optional[str] = None
    primary_contact_email: Optional[EmailStr] = None
    primary_contact_phone: Optional[str] = None
    notes: Optional[str] = None
    internal_notes: Optional[str] = None
    is_active: Optional[bool] = None
    requires_nsf_certification: Optional[bool] = None


class SKUResponse(SKUBase):
    """Schema for SKU responses."""

    id: int
    ingredients: Optional[dict] = None
    additional_documents: Optional[dict] = None
    shared_with: Optional[dict] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SKUSummary(BaseModel):
    """Simplified SKU schema for list views."""

    id: int
    sku_code: str
    name: str
    brand_name: Optional[str] = None
    product_type: Optional[str] = None
    category: Optional[str] = None
    quantity: int
    nsf_certification_status: Optional[str] = None
    nsf_certification_type: Optional[str] = None
    requires_nsf_certification: bool
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SKUExportRequest(BaseModel):
    """Schema for export requests."""

    format: str = Field(..., description="Export format (excel, pdf, csv)")
    sku_ids: Optional[list[int]] = Field(None, description="Specific SKU IDs to export (None = all)")
    include_ingredients: bool = Field(True, description="Include ingredient details")
    include_internal_notes: bool = Field(False, description="Include internal notes")
    certification_type: Optional[str] = Field(None, description="Filter by certification type")


class ShareSKURequest(BaseModel):
    """Schema for sharing SKU data."""

    sku_ids: list[int] = Field(..., description="SKU IDs to share")
    recipient_email: EmailStr = Field(..., description="Recipient email address")
    recipient_role: Optional[str] = Field("partner", description="Recipient role")
    access_level: str = Field("view", description="Access level (view, edit)")
    message: Optional[str] = Field(None, description="Optional message to recipient")
    include_sensitive_data: bool = Field(False, description="Include internal notes and pricing")
