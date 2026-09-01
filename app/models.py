"""API Data Models for Railway FlowBot Server."""
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

class GenerateRequest(BaseModel):
    prompt: str = Field(..., description="Prompt text to generate images with")
    aspect_ratio: str = Field("9:16", description="Aspect ratio (e.g. 9:16, 16:9, 1:1)")
    count: int = Field(1, description="Number of images to generate (default: 1)")
    reference_image_base64: Optional[str] = Field(None, description="Optional base64 encoded reference image")
    reference_image_url: Optional[str] = Field(None, description="Optional public URL to reference image")

class GenerateResponse(BaseModel):
    success: bool = True
    generation_id: str
    prompt: str
    count: int
    images: List[str]
    zip_download_url: Optional[str] = None

class StatusResponse(BaseModel):
    status: str
    is_busy: bool
    authenticated: bool
    user_email: Optional[str] = None
    service: str = "FlowBot-Railway"
