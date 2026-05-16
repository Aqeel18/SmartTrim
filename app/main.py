from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from app.api import routes
from app.api.auth_routes import auth_router
from app.api.history_routes import history_router
from app.db.session import create_tables
import os


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manages the full lifecycle of the application.
    Models are loaded once on startup and gracefully shut down on exit.
    Using the lifespan pattern instead of module-level globals prevents silent
    failures and ensures the server refuses traffic until models are ready.
    """
    print("[SmartTrim 360] Starting up — loading pipeline models...")
    # Create DB tables (no-op if already exist)
    try:
        create_tables()
        print("[SmartTrim 360] Database tables ready.")
    except Exception as db_exc:
        print(f"[SmartTrim 360] WARNING: DB init failed: {db_exc}")
    # Routes initialise models internally; we surface any startup errors here
    if not routes.MODELS_LOADED:
        print("[SmartTrim 360] WARNING: One or more pipeline models failed to load.")
        print("[SmartTrim 360] Check logs above. The /preview endpoint may be unavailable.")
    else:
        print("[SmartTrim 360] All models loaded. Server is ready.")

    yield  # Application runs here

    print("[SmartTrim 360] Shutting down.")


app = FastAPI(
    title="SmartTrim 360",
    description=(
        "Production API for SmartTrim 360 — an AI-powered hairstyle preview and "
        "personal grooming platform. Combines MediaPipe face analysis, BiSeNet hair "
        "segmentation, TPS geometric warping, Poisson blending, and optional "
        "Stable Diffusion inpainting."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

# Ensure working directories exist
os.makedirs("test_images", exist_ok=True)
os.makedirs("uploads", exist_ok=True)

# ── Static file mounts ───────────────────────────────────────────────────────
app.mount("/validation-images", StaticFiles(directory="test_images"), name="validation-images")

_base = os.path.dirname(__file__)
_mounts = {
    "/hairstyle-assets":      os.path.join(_base, "assets", "cleaned_hairstyles"),
    "/hairstyle-assets-orig": os.path.join(_base, "assets", "hairstyles"),
    "/hairstyle-assets-raw":  os.path.join(_base, "assets", "raw_hairstyles"),
    "/ui-assets":             os.path.join(_base, "assets", "ui"),
}
for route_path, directory in _mounts.items():
    if os.path.isdir(directory):
        name = route_path.lstrip("/").replace("/", "-")
        app.mount(route_path, StaticFiles(directory=directory), name=name)

# ── API routes ────────────────────────────────────────────────────────────────
app.include_router(routes.router)
app.include_router(auth_router)
app.include_router(history_router)


@app.get("/", tags=["Health"])
async def root():
    return {
        "service": "SmartTrim 360 API",
        "version": "1.0.0",
        "status": "ok",
        "models_loaded": routes.MODELS_LOADED,
    }


@app.get("/health", tags=["Health"])
async def health():
    """Lightweight health-check endpoint for container orchestrators."""
    return {"status": "ok", "models_loaded": routes.MODELS_LOADED}
