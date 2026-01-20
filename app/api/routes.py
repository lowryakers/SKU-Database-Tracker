"""API routes for SKU management with NSF certification support."""

from fastapi import APIRouter, Depends, HTTPException, status, Response, UploadFile, File, Form
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from typing import List, Dict, Optional
import io
import json

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
    ValidationResult,
    SKUWithValidation,
    ValidateSKURequest,
    ValidationWarningSchema,
)
from app.services.export import ExportService
from app.services.validation import NSFValidator
from app.services.bulk_upload import BulkUploadService

router = APIRouter(prefix="/api/v1", tags=["skus"])

# Initialize NSF Validator
validator = NSFValidator()


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
    if export_request.product_line:
        query = query.where(SKU.product_line == export_request.product_line)
    if export_request.tags:
        # Filter by any of the provided tags
        for tag in export_request.tags:
            query = query.where(SKU.tags.contains([tag]))

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
    if export_request.product_line:
        query = query.where(SKU.product_line == export_request.product_line)
    if export_request.tags:
        for tag in export_request.tags:
            query = query.where(SKU.tags.contains([tag]))

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
    if export_request.product_line:
        query = query.where(SKU.product_line == export_request.product_line)
    if export_request.tags:
        for tag in export_request.tags:
            query = query.where(SKU.tags.contains([tag]))

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


# AUTOCOMPLETE ENDPOINTS

@router.get("/autocomplete/brands", tags=["autocomplete"])
async def get_brands_autocomplete(db: AsyncSession = Depends(get_db)):
    """Get list of unique brand names for autocomplete."""
    result = await db.execute(select(SKU.brand_name).distinct().where(SKU.brand_name.isnot(None)))
    brands = [row[0] for row in result.all() if row[0]]
    return {"brands": sorted(brands)}


@router.get("/autocomplete/manufacturers", tags=["autocomplete"])
async def get_manufacturers_autocomplete(db: AsyncSession = Depends(get_db)):
    """
    Get list of manufacturers with their full details for autocomplete.

    Returns manufacturer names with associated facility information.
    """
    result = await db.execute(
        select(
            SKU.manufacturer_name,
            SKU.manufacturer_facility,
            SKU.manufacturer_address,
            SKU.manufacturer_city,
            SKU.manufacturer_state,
            SKU.manufacturer_country,
            SKU.manufacturer_facility_id
        )
        .distinct()
        .where(SKU.manufacturer_name.isnot(None))
    )

    manufacturers = {}
    for row in result.all():
        if row[0]:  # manufacturer_name exists
            # Use the most complete record for each manufacturer
            if row[0] not in manufacturers or sum(1 for x in row[1:] if x) > sum(1 for x in manufacturers[row[0]].values() if x):
                manufacturers[row[0]] = {
                    "name": row[0],
                    "facility": row[1],
                    "address": row[2],
                    "city": row[3],
                    "state": row[4],
                    "country": row[5],
                    "facility_id": row[6]
                }

    return {"manufacturers": list(manufacturers.values())}


@router.get("/autocomplete/suppliers", tags=["autocomplete"])
async def get_suppliers_autocomplete(db: AsyncSession = Depends(get_db)):
    """
    Get list of suppliers with their full details for autocomplete.

    Returns supplier names with associated contact information.
    """
    result = await db.execute(
        select(
            SKU.supplier_name,
            SKU.supplier_contact,
            SKU.supplier_email,
            SKU.supplier_phone,
            SKU.supplier_address
        )
        .distinct()
        .where(SKU.supplier_name.isnot(None))
    )

    suppliers = {}
    for row in result.all():
        if row[0]:  # supplier_name exists
            # Use the most complete record for each supplier
            if row[0] not in suppliers or sum(1 for x in row[1:] if x) > sum(1 for x in suppliers[row[0]].values() if x):
                suppliers[row[0]] = {
                    "name": row[0],
                    "contact": row[1],
                    "email": row[2],
                    "phone": row[3],
                    "address": row[4]
                }

    return {"suppliers": list(suppliers.values())}


