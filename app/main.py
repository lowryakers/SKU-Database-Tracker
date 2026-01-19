"""Main FastAPI application entry point."""

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.api import routes as api_routes
from app.web import routes as web_routes
from app.database.connection import init_db
from app.models import Base

app = FastAPI(
    title="SKU Database Tracker - NSF Certification Management",
    description="A comprehensive web-based system for tracking SKUs and managing NSF certification requirements",
    version="1.0.0",
)

# Mount static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Templates
templates = Jinja2Templates(directory="app/templates")

# Include routers - Web routes first (so / goes to dashboard)
app.include_router(web_routes.router)
app.include_router(api_routes.router)


@app.on_event("startup")
async def startup_event():
    """Initialize database on startup."""
    await init_db()


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}
