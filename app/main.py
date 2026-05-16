from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from app.api import routes
import os

app = FastAPI(
    title="SmartTrim_360",
    description="Backend API for AI-powered hairstyle preview system",
    version="0.1.0"
)

# Ensure test_images directory exists
os.makedirs("test_images", exist_ok=True)

# Mount static files for validation images
app.mount("/validation-images", StaticFiles(directory="test_images"), name="validation-images")

# Mount static files for hairstyle assets so the frontend can show thumbnails
_base = os.path.dirname(__file__)
_assets_cleaned = os.path.join(_base, 'assets', 'cleaned_hairstyles')
_assets_orig = os.path.join(_base, 'assets', 'hairstyles')
_assets_raw = os.path.join(_base, 'assets', 'raw_hairstyles')
_assets_ui = os.path.join(_base, 'assets', 'ui')

if os.path.isdir(_assets_cleaned):
    app.mount("/hairstyle-assets", StaticFiles(directory=_assets_cleaned), name="hairstyle-assets")
if os.path.isdir(_assets_orig):
    app.mount("/hairstyle-assets-orig", StaticFiles(directory=_assets_orig), name="hairstyle-assets-orig")
if os.path.isdir(_assets_raw):
    app.mount("/hairstyle-assets-raw", StaticFiles(directory=_assets_raw), name="hairstyle-assets-raw")
if os.path.isdir(_assets_ui):
    app.mount("/ui-assets", StaticFiles(directory=_assets_ui), name="ui-assets")

# Include API routes
app.include_router(routes.router)

@app.get("/")
async def root():
    return {"message": "Welcome to SmartTrim_360 API"}