@router.get("/autocomplete/categories", tags=["autocomplete"])
async def get_categories_autocomplete(db: AsyncSession = Depends(get_db)):
    """Get list of unique categories for autocomplete."""
    result = await db.execute(select(SKU.category).distinct().where(SKU.category.isnot(None)))
    categories = [row[0] for row in result.all() if row[0]]
    return {"categories": sorted(categories)}


@router.get("/autocomplete/product-lines", tags=["autocomplete"])
async def get_product_lines_autocomplete(db: AsyncSession = Depends(get_db)):
    """Get list of unique product lines for autocomplete."""
    result = await db.execute(select(SKU.product_line).distinct().where(SKU.product_line.isnot(None)))
    product_lines = [row[0] for row in result.all() if row[0]]
    return {"product_lines": sorted(product_lines)}


@router.get("/autocomplete/states", tags=["autocomplete"])
async def get_states_list():
    """Get list of US states and territories."""
    states = [
        "Alabama", "Alaska", "Arizona", "Arkansas", "California", "Colorado",
        "Connecticut", "Delaware", "Florida", "Georgia", "Hawaii", "Idaho",
        "Illinois", "Indiana", "Iowa", "Kansas", "Kentucky", "Louisiana",
        "Maine", "Maryland", "Massachusetts", "Michigan", "Minnesota",
        "Mississippi", "Missouri", "Montana", "Nebraska", "Nevada",
        "New Hampshire", "New Jersey", "New Mexico", "New York",
        "North Carolina", "North Dakota", "Ohio", "Oklahoma", "Oregon",
        "Pennsylvania", "Rhode Island", "South Carolina", "South Dakota",
        "Tennessee", "Texas", "Utah", "Vermont", "Virginia", "Washington",
        "West Virginia", "Wisconsin", "Wyoming", "Puerto Rico",
        "US Virgin Islands", "Guam", "American Samoa", "Northern Mariana Islands"
    ]
    return {"states": states}


@router.get("/autocomplete/countries", tags=["autocomplete"])
async def get_countries_list():
    """Get list of countries."""
    countries = [
        "United States", "Canada", "Mexico", "United Kingdom", "Germany",
        "France", "Italy", "Spain", "China", "Japan", "South Korea",
        "Australia", "New Zealand", "Brazil", "Argentina", "India",
        "Netherlands", "Belgium", "Switzerland", "Austria", "Sweden",
        "Norway", "Denmark", "Finland", "Poland", "Ireland", "Portugal",
        "Greece", "Czech Republic", "Hungary", "Romania", "Turkey",
        "Israel", "Saudi Arabia", "United Arab Emirates", "Singapore",
        "Malaysia", "Thailand", "Vietnam", "Indonesia", "Philippines",
        "South Africa", "Egypt", "Nigeria", "Kenya"
    ]
    return {"countries": sorted(countries)}
"""Validation endpoint additions for routes.py - to be appended."""


# NSF COMPLIANCE VALIDATION ENDPOINTS

