"""FastAPI application entrypoint for FlowBot-Railway."""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.api.routes import router as api_router
from app.utils.logger import logger

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting FlowBot-Railway Production Service...")
    settings.output_path.mkdir(parents=True, exist_ok=True)
    settings.screenshot_path.mkdir(parents=True, exist_ok=True)
    yield
    from app.services.session_manager import session_manager
    try:
        await session_manager.close()
    except Exception:
        pass
    logger.info("FlowBot-Railway Service stopped.")


app = FastAPI(
    title="FlowBot-Railway API",
    description="Google Flow Image Generation Service for Railway",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)

# Mount generated images statically
app.mount("/generated", StaticFiles(directory=str(settings.output_path)), name="generated")

@app.get("/")
async def root():
    return {
        "service": "FlowBot-Railway API",
        "status": "online",
        "docs": "/docs",
        "endpoints": {
            "generate": "POST /api/v1/generate",
            "status": "GET /api/v1/status",
            "upload_session": "POST /api/v1/auth/upload-session"
        }
    }
