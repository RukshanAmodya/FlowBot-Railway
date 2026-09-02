import asyncio
from pathlib import Path
from playwright.async_api import async_playwright
from app.config import settings

async def test_logged_in():
    p = await async_playwright().start()
    
    # Launch real logged-in Chrome browser
    context = await p.chromium.launch_persistent_context(
        user_data_dir=str(Path(r"F:\Projects\FlowBot\browser_profile")),
        channel="chrome",
        headless=False,
        args=["--start-maximized"]
    )
    
    page = context.pages[0] if context.pages else await context.new_page()
    url = "https://gemini.google.com/share/fed2e5f4f4c3?skid=4bd31dae-312d-41d0-96e6-fb0b519ae1c4"
    print(f"[INFO] Navigating with Real Logged-in Chrome to {url}...")
    await page.goto(url, wait_until="domcontentloaded", timeout=60000)
    await page.wait_for_timeout(4000)

    # Click Continue on dialog if present
    continue_btn = page.locator("button:has-text('Continue')").first
    if await continue_btn.is_visible(timeout=3000):
        print("[INFO] Clicking 'Continue' button...")
        await continue_btn.click()
        await page.wait_for_timeout(3000)

    # Find App Frame
    target_frame = None
    for _ in range(15):
        for f in page.frames:
            try:
                if await f.locator("#fileInput").count() > 0:
                    target_frame = f
                    break
            except Exception:
                pass
        if target_frame:
            break
        await page.wait_for_timeout(1000)

    if not target_frame:
        print("[ERROR] App frame not found!")
        await context.close()
        return

    print("[SUCCESS] App frame found in logged-in Chrome!")
    
    # Check injected apiKey in logged-in session
    key_val = await target_frame.evaluate("() => typeof apiKey !== 'undefined' ? apiKey : 'NOT_DEFINED'")
    print(f"[KEY CHECK] Injected apiKey: '{key_val[:10]}...' (Length: {len(key_val)})")

    # Upload reference image
    img_path = Path(r"C:\Users\Rukshan Amodya\Downloads\38e1213cbf7935579e3234b266c13c42.jpg")
    print(f"[INFO] Uploading reference image: {img_path.name}...")
    await target_frame.locator("#fileInput").set_input_files(str(img_path))
    await page.wait_for_timeout(2000)

    # Fill Prompt
    prompt_text = "Create this image 9:16 size, cinematic portrait of this person holding a cute adorable puppy in arms, soft warm lighting, 8k resolution"
    print(f"[INFO] Injecting prompt: {prompt_text}...")
    await target_frame.locator("#promptInput").fill(prompt_text)
    await page.wait_for_timeout(500)

    # Click Generate
    print("[INFO] Clicking Generate Image button...")
    await target_frame.locator("#generateBtn").click()

    # Track status
    for _ in range(60):
        status = await target_frame.locator("#status").inner_text()
        print(f"Status: {status}")
        if "Success" in status:
            print("[SUCCESS] Generation completed successfully!")
            break
        elif "Error" in status:
            print(f"[ERROR] Status returned: {status}")
            break
        await page.wait_for_timeout(2000)

    # Extract Canvas
    canvas_data = await target_frame.evaluate("""() => {
        const canvas = document.getElementById('mainCanvas');
        return canvas ? canvas.toDataURL('image/png') : null;
    }""")

    if canvas_data and len(canvas_data) > 1000:
        import base64
        _, b64 = canvas_data.split(",", 1)
        out_file = Path(r"F:\Projects\FlowBot-Railway\gemini_logged_in_output.png")
        out_file.write_bytes(base64.b64decode(b64))
        print(f"[SUCCESS] Saved generated puppy image to: {out_file.resolve()} ({out_file.stat().st_size} bytes)")

    await page.wait_for_timeout(3000)
    await context.close()
    await p.stop()

if __name__ == "__main__":
    asyncio.run(test_logged_in())
