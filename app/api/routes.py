"""API routes for Railway FlowBot Server."""
import uuid
import asyncio
import shutil
from typing import Optional, List, Dict
from pathlib import Path
from fastapi import APIRouter, HTTPException, UploadFile, File, BackgroundTasks

from fastapi.responses import FileResponse, JSONResponse
from app.config import settings
from app.models import GenerateRequest, GenerateResponse, StatusResponse
from app.services.session_manager import session_manager
from app.services.flow_generator import FlowGeneratorService
from app.services.flow_adapter import GoogleFlowAdapter, FlowAutomationException
from app.utils.logger import logger

router = APIRouter(prefix="/api/v1", tags=["FlowBot-Railway"])
generation_lock = asyncio.Lock()

def get_static_logged_in_email() -> Optional[str]:
    """Safely extracts logged in email from browser profile without launching browser."""
    try:
        import json
        pref_file = settings.profile_path / "Default" / "Preferences"
        if pref_file.exists():
            data = json.loads(pref_file.read_text(encoding="utf-8", errors="ignore"))
            accounts = data.get("account_info", [])
            if accounts and isinstance(accounts, list):
                return accounts[0].get("email")
    except Exception:
        pass
    return None

@router.get("/screenshots")
async def list_screenshots():
    """Lists all captured diagnostic and step screenshots."""
    files = list(settings.screenshot_path.glob("*.png"))
    files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
    return {
        "count": len(files),
        "screenshots": [f"/screenshots/{f.name}" for f in files[:20]]
    }

@router.get("/status", response_model=StatusResponse)
async def get_status():
    """Checks authentication status and readiness."""
    user_email = get_static_logged_in_email()
    auth_state = bool(user_email or (settings.profile_path / "Default").exists())
    return StatusResponse(
        status="running",
        is_busy=generation_lock.locked(),
        authenticated=auth_state,
        user_email=user_email
    )



@router.post("/generate", response_model=GenerateResponse)
async def generate_images(req: GenerateRequest):
    """Executes single generation request on Railway."""
    if generation_lock.locked():
        raise HTTPException(
            status_code=409,
            detail={"success": False, "error": "GENERATION_IN_PROGRESS", "message": "Another generation is in progress."}
        )

    async with generation_lock:
        gen_id = uuid.uuid4().hex[:12]
        logger.info(f"Accepted generate request [{gen_id}]: prompt='{req.prompt}', count={req.count}, ratio={req.aspect_ratio}")
        
        try:
            page = await session_manager.get_or_create_context()
            generator = FlowGeneratorService(page)
            
            image_paths = await generator.execute_generation(
                prompt=req.prompt,
                generation_id=gen_id,
                count=req.count,
                aspect_ratio=req.aspect_ratio,
                reference_image_base64=req.reference_image_base64,
                reference_image_url=req.reference_image_url
            )
            
            # Format image URLs
            image_urls = [f"/generated/{gen_id}/{p.name}" for p in image_paths]
            
            return GenerateResponse(
                success=True,
                generation_id=gen_id,
                prompt=req.prompt,
                count=len(image_paths),
                images=image_urls,
                zip_download_url=f"/api/v1/download/{gen_id}.zip"
            )
            
        except FlowAutomationException as fae:
            logger.error(f"FlowAutomationException in generation [{gen_id}]: {fae.error_code} - {fae.message}")
            raise HTTPException(
                status_code=500,
                detail={"success": False, "error": fae.error_code, "message": fae.message, "details": fae.details}
            )
        except Exception as e:
            logger.error(f"Unexpected error in generation [{gen_id}]: {e}")
            current_url = "unknown"
            try:
                current_url = page.url
                await page.screenshot(path=str(settings.screenshot_path / f"railway_err_{gen_id}.png"))
            except Exception:
                pass
            raise HTTPException(
                status_code=500,
                detail={"success": False, "error": "UNKNOWN_FLOW_ERROR", "message": f"{str(e)} on URL: {current_url}"}
            )


@router.get("/download/{generation_id}.zip")
async def download_zip(generation_id: str):
    """Downloads all generated image assets as a zip file."""
    gen_dir = settings.output_path / generation_id
    if not gen_dir.exists():
        raise HTTPException(status_code=404, detail="Generation output not found.")
        
    zip_path = settings.output_path / f"{generation_id}.zip"
    if not zip_path.exists():
        shutil.make_archive(str(settings.output_path / generation_id), "zip", gen_dir)
        
    return FileResponse(
        path=zip_path,
        filename=f"FlowBot_{generation_id}.zip",
        media_type="application/zip"
    )

@router.post("/auth/upload-session")
async def upload_session(file: UploadFile = File(...)):
    """Uploads and unpacks authenticated Google session (tar.gz or state.json) into Railway."""
    try:
        try:
            await session_manager.close()
        except Exception:
            pass

        filename = file.filename or "session.tar.gz"
        if filename.endswith(".json"):
            # Direct cross-platform storage state JSON
            target_json = settings.base_path / "state.json"
            with open(target_json, "wb") as f:
                shutil.copyfileobj(file.file, f)
            logger.info(f"Cross-platform state.json saved to {target_json} ({target_json.stat().st_size} bytes)")
            return {"success": True, "message": "Cross-platform state.json Synced successfully!"}
        else:
            temp_tar = settings.temp_path / "temp_session.tar.gz"
            settings.temp_path.mkdir(parents=True, exist_ok=True)
            with open(temp_tar, "wb") as f:
                shutil.copyfileobj(file.file, f)
                
            settings.profile_path.mkdir(parents=True, exist_ok=True)
            shutil.unpack_archive(str(temp_tar), str(settings.profile_path), "gztar")
            temp_tar.unlink(missing_ok=True)
            
            email = get_static_logged_in_email()
            logger.info(f"Google Flow Session unpacked successfully on Railway. User: {email}")
            return {"success": True, "message": "Google Session Synced successfully!", "user_email": email}

    except Exception as e:
        logger.error(f"Failed to unpack session: {e}")
        raise HTTPException(status_code=500, detail=str(e))

