"""Validation service for NSF compliance and banned substances checking."""

import json
import os
from typing import List, Dict, Any, Tuple
from datetime import date, datetime, timedelta


class ValidationWarning:
    """Represents a validation warning."""

    def __init__(self, severity: str, category: str, message: str, field: str = None, suggestion: str = None):
        self.severity = severity  # 'critical', 'warning', 'info'
        self.category = category  # 'banned_substance', 'nsf_requirement', 'data_quality'
        self.message = message
        self.field = field
        self.suggestion = suggestion

    def to_dict(self) -> Dict[str, Any]:
        """Convert warning to dictionary."""
        return {
            "severity": self.severity,
            "category": self.category,
            "message": self.message,
            "field": self.field,
            "suggestion": self.suggestion
        }


class NSFValidator:
    """Validator for NSF compliance and banned substances."""

    def __init__(self):
        """Initialize validator with banned substances database."""
        self.banned_substances = self._load_banned_substances()
        self.banned_keywords = self._extract_all_keywords()

    def _load_banned_substances(self) -> Dict[str, Any]:
        """Load banned substances from JSON file."""
        file_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "data",
            "banned_substances.json"
        )
        try:
            with open(file_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            # Return minimal structure if file not found
            return {
                "categories": {},
                "high_risk_ingredients": {"keywords": []},
                "warning_patterns": []
            }

    def _extract_all_keywords(self) -> List[str]:
        """Extract all banned substance keywords into a flat list."""
        keywords = []
        for category_data in self.banned_substances.get("categories", {}).values():
            keywords.extend(category_data.get("keywords", []))
        keywords.extend(self.banned_substances.get("high_risk_ingredients", {}).get("keywords", []))
        return [k.lower() for k in keywords]

    def check_ingredient_name(self, ingredient_name: str) -> Tuple[bool, List[str]]:
        """
        Check if an ingredient name matches any banned substances.

        Returns:
            Tuple of (is_banned, list_of_matching_categories)
        """
        if not ingredient_name:
            return False, []

        ingredient_lower = ingredient_name.lower().strip()
        matching_categories = []

        # Check against all categories
        for category_key, category_data in self.banned_substances.get("categories", {}).items():
            for keyword in category_data.get("keywords", []):
                if keyword.lower() in ingredient_lower or ingredient_lower in keyword.lower():
                    matching_categories.append(category_data.get("name", category_key))
                    break

        # Check high-risk ingredients
        for keyword in self.banned_substances.get("high_risk_ingredients", {}).get("keywords", []):
            if keyword.lower() in ingredient_lower or ingredient_lower in keyword.lower():
                if "High-Risk Ingredients" not in matching_categories:
                    matching_categories.append("High-Risk Ingredients (may contain banned substances)")
                break

        return len(matching_categories) > 0, matching_categories

    def check_product_name_patterns(self, product_name: str, description: str = None) -> List[str]:
        """
        Check product name and description for warning patterns.

        Returns:
            List of matched warning patterns
        """
        matched_patterns = []
        text_to_check = (product_name or "").lower()
        if description:
            text_to_check += " " + description.lower()

        for pattern in self.banned_substances.get("warning_patterns", []):
            if pattern.lower() in text_to_check:
                matched_patterns.append(pattern)

        return matched_patterns

    def validate_sku(self, sku_data: Dict[str, Any], ingredients: List[Dict[str, Any]] = None) -> List[ValidationWarning]:
        """
        Comprehensive validation of SKU data for NSF compliance.

        Args:
            sku_data: SKU data dictionary
            ingredients: List of ingredient dictionaries

        Returns:
            List of ValidationWarning objects
        """
        warnings = []

        # Check if product requires NSF certification
        requires_nsf = sku_data.get("requires_nsf_certification", False)
        nsf_cert_type = sku_data.get("nsf_certification_type")

        # 1. BANNED SUBSTANCES CHECK
        if ingredients:
            for ing in ingredients:
                ing_name = ing.get("name", "")
                is_banned, categories = self.check_ingredient_name(ing_name)

                if is_banned:
                    warnings.append(ValidationWarning(
                        severity="critical",
                        category="banned_substance",
                        message=f"Ingredient '{ing_name}' matches banned substance categories: {', '.join(categories)}",
                        field="ingredients",
                        suggestion="Remove this ingredient or verify it's not a banned substance. Contact NSF for clarification."
                    ))

        # 2. PRODUCT NAME/DESCRIPTION PATTERNS
        warning_patterns = self.check_product_name_patterns(
            sku_data.get("name", ""),
            sku_data.get("description", "")
        )

        if warning_patterns:
            warnings.append(ValidationWarning(
                severity="warning",
                category="product_claims",
                message=f"Product name/description contains high-risk terms: {', '.join(warning_patterns)}",
                field="name",
                suggestion="Products with these terms often contain banned substances. Ensure all ingredients are compliant."
            ))

        # 3. NSF CERTIFICATION REQUIREMENTS
        if requires_nsf or nsf_cert_type:
            nsf_warnings = self._validate_nsf_requirements(sku_data, ingredients)
            warnings.extend(nsf_warnings)

        # 4. DATA QUALITY CHECKS
        quality_warnings = self._validate_data_quality(sku_data)
        warnings.extend(quality_warnings)

        return warnings

    def _validate_nsf_requirements(self, sku_data: Dict[str, Any], ingredients: List[Dict[str, Any]] = None) -> List[ValidationWarning]:
        """Validate NSF-specific requirements."""
        warnings = []
        nsf_cert_type = sku_data.get("nsf_certification_type", "")

        # Required fields for NSF certification
        required_fields = {
            "basic_info": {
                "sku_code": "SKU Code",
                "name": "Product Name",
                "brand_name": "Brand Name",
                "product_type": "Product Type"
            },
            "formulation": {
                "net_content": "Net Content",
                "serving_size": "Serving Size",
                "servings_per_container": "Servings per Container"
            },
            "manufacturing": {
                "manufacturer_name": "Manufacturer Name",
                "manufacturer_facility": "Manufacturing Facility",
                "manufacturer_city": "City",
                "manufacturer_state": "State/Province",
                "manufacturer_country": "Country"
            },
            "label": {
                "label_claims": "Label Claims",
                "intended_use": "Intended Use",
                "directions_for_use": "Directions for Use"
            },
            "contact": {
                "primary_contact_email": "Primary Contact Email"
            }
        }

        # Check required fields
        missing_fields = []
        for section, fields in required_fields.items():
            for field_key, field_name in fields.items():
                if not sku_data.get(field_key):
                    missing_fields.append(field_name)

        if missing_fields:
            warnings.append(ValidationWarning(
                severity="warning",
                category="nsf_requirement",
                message=f"Missing required NSF fields: {', '.join(missing_fields[:5])}{'...' if len(missing_fields) > 5 else ''}",
                field="multiple",
                suggestion="Complete all required fields for NSF certification application."
            ))

        # Check ingredients
        if not ingredients or len(ingredients) == 0:
            warnings.append(ValidationWarning(
                severity="critical",
                category="nsf_requirement",
                message="No ingredients listed. NSF requires complete ingredient disclosure.",
                field="ingredients",
                suggestion="Add all product ingredients with amounts and sources."
            ))
        else:
            # Check ingredient completeness
            incomplete_ingredients = []
            for ing in ingredients:
                if not ing.get("amount") or not ing.get("source"):
                    incomplete_ingredients.append(ing.get("name", "Unknown"))

            if incomplete_ingredients:
                warnings.append(ValidationWarning(
                    severity="warning",
                    category="nsf_requirement",
                    message=f"Incomplete ingredient data for: {', '.join(incomplete_ingredients[:3])}",
                    field="ingredients",
                    suggestion="NSF requires ingredient amounts and sources for all ingredients."
                ))

        # NSF Certified for Sport specific checks
        if "sport" in nsf_cert_type.lower():
            if not sku_data.get("nsf_banned_substances_tested"):
                warnings.append(ValidationWarning(
                    severity="warning",
                    category="nsf_requirement",
                    message="NSF Certified for Sport requires testing for 290+ banned substances.",
                    field="nsf_banned_substances_tested",
                    suggestion="Ensure product has been tested for banned substances before certification."
                ))

        # Check documentation
        missing_docs = []
        if not sku_data.get("sds_document_url"):
            missing_docs.append("Safety Data Sheet (SDS)")
        if not sku_data.get("coa_document_url"):
            missing_docs.append("Certificate of Analysis (COA)")
        if not sku_data.get("label_image_url"):
            missing_docs.append("Product Label Image")

        if missing_docs:
            warnings.append(ValidationWarning(
                severity="info",
                category="nsf_requirement",
                message=f"Missing documentation: {', '.join(missing_docs)}",
                field="documentation",
                suggestion="NSF may require these documents during the certification process."
            ))

        # Check certification dates
        if sku_data.get("nsf_certification_status") == "Certified":
            exp_date = sku_data.get("nsf_expiration_date")
            if exp_date:
                if isinstance(exp_date, str):
                    exp_date = datetime.strptime(exp_date, "%Y-%m-%d").date()

                days_until_expiration = (exp_date - date.today()).days

                if days_until_expiration < 0:
                    warnings.append(ValidationWarning(
                        severity="critical",
                        category="nsf_requirement",
                        message="NSF certification has EXPIRED!",
                        field="nsf_expiration_date",
                        suggestion="Renew certification immediately. Product cannot be marketed as NSF certified."
                    ))
                elif days_until_expiration < 90:
                    warnings.append(ValidationWarning(
                        severity="warning",
                        category="nsf_requirement",
                        message=f"NSF certification expires in {days_until_expiration} days.",
                        field="nsf_expiration_date",
                        suggestion="Begin renewal process now to avoid lapse in certification."
                    ))

        return warnings

    def _validate_data_quality(self, sku_data: Dict[str, Any]) -> List[ValidationWarning]:
        """Validate data quality and completeness."""
        warnings = []

        # Check for very short or missing descriptions
        description = sku_data.get("description", "")
        if not description or len(description) < 20:
            warnings.append(ValidationWarning(
                severity="info",
                category="data_quality",
                message="Product description is missing or very short.",
                field="description",
                suggestion="Add a detailed product description for better documentation."
            ))

        # Check allergen information
        if not sku_data.get("allergens"):
            warnings.append(ValidationWarning(
                severity="info",
                category="data_quality",
                message="No allergen information provided.",
                field="allergens",
                suggestion="Specify allergen information or state 'None' if not applicable."
            ))

        # Check batch/lot tracking
        if not sku_data.get("lot_number") and not sku_data.get("batch_number"):
            warnings.append(ValidationWarning(
                severity="info",
                category="data_quality",
                message="No lot or batch number specified.",
                field="lot_number",
                suggestion="Lot/batch tracking is important for quality control and NSF audits."
            ))

        # Check expiration date
        exp_date = sku_data.get("expiration_date")
        if exp_date:
            if isinstance(exp_date, str):
                exp_date = datetime.strptime(exp_date, "%Y-%m-%d").date()

            if exp_date < date.today():
                warnings.append(ValidationWarning(
                    severity="warning",
                    category="data_quality",
                    message="Product has passed its expiration date.",
                    field="expiration_date",
                    suggestion="Update inventory status or remove expired product."
                ))

        return warnings

    def get_validation_summary(self, warnings: List[ValidationWarning]) -> Dict[str, Any]:
        """
        Generate a summary of validation results.

        Returns:
            Dictionary with validation summary
        """
        if not warnings:
            return {
                "status": "passed",
                "total_warnings": 0,
                "critical_count": 0,
                "warning_count": 0,
                "info_count": 0,
                "nsf_ready": True,
                "message": "All validation checks passed! Product is ready for NSF certification."
            }

        critical = sum(1 for w in warnings if w.severity == "critical")
        warning = sum(1 for w in warnings if w.severity == "warning")
        info = sum(1 for w in warnings if w.severity == "info")

        # Check if any banned substances detected
        has_banned = any(w.category == "banned_substance" for w in warnings)

        if has_banned or critical > 0:
            status = "failed"
            nsf_ready = False
            message = "CRITICAL ISSUES DETECTED! Product is NOT ready for NSF certification."
        elif warning > 0:
            status = "warning"
            nsf_ready = False
            message = "Warnings detected. Address these issues before NSF submission."
        else:
            status = "passed"
            nsf_ready = True
            message = "Minor suggestions only. Product can proceed to NSF certification."

        return {
            "status": status,
            "total_warnings": len(warnings),
            "critical_count": critical,
            "warning_count": warning,
            "info_count": info,
            "nsf_ready": nsf_ready,
            "has_banned_substances": has_banned,
            "message": message
        }
