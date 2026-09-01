import sys
import httpx
from pathlib import Path

STATE_JSON = Path(r"F:\Projects\FlowBot\state.json")

def main():
    if len(sys.argv) < 2:
        print("Usage: python sync_json_session_to_railway.py <RAILWAY_URL>")
        print("Example: python sync_json_session_to_railway.py https://flowbot-railway-production.up.railway.app")
        return

    railway_url = sys.argv[1].rstrip("/")
    upload_endpoint = f"{railway_url}/api/v1/auth/upload-session"

    print("=" * 60)
    print("[INFO] Uploading cross-platform state.json to Railway...")
    print("=" * 60)

    if not STATE_JSON.exists():
        print(f"[ERROR] state.json not found! Run scripts/export_session.py first.")
        return

    size_kb = STATE_JSON.stat().st_size / 1024
    print(f"[INFO] Uploading state.json ({size_kb:.2f} KB) to {upload_endpoint} ...")

    with open(STATE_JSON, "rb") as f:
        files = {"file": ("state.json", f, "application/json")}
        with httpx.Client(timeout=60.0) as client:
            r = client.post(upload_endpoint, files=files)

    if r.status_code == 200:
        print("\n" + "=" * 60)
        print("[SUCCESS] Cross-platform session uploaded to Railway successfully!")
        print(f"[RESPONSE] {r.json()}")
        print("=" * 60)
    else:
        print(f"\n[FAILED] Upload returned status {r.status_code}: {r.text}")

if __name__ == "__main__":
    main()
