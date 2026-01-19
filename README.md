# SKU Database Tracker - NSF Certification Management System

A comprehensive, web-based inventory management system designed for tracking Stock Keeping Units (SKUs) with full support for NSF certification requirements. Built with Python, FastAPI, and SQLite - perfect for brands seeking NSF Certified for Sport or other NSF certifications.

## 🚀 Quick Start

**Want to deploy with a public URL?** → See [DEPLOYMENT.md](DEPLOYMENT.md) for step-by-step instructions to deploy to Railway, Render, or Fly.io (5 minutes to get a public URL!)

**Running locally?** → Jump to [Quick Start](#quick-start) section below

## Features

### Core Functionality
- **Complete SKU Management**: Track all product information including formulations, ingredients, manufacturing details
- **NSF Certification Support**: Full support for NSF Certified for Sport, NSF/ANSI 173, NSF 229, NSF 527, and other certifications
- **User-Friendly Web Interface**: Designed for non-technical users to easily manage product data
- **Powerful REST API**: Full programmatic access for integrations and automation
- **Multi-Format Export**: Generate Excel, PDF, and CSV exports for NSF submissions and partner sharing
- **Ingredient Management**: Detailed ingredient tracking with amounts, sources, and allergen information
- **Batch/Lot Tracking**: Manufacturing dates, lot numbers, and expiration tracking
- **Documentation Management**: Links to SDS, COA, label images, and other required documents

### NSF Certification Features

#### Supported Certification Types
- **NSF Certified for Sport**: For dietary supplements and sports nutrition products (290+ banned substances testing)
- **NSF/ANSI 173**: Dietary supplement certification
- **NSF 229**: Dietary supplement ingredient certification
- **NSF 527**: Vitamin and mineral supplement certification
- **NSF 372**: Drinking water system components
- **Custom certification types**: Support for any NSF certification program

#### Certification Tracking
- Certification status tracking (Not Started, In Progress, Certified, Expired, Pending Renewal)
- Certification numbers and dates
- Expiration and renewal tracking
- Next audit date reminders
- Test results documentation
- Banned substances testing status

#### NSF-Required Data Fields
- Complete product formulation with ingredient details
- Manufacturing facility information (name, address, facility ID)
- Supplier information and contacts
- Label claims and intended use
- Product specifications (serving size, net content, etc.)
- Quality control documentation
- Safety data sheets (SDS)
- Certificates of Analysis (COA)

### Export & Sharing

#### Export Formats
1. **Excel (.xlsx)**
   - Multiple sheets (SKU data + Ingredients)
   - Formatted headers and professional styling
   - Perfect for NSF submissions
   - Includes all certification fields

2. **PDF**
   - Professional certification reports
   - Formatted for sharing with partners and certifying bodies
   - Product details with ingredient breakdowns
   - Page breaks for easy printing

3. **CSV**
   - Simple format for data import/export
   - Compatible with spreadsheet applications
   - Useful for data migration

#### Export Features
- Filter by certification type
- Include/exclude ingredient details
- Include/exclude internal notes
- Selective SKU export
- Batch export capabilities

## Tech Stack

- **Backend Framework**: FastAPI 0.109+ (Modern Python async framework)
- **Database**: SQLite with SQLAlchemy 2.0+ (Async ORM)
- **Data Validation**: Pydantic 2.5+ (Type-safe data validation)
- **Web Server**: Uvicorn with standard extras
- **Export Libraries**: OpenPyXL (Excel), ReportLab (PDF), CSV (built-in)
- **Frontend**: Bootstrap 5, Font Awesome icons, vanilla JavaScript
- **Python Version**: 3.11+

## Project Structure

```
sku-database-tracker/
├── app/
│   ├── api/              # REST API routes
│   │   └── routes.py     # SKU CRUD, ingredients, export endpoints
│   ├── database/         # Database connection and configuration
│   │   └── connection.py
│   ├── models/           # SQLAlchemy database models
│   │   └── sku.py        # SKU and Ingredient models (50+ fields)
│   ├── schemas/          # Pydantic validation schemas
│   │   └── sku.py        # Request/response schemas
│   ├── services/         # Business logic services
│   │   └── export.py     # Excel, PDF, CSV export service
│   ├── web/              # Web interface routes
│   │   └── routes.py     # HTML page routes
│   ├── static/           # Static files (CSS, JS, images)
│   ├── templates/        # Jinja2 HTML templates
│   │   ├── base.html
│   │   ├── dashboard.html
│   │   ├── sku_list.html
│   │   ├── sku_form.html
│   │   ├── nsf_certification.html
│   │   └── export.html
│   ├── config.py         # Application configuration
│   └── main.py           # FastAPI application entry point
├── tests/                # Test files
├── data/                 # SQLite database storage (created at runtime)
├── .env.example          # Example environment variables
├── .gitignore            # Git ignore rules
├── pyproject.toml        # Modern Python project configuration
├── requirements.txt      # Production dependencies
└── requirements-dev.txt  # Development dependencies
```

## Quick Start

### Prerequisites

- Python 3.11 or higher
- pip (Python package manager)

### Installation

1. **Clone the repository:**
```bash
git clone <repository-url>
cd SKU-Database-Tracker
```

2. **Create a virtual environment:**
```bash
python -m venv venv

# On Windows
venv\Scripts\activate

# On macOS/Linux
source venv/bin/activate
```

3. **Install dependencies:**
```bash
pip install -r requirements.txt
```

4. **Create environment file:**
```bash
cp .env.example .env
# Edit .env and update SECRET_KEY for production
```

### Running the Application

Start the development server:
```bash
uvicorn app.main:app --reload
```

The application will be available at:
- **Web Interface**: http://localhost:8000 (User-friendly dashboard)
- **Interactive API docs (Swagger)**: http://localhost:8000/docs
- **Alternative API docs (ReDoc)**: http://localhost:8000/redoc
- **Health check**: http://localhost:8000/health

## User Guide

### For Non-Technical Users

#### 1. Accessing the Dashboard
- Open your web browser and go to http://localhost:8000
- You'll see the dashboard with statistics and quick actions

#### 2. Adding a New Product
- Click "Add New SKU" from the dashboard or sidebar
- Use the API documentation link to access the full form
- Fill in all required fields (marked with *)
- Include NSF certification details if applicable

#### 3. Managing Existing Products
- Click "All SKUs" to see your product list
- Use the "Edit" button to update product information
- Filter by category or NSF status

#### 4. NSF Certification Tracking
- Click "NSF Certification" in the sidebar
- View all products requiring certification
- Track certification status, expiration dates, and audit schedules
- Update certification information as needed

#### 5. Exporting Data
- Click "Export Data" from the sidebar
- Choose your export format (Excel, PDF, or CSV)
- Select filters (certification type, ingredients, etc.)
- Click "Generate Export" to download

### For Developers & Technical Users

#### API Endpoints

**SKU Management**
- `POST /api/v1/skus` - Create a new SKU
- `GET /api/v1/skus` - List all SKUs (with filters)
- `GET /api/v1/skus/{id}` - Get a specific SKU
- `PUT /api/v1/skus/{id}` - Update a SKU
- `DELETE /api/v1/skus/{id}` - Delete a SKU

**Ingredient Management**
- `POST /api/v1/skus/{sku_id}/ingredients` - Add ingredient to SKU
- `GET /api/v1/skus/{sku_id}/ingredients` - List SKU ingredients
- `DELETE /api/v1/ingredients/{id}` - Delete an ingredient

**Export Endpoints**
- `POST /api/v1/skus/export/excel` - Export to Excel
- `POST /api/v1/skus/export/pdf` - Export to PDF
- `POST /api/v1/skus/export/csv` - Export to CSV

**Statistics**
- `GET /api/v1/skus/stats/summary` - Get SKU statistics and NSF overview

#### Example: Create a Complete SKU with NSF Data

```bash
curl -X POST "http://localhost:8000/api/v1/skus" \
  -H "Content-Type: application/json" \
  -d '{
    "sku_code": "PROTEIN-001",
    "name": "Premium Whey Protein",
    "brand_name": "Elite Nutrition",
    "product_type": "Dietary Supplement",
    "category": "Sports Nutrition",
    "description": "High-quality whey protein isolate",
    "net_content": "2 lbs (907g)",
    "serving_size": "1 scoop (30g)",
    "servings_per_container": 30,
    "quantity": 500,
    "unit_price": 49.99,
    "manufacturer_name": "Elite Manufacturing Co",
    "manufacturer_facility": "Facility A",
    "manufacturer_city": "Austin",
    "manufacturer_state": "TX",
    "manufacturer_country": "USA",
    "nsf_certification_type": "NSF Certified for Sport",
    "nsf_certification_status": "In Progress",
    "requires_nsf_certification": true,
    "label_claims": "25g Protein per serving, BCAA enriched",
    "intended_use": "Muscle recovery and growth support",
    "primary_contact_email": "quality@elitenutrition.com",
    "is_active": true
  }'
```

#### Example: Export NSF Certified Products to Excel

```bash
curl -X POST "http://localhost:8000/api/v1/skus/export/excel" \
  -H "Content-Type: application/json" \
  -d '{
    "format": "excel",
    "certification_type": "NSF Certified for Sport",
    "include_ingredients": true,
    "include_internal_notes": false
  }' \
  --output nsf_products.xlsx
```

## NSF Certification Requirements

### What NSF Looks For

Based on NSF International requirements, this tool helps you track:

1. **Product Formulation**
   - Complete ingredient list with amounts
   - Source materials and suppliers
   - Active vs inactive ingredients
   - Allergen information

2. **Manufacturing Information**
   - Facility name, address, and ID
   - Manufacturing processes
   - Quality control procedures
   - Batch/lot tracking

3. **Label Information**
   - All label claims
   - Intended use statements
   - Directions for use
   - Warnings and precautions

4. **Testing Documentation**
   - Banned substances testing (290+ for Sport)
   - Certificate of Analysis (COA)
   - Safety Data Sheets (SDS)
   - Test result summaries

5. **Ongoing Compliance**
   - Certification expiration dates
   - Audit schedules
   - Annual re-testing
   - Formulation change notifications

### NSF Certified for Sport Specific

For products seeking NSF Certified for Sport certification:
- Testing for 290+ banned substances
- Must also comply with NSF/ANSI 173
- Annual re-testing required
- Facility audits
- Recognized by USADA, MLB, NHL, NFL, NBA, PGA, UFC, and more

## Development

### Install Development Dependencies

```bash
pip install -r requirements-dev.txt
```

### Code Quality Tools

**Black** - Code formatter:
```bash
black app/ tests/
```

**Ruff** - Fast Python linter:
```bash
ruff check app/ tests/
```

**MyPy** - Static type checker:
```bash
mypy app/
```

### Running Tests

```bash
pytest
```

With coverage:
```bash
pytest --cov=app --cov-report=html
```

## Dependency Analysis

### Production Dependencies (All Secure & Modern)

| Package | Version | Purpose | Notes |
|---------|---------|---------|-------|
| **fastapi** | >=0.109.0 | Web framework | Latest stable, regular security updates |
| **uvicorn[standard]** | >=0.27.0 | ASGI server | Production-ready |
| **sqlalchemy** | >=2.0.25 | ORM/Database | Latest 2.x with async support |
| **pydantic** | >=2.5.3 | Data validation | V2 with performance improvements |
| **pydantic-settings** | >=2.1.0 | Settings management | Secure config handling |
| **aiosqlite** | >=0.19.0 | Async SQLite | Enables async database operations |
| **jinja2** | >=3.1.3 | Template engine | For web interface |
| **openpyxl** | >=3.1.2 | Excel generation | NSF submission exports |
| **reportlab** | >=4.0.9 | PDF generation | Professional reports |
| **xlsxwriter** | >=3.1.9 | Excel writing | Advanced Excel features |
| **python-jose[cryptography]** | >=3.3.0 | JWT tokens | For authentication (future) |
| **passlib[bcrypt]** | >=1.7.4 | Password hashing | For authentication (future) |

✅ **No outdated packages** - All dependencies use recent stable versions
✅ **No known vulnerabilities** - Selected versions have no published CVEs
✅ **Minimal bloat** - Only essential packages included
✅ **Production ready** - All packages are battle-tested

## Security Considerations

1. **Change SECRET_KEY**: Update the secret key in `.env` for production
2. **Environment Variables**: Never commit `.env` files to version control
3. **Database Backups**: Regularly backup your SQLite database
4. **Input Validation**: All inputs are validated via Pydantic schemas
5. **SQL Injection**: Protected by SQLAlchemy ORM
6. **Sensitive Data**: Internal notes and pricing can be excluded from exports

## Deployment

### 🌐 Deploy to the Cloud

**Want a public URL accessible from anywhere?**

See **[DEPLOYMENT.md](DEPLOYMENT.md)** for complete step-by-step guides to deploy to:
- **Railway** (Recommended - 5 minute setup, free tier)
- **Render** (Free tier with auto-sleep)
- **Fly.io** (Global edge deployment)

Each guide includes:
- ✅ One-click deployment from GitHub
- ✅ Automatic HTTPS
- ✅ Custom domain setup
- ✅ Environment variable configuration
- ✅ Database options (SQLite → PostgreSQL)

### For Production

1. **Use PostgreSQL** instead of SQLite for better concurrent access
2. **Set up HTTPS** with proper SSL certificates (automatic with Railway/Render)
3. **Configure authentication** for user access control
4. **Enable CORS** carefully for API access
5. **Use environment variables** for all configuration
6. **Set up automated backups** of your database
7. **Monitor application logs** for errors and issues

### Scaling Options

- **Database**: Migrate to PostgreSQL or MySQL for production
- **Authentication**: Add JWT-based authentication for API access
- **File Storage**: Use cloud storage (S3, Azure Blob) for documents
- **Email**: Integrate email service for export delivery
- **API Rate Limiting**: Add rate limiting for public API endpoints

## Roadmap

- [x] Core SKU management
- [x] NSF certification field support
- [x] Web interface for non-technical users
- [x] Excel/PDF/CSV export
- [x] Ingredient management
- [x] NSF certification tracking
- [ ] User authentication and authorization
- [ ] Email sharing of exports
- [ ] Automated NSF compliance checks
- [ ] Low stock alerts
- [ ] Barcode scanning support
- [ ] Document upload and storage
- [ ] Audit trail for all changes
- [ ] Multi-tenant support
- [ ] API webhook notifications
- [ ] Advanced reporting and analytics

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Support & Resources

### NSF International Resources
- [NSF Certified for Sport](https://www.nsfsport.com/)
- [NSF Certification Portal](https://www.nsf.org/certified-products-systems)
- [NSF Product Listings](https://listings.nsf.org/)

### Application Support
- For issues or questions, please open an issue on the repository
- API documentation available at `/docs` when running the application
- Web interface help available in the Help modal

## License

MIT License - feel free to use this project for personal or commercial purposes.

## Acknowledgments

Built with insights from NSF International certification requirements to help brands streamline their certification process and maintain compliance with industry standards.

---

**Ready to get NSF certified?** This tool provides everything you need to organize your product data and generate professional submissions for NSF International certification programs.
