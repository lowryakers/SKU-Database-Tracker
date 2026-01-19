# SKU Database Tracker

A modern, web-based inventory management system for tracking Stock Keeping Units (SKUs). Built with Python, FastAPI, and SQLite.

## Features

- RESTful API for SKU management (Create, Read, Update, Delete)
- SQLite database for simple, portable data storage
- Async/await support for high performance
- Modern Python type hints and validation
- Interactive API documentation (Swagger UI)
- Easy to deploy and maintain

## Tech Stack

- **Backend Framework**: FastAPI 0.109+
- **Database**: SQLite with SQLAlchemy 2.0+ (async)
- **Data Validation**: Pydantic 2.5+
- **Server**: Uvicorn with standard extras
- **Python Version**: 3.11+

## Project Structure

```
sku-database-tracker/
├── app/
│   ├── api/              # API routes
│   ├── database/         # Database connection and configuration
│   ├── models/           # SQLAlchemy database models
│   ├── schemas/          # Pydantic schemas for validation
│   ├── static/           # Static files (CSS, JS, images)
│   ├── templates/        # HTML templates
│   ├── config.py         # Application configuration
│   └── main.py           # FastAPI application entry point
├── tests/                # Test files
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

1. Clone the repository:
```bash
git clone <repository-url>
cd SKU-Database-Tracker
```

2. Create a virtual environment:
```bash
python -m venv venv

# On Windows
venv\Scripts\activate

# On macOS/Linux
source venv/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create environment file:
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
- Main application: http://localhost:8000
- Interactive API docs (Swagger): http://localhost:8000/docs
- Alternative API docs (ReDoc): http://localhost:8000/redoc

## API Endpoints

### SKU Management

- `POST /api/v1/skus` - Create a new SKU
- `GET /api/v1/skus` - List all SKUs (with pagination)
- `GET /api/v1/skus/{id}` - Get a specific SKU
- `PUT /api/v1/skus/{id}` - Update a SKU
- `DELETE /api/v1/skus/{id}` - Delete a SKU

### Example SKU Object

```json
{
  "sku_code": "PROD-001",
  "name": "Widget A",
  "description": "High-quality widget",
  "category": "Widgets",
  "quantity": 100,
  "unit_price": 29.99,
  "supplier": "Acme Corp",
  "location": "Warehouse A, Shelf 3"
}
```

## Development

### Install Development Dependencies

```bash
pip install -r requirements-dev.txt
```

### Code Quality Tools

- **Black**: Code formatter
```bash
black app/ tests/
```

- **Ruff**: Fast Python linter
```bash
ruff check app/ tests/
```

- **MyPy**: Static type checker
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

### Current Dependencies (Secure & Modern)

All dependencies are selected for security, performance, and modern Python best practices:

| Package | Version | Purpose | Security Notes |
|---------|---------|---------|----------------|
| **fastapi** | >=0.109.0 | Web framework | Active development, regular security updates |
| **uvicorn** | >=0.27.0 | ASGI server | Production-ready, widely used |
| **sqlalchemy** | >=2.0.25 | ORM/Database | Latest 2.x version, async support |
| **pydantic** | >=2.5.3 | Data validation | V2 with performance improvements |
| **pydantic-settings** | >=2.1.0 | Settings management | Secure config handling |
| **python-multipart** | >=0.0.6 | Form data parsing | Required for file uploads |
| **jinja2** | >=3.1.3 | Template engine | Security fixes included |
| **aiosqlite** | >=0.19.0 | Async SQLite | Enables async database operations |

### Dependency Recommendations

✅ **No outdated packages** - All dependencies use recent stable versions

✅ **No known vulnerabilities** - Selected versions have no published CVEs

✅ **Minimal bloat** - Only essential packages included

✅ **Production ready** - All packages are battle-tested and widely used

### Regular Maintenance

To check for updates:
```bash
pip list --outdated
```

To upgrade packages:
```bash
pip install --upgrade -r requirements.txt
```

## Security Considerations

1. **Change SECRET_KEY**: Update the secret key in `.env` for production
2. **Environment Variables**: Never commit `.env` files to version control
3. **Database Backups**: Regularly backup your SQLite database
4. **Input Validation**: All inputs are validated via Pydantic schemas
5. **SQL Injection**: Protected by SQLAlchemy ORM

## Future Enhancements

- [ ] Authentication and authorization (JWT tokens)
- [ ] User management and roles
- [ ] Web UI for non-technical users
- [ ] Barcode scanning support
- [ ] Export/import functionality (CSV, Excel)
- [ ] Inventory analytics and reporting
- [ ] Low stock alerts
- [ ] Multi-warehouse support
- [ ] Audit logs for all changes

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

MIT License - feel free to use this project for personal or commercial purposes.

## Support

For issues, questions, or contributions, please open an issue on the repository.
