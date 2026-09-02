"""Adapter layer abstracting interaction with Gemini Studio Canvas DOM."""
import asyncio
from pathlib import Path
from typing import Optional, List
from playwright.async_api import Page, Frame, Locator
from app.config import settings
from app.utils.logger import logger

class StudioAutomationException(Exception):
    def __init__(self, error_code: str, message: str, details: Optional[dict] = None):
        super().__init__(message)
        self.error_code = error_code
        self.message = message
        self.details = details or {}

class GeminiStudioAdapter:
    def __init__(self, page: Page):
        self.page = page
        self.app_frame: Optional[Frame] = None

    async def navigate_and_init(self) -> Frame:
        """Navigates to Gemini Studio share URL and connects to the interactive HTML app frame."""
        logger.info(f"Navigating to Gemini Studio: {settings.STUDIO_URL}...")
        try:
            await self.page.goto(settings.STUDIO_URL, wait_until="domcontentloaded", timeout=45000)
        except Exception as e:
            logger.info(f"Navigation notice ({e}); waiting for DOM to settle...")

        await self.page.wait_for_timeout(3000)

        # 1. Dismiss "Continue" dialog if visible
        try:
            continue_btn = self.page.locator("button:has-text('Continue')").first
            if await continue_btn.is_visible(timeout=3000):
                logger.info("Clicking 'Continue' dialog button...")
                await continue_btn.click()
                await self.page.wait_for_timeout(3000)
        except Exception:
            pass

        # 2. Dismiss cookie notice if visible
        try:
            cookie_btn = self.page.locator("button:has-text('OK, got it'), button:has-text('Accept all')").first
            if await cookie_btn.is_visible(timeout=1000):
                await cookie_btn.click()
                await self.page.wait_for_timeout(400)
        except Exception:
            pass

        # 3. Locate the iframe running the HTML App
        for _ in range(20):
            for f in self.page.frames:
                try:
                    if await f.locator("#fileInput").count() > 0 and await f.locator("#generateBtn").count() > 0:
                        self.app_frame = f
                        logger.info(f"Successfully connected to Gemini App Frame: {f.url[:60]}")
                        return self.app_frame
                except Exception:
                    pass
            await self.page.wait_for_timeout(1000)

        raise StudioAutomationException(
            "GEMINI_FRAME_NOT_FOUND",
            "Could not locate the interactive Gemini Canvas HTML application iframe."
        )

    async def upload_reference_image(self, image_path: Path) -> None:
        """Uploads reference image to the #fileInput inside the app frame."""
        if not self.app_frame:
            await self.navigate_and_init()

        logger.info(f"Uploading reference image: {image_path.name} to #fileInput...")
        file_input = self.app_frame.locator("#fileInput")
        await file_input.set_input_files(str(image_path))
        await self.page.wait_for_timeout(1500)

    async def insert_prompt_and_generate(self, prompt: str) -> None:
        """Types prompt into #promptInput and clicks #generateBtn."""
        if not self.app_frame:
            await self.navigate_and_init()

        logger.info(f"Injecting user prompt: '{prompt}'...")
        prompt_box = self.app_frame.locator("#promptInput")
        await prompt_box.fill(prompt)
        await self.page.wait_for_timeout(500)

        logger.info("Clicking #generateBtn to start AI generation...")
        gen_btn = self.app_frame.locator("#generateBtn")
        await gen_btn.click()
        await self.page.wait_for_timeout(1500)

    async def wait_for_completion(self, timeout_seconds: int = 180) -> str:
        """Polls #status until 'Success!' or error, and returns extracted base64 image."""
        if not self.app_frame:
            raise StudioAutomationException("APP_FRAME_MISSING", "Gemini App frame is not initialized.")

        logger.info("Tracking generation status in Gemini Studio...")
        start_time = asyncio.get_event_loop().time()

        while asyncio.get_event_loop().time() - start_time < timeout_seconds:
            try:
                status_text = await self.app_frame.locator("#status").inner_text()
                if status_text:
                    logger.info(f"Gemini Status: {status_text}")

                if "Success" in status_text:
                    logger.info("100% Generation Success detected!")
                    await self.page.wait_for_timeout(1000)
                    break
                elif "Error" in status_text:
                    raise StudioAutomationException("GENERATION_FAILED", f"Gemini Studio reported error: {status_text}")
            except StudioAutomationException:
                raise
            except Exception:
                pass

            await asyncio.sleep(2)
        else:
            raise StudioAutomationException("GENERATION_TIMEOUT", f"Generation timed out after {timeout_seconds}s.")

        # Extract canvas base64 image data
        canvas_data = await self.app_frame.evaluate("""() => {
            const canvas = document.getElementById('mainCanvas');
            return canvas ? canvas.toDataURL('image/png') : null;
        }""")

        if not canvas_data or len(canvas_data) < 1000:
            raise StudioAutomationException("CANVAS_EXTRACTION_FAILED", "Failed to extract rendered image from #mainCanvas.")

        return canvas_data
