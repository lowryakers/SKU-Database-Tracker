# NSF Compliance Validation Guide

## Overview

The SKU Database Tracker now includes **automatic validation** for NSF compliance and banned substances. Every time you create or update a product, the system automatically checks for:

✅ **290+ Banned Substances** (NSF Certified for Sport)
✅ **NSF Certification Requirements** (required fields and data)
✅ **Data Quality** (completeness, expiration dates)
✅ **High-Risk Patterns** (flagged ingredients and product names)

---

## How It Works

### Automatic Validation

**When Creating/Updating Products**, validation happens automatically:

1. **Ingredient Screening** - Each ingredient is checked against the banned substances database
2. **Pattern Matching** - Product names and descriptions are scanned for high-risk terms
3. **Requirements Check** - NSF-required fields are verified
4. **Compliance Report** - Results returned with severity levels and suggestions

### Validation Results

Every validation returns:
- **Status**: `passed`, `warning`, or `failed`
- **NSF Ready**: Boolean indicating if product can proceed to certification
- **Warnings Count**: By severity (critical, warning, info)
- **Detailed List**: Each issue with field, message, and suggestion

---

## Banned Substances Database

### Coverage (290+ Substances)

Based on the **WADA Prohibited List** and **NSF Certified for Sport** requirements:

#### Major Categories

1. **Anabolic Agents** (Steroids & SARMs)
   - testosterone, nandrolone, stanozolol, trenbolone
   - SARMs: ostarine, ligandrol, RAD140, andarine
   - Prohormones: DHEA, androstenedione

2. **Peptide Hormones** (EPO, HGH, Growth Factors)
   - erythropoietin (EPO), human growth hormone (HGH)
   - IGF-1, mechano growth factor
   - Growth hormone releasing agents: GHRP, MK-677, CJC-1295

3. **Beta-2 Agonists**
   - clenbuterol, salbutamol, formoterol
   - higenamine, methylsynephrine

4. **Hormone Modulators**
   - Aromatase inhibitors: anastrozole, letrozole, exemestane
   - SERMs: clomiphene, tamoxifen, raloxifene

5. **Diuretics & Masking Agents**
   - furosemide, hydrochlorothiazide
   - probenecid, epitestosterone

6. **Stimulants**
   - DMAA, DMBA, octodrine, amp citrate
   - ephedrine, pseudoephedrine, synephrine
   - methylhexanamine, phenylethylamine

7. **Narcotics**
   - morphine, codeine, fentanyl
   - oxycodone, hydrocodone

8. **Cannabinoids**
   - THC, cannabis, synthetic cannabinoids
   - CBD (flagged for verification)

9. **Glucocorticoids**
   - prednisone, dexamethasone, triamcinolone

10. **Gene & Blood Doping**
    - Gene therapy, gene editing, blood manipulation

#### High-Risk Ingredients

Common supplement ingredients that may be contaminated:
- yohimbe, rauwolscine, deer antler velvet
- tribulus terrestris, horny goat weed
- mucuna pruriens, wild yam extract
- turkesterone, ecdysterone, laxogenin

#### Warning Patterns

Product names/descriptions flagged for review:
- "proprietary blend", "anabolic", "testosterone booster"
- "muscle builder", "fat burner extreme"
- "hardcore", "pro-hormone", "designer supplement"

---

## API Endpoints

### 1. Validate Without Creating

Test product data before creating:

```bash
POST /api/v1/skus/validate
```

**Request:**
```json
{
  "sku_data": {
    "sku_code": "TEST-001",
    "name": "Protein Powder",
    "requires_nsf_certification": true,
    "nsf_certification_type": "NSF Certified for Sport"
  },
  "ingredients": [
    {
      "name": "Whey Protein Isolate",
      "amount": "25g"
    },
    {
      "name": "DMAA",
      "amount": "50mg"
    }
  ]
}
```

**Response:**
```json
{
  "status": "failed",
  "total_warnings": 2,
  "critical_count": 1,
  "warning_count": 1,
  "info_count": 0,
  "nsf_ready": false,
  "has_banned_substances": true,
  "message": "CRITICAL ISSUES DETECTED! Product is NOT ready for NSF certification.",
  "warnings": [
    {
      "severity": "critical",
      "category": "banned_substance",
      "message": "Ingredient 'DMAA' matches banned substance categories: Stimulants",
      "field": "ingredients",
      "suggestion": "Remove this ingredient or verify it's not a banned substance. Contact NSF for clarification."
    },
    {
      "severity": "warning",
      "category": "nsf_requirement",
      "message": "Missing required NSF fields: Brand Name, Product Type, Net Content...",
      "field": "multiple",
      "suggestion": "Complete all required fields for NSF certification application."
    }
  ]
}
```

### 2. Create with Validation

Create SKU and get validation results:

```bash
POST /api/v1/skus/with-validation
```

Returns the created SKU plus full validation results.

### 3. Validate Existing SKU

Check compliance of products already in database:

```bash
GET /api/v1/skus/{sku_id}/validate
```

Useful for:
- Periodic compliance audits
- Re-checking after ingredient changes
- Before NSF submission

