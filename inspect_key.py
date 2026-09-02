import asyncio
from pathlib import Path
from playwright.async_api import async_playwright

async def inspect_api_call():
    p = await async_playwright().start()
    browser = await p.chromium.launch(headless=True)
    page = await browser.new_page()

    # Capture network requests to see how Gemini injects API Key or calls GenerativeLanguage API
    page.on("request", lambda req: print(f"[REQ] {req.method} {req.url[:100]}"))
    page.on("response", lambda res: print(f"[RES] {res.status} {res.url[:100]}") if "generativelanguage" in res.url or "key=" in res.url else None)

    url = "https://gemini.google.com/share/fed2e5f4f4c3?skid=4bd31dae-312d-41d0-96e6-fb0b519ae1c4"
    await page.goto(url, wait_until="domcontentloaded", timeout=45000)
    await page.wait_for_timeout(3000)

    continue_btn = page.locator("button:has-text('Continue')").first
    if await continue_btn.is_visible():
        await continue_btn.click()
        await page.wait_for_timeout(3000)

    target_frame = None
    for f in page.frames:
        try:
            if await f.locator("#fileInput").count() > 0:
                target_frame = f
                break
        except Exception:
            pass

    if target_frame:
        # Check apiKey variable inside iframe
        key_val = await target_frame.evaluate("() => typeof apiKey !== 'undefined' ? apiKey : 'NOT_DEFINED'")
        print(f"\n[KEY INSPECTION] apiKey in iframe: '{key_val}'")

    await browser.close()
    await p.stop()

if __name__ == "__main__":
    asyncio.run(inspect_api_call())
