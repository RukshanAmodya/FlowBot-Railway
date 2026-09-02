import asyncio
from playwright.async_api import async_playwright

async def inspect():
    p = await async_playwright().start()
    browser = await p.chromium.launch(headless=True)
    page = await browser.new_page()
    url = "https://gemini.google.com/share/fed2e5f4f4c3?skid=4bd31dae-312d-41d0-96e6-fb0b519ae1c4"
    await page.goto(url, wait_until="networkidle", timeout=60000)
    await page.wait_for_timeout(2000)

    # 1. Click "Continue" on dialog
    continue_btn = page.locator("button:has-text('Continue')").first
    if await continue_btn.is_visible():
        print("[INFO] Clicking 'Continue' dialog button...")
        await continue_btn.click()
        await page.wait_for_timeout(4000)

    # 2. Check frames after Continue
    print(f"[INFO] Frames count: {len(page.frames)}")
    target_frame = None
    for idx, f in enumerate(page.frames):
        try:
            inp = await f.locator("#fileInput").count()
            btn = await f.locator("#generateBtn").count()
            print(f"Frame {idx} ({f.url[:60]}): #fileInput={inp}, #generateBtn={btn}")
            if inp > 0 and btn > 0:
                target_frame = f
        except Exception:
            pass

    if target_frame:
        print("[SUCCESS] Found App Frame with #fileInput and #generateBtn!")
        
        # Test typing prompt inside frame
        await target_frame.locator("#promptInput").fill("Create a beautiful 9:16 portrait")
        print("[INFO] Filled prompt in iframe successfully!")

    await page.screenshot(path="gemini_app_loaded.png", full_page=True)
    await browser.close()
    await p.stop()

if __name__ == "__main__":
    asyncio.run(inspect())