### 4. View Banned Substances

Get information about banned substances:

```bash
GET /api/v1/validation/banned-substances
```

Returns categories, examples, and total keywords tracked.

---

## Warning Severity Levels

### 🔴 CRITICAL
- **Banned substances detected** in ingredients
- **Major compliance issues** (e.g., expired certification)
- **Product is NOT NSF-ready**

**Action Required:** Remove banned ingredient or reformulate product

### 🟡 WARNING
- **Missing required NSF fields**
- **Incomplete ingredient data**
- **Approaching expiration dates**
- **Product needs attention before NSF submission**

**Action Required:** Complete missing information

### 🔵 INFO
- **Suggestions for data quality**
- **Missing optional fields**
- **Product can proceed to certification**

**Action Recommended:** Improve data for better documentation

---

## NSF Requirements Validated

### Product Information
- ✅ SKU Code
- ✅ Product Name
- ✅ Brand Name
- ✅ Product Type
- ✅ Net Content
- ✅ Serving Size
- ✅ Servings per Container

### Manufacturing
- ✅ Manufacturer Name
- ✅ Manufacturing Facility
- ✅ Facility Address (City, State, Country)
- ✅ Facility ID (if applicable)

### Formulation
- ✅ Complete Ingredient List
- ✅ Ingredient Amounts
- ✅ Ingredient Sources
- ✅ Allergen Information

### Label & Claims
- ✅ Label Claims
- ✅ Intended Use
- ✅ Directions for Use
- ✅ Warnings

### Documentation
- ✅ Safety Data Sheet (SDS)
- ✅ Certificate of Analysis (COA)
- ✅ Product Label Image

### Certification Tracking
- ✅ NSF Certification Type
- ✅ Certification Status
- ✅ Certification Number & Dates
- ✅ Expiration Date
- ✅ Next Audit Date
- ✅ Banned Substances Testing Status

---

## Web Interface

### Validation Guide Page

Access at: **http://localhost:8000/validation**

Features:
- Complete guide to validation system
- Banned substances categories overview
- Warning levels explanation
- Links to API documentation
- NSF resources

### Integration Points

Validation can be triggered from:
1. **API Documentation** (`/docs`) - Interactive testing
2. **Validation Guide** (`/validation`) - Educational resource
3. **Direct API Calls** - Programmatic validation

---

## Example Use Cases

### Before NSF Submission

```bash
# Validate specific product
GET /api/v1/skus/123/validate

# Check if NSF ready
{
  "nsf_ready": true,
  "has_banned_substances": false,
  "status": "passed"
}
```

### After Ingredient Change

```bash
# Re-validate product
POST /api/v1/skus/validate
# Include updated ingredient list
# Check for new banned substances
```

### Periodic Compliance Audit

```bash
# Validate all NSF products
GET /api/v1/skus?requires_nsf=true
# Then validate each:
GET /api/v1/skus/{id}/validate
```

### Partner Collaboration

Before sharing data:
1. Validate all products
2. Fix any critical issues
3. Export validated data
4. Share with confidence

---

## Best Practices

### 1. Validate Early
- Check products before adding to database
- Use `/validate` endpoint to test formulations
- Catch issues before production

### 2. Regular Audits
- Validate existing products monthly
- Check for expired certifications
- Update banned substances list

### 3. Document Everything
- Complete all NSF-required fields
- Add ingredient sources
- Upload documentation (SDS, COA)

### 4. Monitor Warnings
- Address critical issues immediately
- Plan to fix warnings before submission
- Use suggestions to improve data quality

### 5. Stay Updated
- Banned substances list updated regularly
- Check NSF website for new requirements
- Re-validate products after list updates

---

## Troubleshooting

### "Banned Substance Detected"

**Problem:** Ingredient flagged as banned

**Solutions:**
1. Verify ingredient is actually banned (check NSF)
2. Remove ingredient and reformulate
3. Find alternative ingredient
4. If false positive, document and contact NSF

### "Missing Required Fields"

**Problem:** NSF requirements not met

**Solutions:**
1. Review validation warnings
2. Complete missing fields
3. Re-validate until all fields present
4. Check NSF documentation for specifics

### "Product Not NSF Ready"

**Problem:** Multiple compliance issues

**Solutions:**
1. Review all validation warnings
2. Fix critical issues first
3. Address warnings next
4. Improve info items for quality
5. Re-validate after each fix

---

## Support Resources

### NSF International
- **NSF Certified for Sport**: https://www.nsfsport.com/
- **Certification Portal**: https://www.nsf.org/certified-products-systems
- **Product Listings**: https://listings.nsf.org/

### Application Resources
- **API Documentation**: http://localhost:8000/docs
- **Validation Guide**: http://localhost:8000/validation
- **Banned Substances List**: http://localhost:8000/api/v1/validation/banned-substances

---

## Summary

The validation system provides **automatic, comprehensive checking** for:
- ✅ All 290+ banned substances
- ✅ Complete NSF requirements
- ✅ Data quality and completeness
- ✅ Certification status and expiration

**Every product is validated automatically** to ensure NSF compliance before submission!
