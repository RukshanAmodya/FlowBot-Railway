import asyncio
from pathlib import Path
from playwright.async_api import async_playwright

async def test_full_gen():
    p = await async_playwright().start()
    browser = await p.chromium.launch(headless=True)
    page = await browser.new_page()
    url = "https://gemini.google.com/share/fed2e5f4f4c3?skid=4bd31dae-312d-41d0-96e6-fb0b519ae1c4"
    print(f"[INFO] Navigating to {url}...")
    await page.goto(url, wait_until="networkidle", timeout=60000)
    await page.wait_for_timeout(2000)

    # Click Continue
    continue_btn = page.locator("button:has-text('Continue')").first
    if await continue_btn.is_visible():
        await continue_btn.click()
        await page.wait_for_timeout(3000)

    # Locate app frame
    target_frame = None
    for f in page.frames:
        try:
            if await f.locator("#fileInput").count() > 0:
                target_frame = f
                break
        except Exception:
            pass

    if not target_frame:
        print("[ERROR] App frame not found!")
        await browser.close()
        return

    # Upload reference image
    img_path = Path(r"C:\Users\Rukshan Amodya\Downloads\38e1213cbf7935579e3234b266c13c42.jpg")
    print(f"[INFO] Uploading reference image: {img_path.name}...")
    file_input = target_frame.locator("#fileInput")
    await file_input.set_input_files(str(img_path))
    await page.wait_for_timeout(1500)

    # Type prompt
    prompt_text = "Create this image 9:16 size, cinematic portrait of this person holding a cute puppy in arms, soft warm lighting, 8k resolution"
    print(f"[INFO] Injecting prompt: {prompt_text}...")
    prompt_box = target_frame.locator("#promptInput")
    await prompt_box.fill(prompt_text)
    await page.wait_for_timeout(500)

    # Click Generate
    print("[INFO] Clicking Generate Image button...")
    gen_btn = target_frame.locator("#generateBtn")
    await gen_btn.click()

    # Wait for completion (status text or canvas data)
    print("[INFO] Waiting for image generation to complete...")
    for _ in range(60):
        status = await target_frame.locator("#status").inner_text()
        print(f"Status: {status}")
        if "Success" in status:
            print("[SUCCESS] Generation completed successfully!")
            break
        elif "Error" in status:
            print(f"[ERROR] Generation failed: {status}")
            break
        await page.wait_for_timeout(2000)

    # Extract canvas image data
    canvas_data = await target_frame.evaluate("""() => {
        const canvas = document.getElementById('mainCanvas');
        return canvas ? canvas.toDataURL('image/png') : null;
    }""")

    if canvas_data and len(canvas_data) > 1000:
        import base64
        _, b64 = canvas_data.split(",", 1)
        out_file = Path("gemini_generated_output.png")
        out_file.write_bytes(base64.b64decode(b64))
        print(f"[SUCCESS] Saved generated image to {out_file.resolve()} (Size: {out_file.stat().st_size} bytes)")

    await page.screenshot(path="gemini_after_gen.png", full_page=True)
    await browser.close()
    await p.stop()

if __name__ == "__main__":
    asyncio.run(test_full_gen())