@router.post("/skus/validate", response_model=ValidationResult, tags=["validation"])
async def validate_sku_data(
    request: ValidateSKURequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Validate SKU data for NSF compliance WITHOUT creating it.

    Checks for:
    - Banned substances (290+ for NSF Certified for Sport)
    - NSF certification requirements
    - Data quality and completeness
    - High-risk ingredient patterns

    Returns detailed warnings and suggestions.
    """
    # Convert Pydantic models to dicts for validation
    sku_dict = request.sku_data.model_dump()
    ingredients_list = [ing.model_dump() for ing in request.ingredients] if request.ingredients else []

    # Run validation
    warnings = validator.validate_sku(sku_dict, ingredients_list)
    summary = validator.get_validation_summary(warnings)

    # Convert warnings to schema
    warning_schemas = [ValidationWarningSchema(**w.to_dict()) for w in warnings]

    return ValidationResult(
        **summary,
        warnings=warning_schemas
    )


@router.post("/skus/with-validation", response_model=SKUWithValidation, status_code=status.HTTP_201_CREATED, tags=["skus"])
async def create_sku_with_validation(
    sku_data: SKUCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new SKU with automatic NSF compliance validation.

    This endpoint:
    1. Validates the SKU data for NSF compliance
    2. Checks for banned substances
    3. Verifies required NSF fields
    4. Creates the SKU if validation passes
    5. Returns the SKU with validation results

    If critical issues are found (e.g., banned substances), the SKU is still created
    but flagged with validation warnings.
    """
    # Check if SKU code already exists
    result = await db.execute(select(SKU).where(SKU.sku_code == sku_data.sku_code))
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"SKU with code '{sku_data.sku_code}' already exists"
        )

    # Run validation before creating
    sku_dict = sku_data.model_dump()
    warnings = validator.validate_sku(sku_dict, [])
    summary = validator.get_validation_summary(warnings)
    warning_schemas = [ValidationWarningSchema(**w.to_dict()) for w in warnings]

    # Create the SKU
    sku = SKU(**sku_dict)
    db.add(sku)
    await db.commit()
    await db.refresh(sku)

    # Prepare response with validation
    sku_response = SKUResponse.model_validate(sku)

    validation_result = ValidationResult(
        **summary,
        warnings=warning_schemas
    )

    # Return SKU with validation results
    return SKUWithValidation(
        **sku_response.model_dump(),
        validation=validation_result
    )


