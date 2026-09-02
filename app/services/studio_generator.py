"""Gemini Studio Generator Service orchestrating uploads, prompt injection, and output saving."""
import base64
import asyncio
import datetime
from pathlib import Path
from typing import List, Optional
from playwright.async_api import Page
from app.config import settings
from app.utils.logger import logger
from app.services.gemini_studio_adapter import GeminiStudioAdapter, StudioAutomationException

class StudioGeneratorService:
    def __init__(self, page: Page):
        self.page = page
        self.adapter = GeminiStudioAdapter(page)

    async def capture_diagnostic_snapshot(self, prefix: str = "snapshot") -> Path:
        """Captures screenshot for debugging."""
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        screenshot_file = settings.screenshot_path / f"{timestamp}_{prefix}.png"
        try:
            await self.page.screenshot(path=str(screenshot_file), full_page=True)
            logger.info(f"Saved diagnostic snapshot to {screenshot_file}")
        except Exception as e:
            logger.error(f"Failed to capture snapshot: {e}")
        return screenshot_file

    async def execute_generation(
        self,
        prompt: str,
        generation_id: str,
        reference_image_base64: Optional[str] = None,
        reference_image_url: Optional[str] = None
    ) -> List[Path]:
        """Executes full Gemini Studio generation flow."""
        try:
            self.page.set_default_timeout(60000)

            # Step 1: Initialize and connect to Gemini App Frame
            await self.adapter.navigate_and_init()
            await self.capture_diagnostic_snapshot(f"{generation_id}_step1_app_loaded")

            # Step 2: Upload Reference Image if provided
            if reference_image_base64 or reference_image_url:
                ref_path = settings.output_path / generation_id / "reference_input.png"
                ref_path.parent.mkdir(parents=True, exist_ok=True)

                if reference_image_base64:
                    raw_b64 = reference_image_base64.split(",", 1)[-1] if "," in reference_image_base64 else reference_image_base64
                    ref_path.write_bytes(base64.b64decode(raw_b64))
                    await self.adapter.upload_reference_image(ref_path)
                elif reference_image_url:
                    import httpx
                    async with httpx.AsyncClient() as client:
                        resp = await client.get(reference_image_url, timeout=15)
                        if resp.status_code == 200:
                            ref_path.write_bytes(resp.content)
                            await self.adapter.upload_reference_image(ref_path)

                await self.capture_diagnostic_snapshot(f"{generation_id}_step2_ref_uploaded")

            # Step 3: Inject Prompt and click Generate Image
            await self.adapter.insert_prompt_and_generate(prompt)
            await self.capture_diagnostic_snapshot(f"{generation_id}_step3_generating")

            # Step 4: Wait for completion and extract output
            canvas_data = await self.adapter.wait_for_completion(timeout_seconds=settings.GENERATION_TIMEOUT_SECONDS)
            await self.capture_diagnostic_snapshot(f"{generation_id}_step4_success")

            # Step 5: Save output image
            out_dir = settings.output_path / generation_id
            out_dir.mkdir(parents=True, exist_ok=True)
            output_file = out_dir / "image_1.png"

            _, b64_payload = canvas_data.split(",", 1)
            output_file.write_bytes(base64.b64decode(b64_payload))
            logger.info(f"Successfully generated and saved image to {output_file} ({output_file.stat().st_size} bytes)")

            return [output_file]

        except StudioAutomationException as sae:
            await self.capture_diagnostic_snapshot(f"error_{sae.error_code.lower()}")
            raise
        except Exception as e:
            await self.capture_diagnostic_snapshot("unexpected_error")
            logger.exception(f"Unexpected error in Gemini Studio generation: {e}")
            raise StudioAutomationException("UNKNOWN_STUDIO_ERROR", f"Step failed: {str(e)}")
