import asyncio
from playwright.async_api import async_playwright

async def inspect():
    p = await async_playwright().start()
    browser = await p.chromium.launch(headless=True)
    page = await browser.new_page()
    url = "https://gemini.google.com/share/fed2e5f4f4c3?skid=4bd31dae-312d-41d0-96e6-fb0b519ae1c4"
    await page.goto(url, wait_until="networkidle", timeout=60000)
    await page.wait_for_timeout(3000)

    # Click Preview tab/button
    preview_btn = page.locator("button:has-text('Preview'), [role='tab']:has-text('Preview'), div:has-text('Preview')").first
    if await preview_btn.is_visible():
        print("[INFO] Found Preview button/tab! Clicking...")
        await preview_btn.click()
        await page.wait_for_timeout(3000)

    print(f"[INFO] Total frames: {len(page.frames)}")
    target_frame = None
    for idx, f in enumerate(page.frames):
        try:
            inp_cnt = await f.locator("#fileInput").count()
            btn_cnt = await f.locator("#generateBtn").count()
            print(f"Frame {idx} ({f.url[:60]}): #fileInput={inp_cnt}, #generateBtn={btn_cnt}")
            if inp_cnt > 0 and btn_cnt > 0:
                target_frame = f
        except Exception as e:
            pass

    if target_frame:
        print("[SUCCESS] Found HTML App Frame with #fileInput and #generateBtn!")
    else:
        print("[NOTICE] App frame not directly found, checking embedded sandbox iframes...")

    await page.screenshot(path="gemini_preview_after_click.png", full_page=True)
    await browser.close()
    await p.stop()

if __name__ == "__main__":
    asyncio.run(inspect())