@router.get("/skus/{sku_id}/validate", response_model=ValidationResult, tags=["validation"])
async def validate_existing_sku(
    sku_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Validate an existing SKU for NSF compliance.

    Useful for:
    - Checking compliance before NSF submission
    - Re-validating after ingredient changes
    - Periodic compliance checks
    """
    # Get SKU with ingredients
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

    # Convert to dict for validation
    sku_dict = {
        "sku_code": sku.sku_code,
        "name": sku.name,
        "brand_name": sku.brand_name,
        "product_type": sku.product_type,
        "category": sku.category,
        "description": sku.description,
        "requires_nsf_certification": sku.requires_nsf_certification,
        "nsf_certification_type": sku.nsf_certification_type,
        "nsf_certification_status": sku.nsf_certification_status,
        "nsf_banned_substances_tested": sku.nsf_banned_substances_tested,
        "nsf_expiration_date": sku.nsf_expiration_date,
        "manufacturer_name": sku.manufacturer_name,
        "manufacturer_facility": sku.manufacturer_facility,
        "manufacturer_city": sku.manufacturer_city,
        "manufacturer_state": sku.manufacturer_state,
        "manufacturer_country": sku.manufacturer_country,
        "net_content": sku.net_content,
        "serving_size": sku.serving_size,
        "servings_per_container": sku.servings_per_container,
        "label_claims": sku.label_claims,
        "intended_use": sku.intended_use,
        "directions_for_use": sku.directions_for_use,
        "allergens": sku.allergens,
        "sds_document_url": sku.sds_document_url,
        "coa_document_url": sku.coa_document_url,
        "label_image_url": sku.label_image_url,
        "primary_contact_email": sku.primary_contact_email,
        "expiration_date": sku.expiration_date,
        "lot_number": sku.lot_number,
    }

    ingredients_list = [
        {
            "name": ing.name,
            "amount": ing.amount,
            "source": ing.source,
        }
        for ing in sku.ingredients_list
    ] if sku.ingredients_list else []

    # Run validation
    warnings = validator.validate_sku(sku_dict, ingredients_list)
    summary = validator.get_validation_summary(warnings)
    warning_schemas = [ValidationWarningSchema(**w.to_dict()) for w in warnings]

    return ValidationResult(
        **summary,
        warnings=warning_schemas
    )


@router.get("/validation/banned-substances", tags=["validation"])
async def get_banned_substances_info():
    """
    Get information about banned substances categories.

    Returns the complete list of banned substance categories and
    examples for NSF Certified for Sport compliance.
    """
    return {
        "metadata": validator.banned_substances.get("metadata", {}),
        "categories": {
            key: {
                "name": value.get("name"),
                "description": value.get("description"),
                "example_keywords": value.get("keywords", [])[:10]  # First 10 examples
            }
            for key, value in validator.banned_substances.get("categories", {}).items()
        },
        "high_risk_ingredients": {
            "description": validator.banned_substances.get("high_risk_ingredients", {}).get("description"),
            "examples": validator.banned_substances.get("high_risk_ingredients", {}).get("keywords", [])[:15]
        },
        "total_keywords_tracked": len(validator.banned_keywords),
        "note": "This list is based on WADA Prohibited List and NSF Certified for Sport requirements (290+ substances)"
    }


# BULK UPLOAD ENDPOINTS

@router.post("/bulk/bom/parse", tags=["bulk-upload"])
async def parse_bom_file_preview(
    file: UploadFile = File(...),
):
    """
    Parse a BOM file (CSV or Excel) and preview the data without saving.

    Supports: .csv, .xlsx, .xls

    Returns the parsed BOM data with SKU mappings for review, plus diagnostic info.
    """
    filename = file.filename.lower()
    if not filename.endswith(('.csv', '.xlsx', '.xls')):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only CSV and Excel files (.csv, .xlsx, .xls) are supported for BOM upload"
        )

    try:
        result = await BulkUploadService.parse_bom_file(file)

        # Add success message
        if result['errors']:
            message = f"Parsed {result['total_rows']} BOM entries with {len(result['errors'])} warnings"
        elif result['total_rows'] > 0:
            message = f"Successfully parsed {result['total_rows']} BOM entries"
        else:
            message = "No BOM entries found - please check your file format"

        return {
            "total_rows": result['total_rows'],
            "data": result['data'],
            "columns_found": result['columns_found'],
            "errors": result['errors'],
            "message": message
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error parsing BOM file: {str(e)}"
        )


@router.post("/ingredients/parse", tags=["ingredients"])
async def parse_ingredient_formulation(
    file: UploadFile = File(...),
):
    """
    Parse an ingredient formulation file (CSV or Excel) for a single SKU.

    Supports: .csv, .xlsx, .xls

    Expected columns:
    - Ingredient Name/Name/Ingredient
    - Unit/UOM
    - Amount/Quantity

    Returns parsed ingredients with formula validation (sum should equal 1.0).
    """
    filename = file.filename.lower()
    if not filename.endswith(('.csv', '.xlsx', '.xls')):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only CSV and Excel files (.csv, .xlsx, .xls) are supported"
        )

    try:
        import csv
        import io
        try:
            import openpyxl
            OPENPYXL_AVAILABLE = True
        except ImportError:
            OPENPYXL_AVAILABLE = False

        content = await file.read()
        ingredients = []
        columns_found = []
        errors = []

        # Parse file based on type
        if filename.endswith(('.xlsx', '.xls')):
            if not OPENPYXL_AVAILABLE:
                return {
                    'total_ingredients': 0,
                    'ingredients': [],
                    'columns_found': [],
                    'errors': ['Excel file support requires openpyxl. Please convert to CSV or install openpyxl.'],
                    'formula_sum': 0,
                    'formula_valid': False
                }

            # Parse Excel file
            workbook = openpyxl.load_workbook(io.BytesIO(content), read_only=True, data_only=True)
            sheet = workbook.active

            # Get headers from first row
            headers = []
            for cell in sheet[1]:
                headers.append(str(cell.value) if cell.value else '')
            columns_found = [h for h in headers if h]

            # Parse data rows
            for row_idx, row in enumerate(sheet.iter_rows(min_row=2, values_only=True), start=2):
                if not any(row):  # Skip empty rows
                    continue

                row_dict = {}
                for idx, value in enumerate(row):
                    if idx < len(headers) and headers[idx]:
                        row_dict[headers[idx]] = str(value) if value is not None else ''

                _process_ingredient_row(row_dict, ingredients, errors, row_idx)

        else:
            # Parse CSV file
            try:
                decoded = content.decode('utf-8-sig')
            except UnicodeDecodeError:
                try:
                    decoded = content.decode('latin-1')
                except UnicodeDecodeError:
                    decoded = content.decode('utf-8', errors='ignore')

            csv_reader = csv.DictReader(io.StringIO(decoded))
            columns_found = list(csv_reader.fieldnames) if csv_reader.fieldnames else []

            for row_idx, row in enumerate(csv_reader, start=2):
                if not any(row.values()):  # Skip empty rows
                    continue
                _process_ingredient_row(row, ingredients, errors, row_idx)

        # Calculate formula sum
        formula_sum = 0.0
        for ing in ingredients:
            if ing.get('amount'):
                try:
                    amount_val = float(ing['amount'])
                    formula_sum += amount_val
                except (ValueError, TypeError):
                    pass

        # Check if formula is valid (sum equals 1.0 with tolerance)
        formula_valid = abs(formula_sum - 1.0) < 0.0001  # Tolerance for floating point

        if not ingredients and not errors:
            errors.append(
                f"No ingredients found. Columns detected: {', '.join(columns_found) if columns_found else 'None'}. "
                f"Please ensure your file has columns for Ingredient Name, Unit, and Amount."
            )

        return {
            'total_ingredients': len(ingredients),
            'ingredients': ingredients,
            'columns_found': columns_found,
            'errors': errors,
            'formula_sum': formula_sum,
            'formula_valid': formula_valid
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error parsing ingredient file: {str(e)}"
        )


def _find_column(row: Dict, possible_names: List[str]) -> Optional[str]:
    """Find a column value by trying multiple possible names (case-insensitive)."""
    for name in possible_names:
        # Try exact match first
        if name in row and row[name]:
            return row[name]
        # Try case-insensitive match
        for key in row.keys():
            if key.lower() == name.lower() and row[key]:
                return row[key]
    return None


def _process_ingredient_row(row: Dict, ingredients: List, errors: List, row_num: int):
    """Process a single ingredient row and add to ingredients list if valid."""
    # Try to extract ingredient name
    ingredient_name = _find_column(row, [
        'Ingredient', 'ingredient', 'Name', 'name', 'Ingredient Name',
        'ingredient_name', 'IngredientName', 'Item', 'item',
        'Component', 'component', 'Material', 'material', 'Description'
    ])

    # Try to extract amount
    amount = _find_column(row, [
        'Amount', 'amount', 'Quantity', 'quantity', 'Qty', 'qty',
        'Weight', 'weight', 'Value', 'value', 'QTY', 'QUANTITY'
    ])

    # Try to extract unit
    unit = _find_column(row, [
        'Unit', 'unit', 'UOM', 'uom', 'Units', 'units',
        'Unit of measurement', 'Unit_of_measurement', 'Measurement Unit'
    ])

    if ingredient_name:
        # Optional: source/form
        source = _find_column(row, [
            'Source', 'source', 'Form', 'form', 'Type', 'type',
            'Specification', 'specification', 'Grade', 'grade'
        ])

        # Optional: CAS number
        cas_number = _find_column(row, [
            'CAS', 'cas', 'CAS Number', 'CAS_Number', 'cas_number', 'CAS#'
        ])

        ingredients.append({
            'name': ingredient_name.strip(),
            'amount': amount.strip() if amount else '',
            'unit': unit.strip() if unit else '',
            'source': source.strip() if source else '',
            'cas_number': cas_number.strip() if cas_number else ''
        })
    elif any(row.values()):  # Row has data but missing ingredient name
        errors.append(f"Row {row_num}: Missing ingredient name")


@router.post("/bulk/bom/upload", tags=["bulk-upload"])
async def bulk_upload_bom_files(
    files: List[UploadFile] = File(...),
    sku_mappings: str = Form(...),
    db: AsyncSession = Depends(get_db)
):
    """
    Bulk upload BOM files and associate them with SKUs.

    sku_mappings should be a JSON string: {"filename1.csv": "SKU001", "filename2.csv": "SKU002"}
    """
    try:
        mappings = json.loads(sku_mappings)
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid sku_mappings JSON format"
        )

    # Upload files
    results = await BulkUploadService.bulk_upload_boms(files, mappings)

    # Update SKU records with file paths and ingredients
    for result in results:
        if result['status'] == 'success':
            sku_code = result['sku_code']
            filepath = result['filepath']

            # Find SKU in database
            db_result = await db.execute(select(SKU).where(SKU.sku_code == sku_code))
            sku = db_result.scalar_one_or_none()

            if sku:
                # Update BOM file path
                sku.bom_file_path = filepath

                # Add ingredients from BOM
                for ing_data in result.get('ingredients', []):
                    if ing_data['sku_code'] == sku_code:
                        ingredient = Ingredient(
                            sku_id=sku.id,
                            name=ing_data['ingredient_name'],
                            amount=ing_data.get('amount'),
                            source=ing_data.get('source'),
                            unit=ing_data.get('unit'),
                            cas_number=ing_data.get('cas_number')
                        )
                        db.add(ingredient)

                await db.commit()
                result['sku_id'] = sku.id
                result['db_updated'] = True
            else:
                result['db_updated'] = False
                result['warning'] = f"SKU code '{sku_code}' not found in database"

    return {
        "total_files": len(files),
        "results": results
    }


@router.post("/bulk/artwork/match", tags=["bulk-upload"])
async def auto_match_artwork_files(
    files: List[UploadFile] = File(...),
    db: AsyncSession = Depends(get_db)
):
    """
    Auto-match artwork files to SKUs based on filename patterns.

    Returns suggested matches for user approval.
    """
    # Get all SKU codes from database
    result = await db.execute(select(SKU.sku_code))
    available_skus = [row[0] for row in result.all()]

    # Auto-match files
    matches = BulkUploadService.match_files_to_skus(files, available_skus)

    return {
        "total_files": len(files),
        "matches": [
            {
                "filename": m['filename'],
                "suggested_sku": m['suggested_sku'],
                "confidence": m['confidence']
            }
            for m in matches
        ],
        "message": "Review the matches and confirm to proceed with upload"
    }


@router.post("/bulk/artwork/upload", tags=["bulk-upload"])
async def bulk_upload_artwork_files(
    files: List[UploadFile] = File(...),
    sku_mappings: str = Form(...),
    db: AsyncSession = Depends(get_db)
):
    """
    Bulk upload artwork files and associate them with SKUs.

    sku_mappings should be a JSON string: {"filename1.jpg": "SKU001", "filename2.png": "SKU002"}
    """
    try:
        mappings = json.loads(sku_mappings)
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid sku_mappings JSON format"
        )

    # Upload files
    results = await BulkUploadService.bulk_upload_artworks(files, mappings)

    # Update SKU records with file paths
    for result in results:
        if result['status'] == 'success':
            sku_code = result['sku_code']
            filepath = result['filepath']

            # Find SKU in database
            db_result = await db.execute(select(SKU).where(SKU.sku_code == sku_code))
            sku = db_result.scalar_one_or_none()

            if sku:
                # Update artwork file path
                sku.artwork_file_path = filepath
                await db.commit()
                result['sku_id'] = sku.id
                result['db_updated'] = True
            else:
                result['db_updated'] = False
                result['warning'] = f"SKU code '{sku_code}' not found in database"

    return {
        "total_files": len(files),
        "results": results
    }
