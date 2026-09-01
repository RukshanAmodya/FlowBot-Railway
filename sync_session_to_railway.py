import sys
import tarfile
import httpx
from pathlib import Path

# Set paths
LOCAL_PROFILE = Path(r"F:\Projects\FlowBot\browser_profile")
TAR_FILE = Path("railway_session.tar.gz")

def main():
    if len(sys.argv) < 2:
        print("Usage: python sync_session_to_railway.py <RAILWAY_URL>")
        print("Example: python sync_session_to_railway.py https://flowbot-railway-production.up.railway.app")
        return

    railway_url = sys.argv[1].rstrip("/")
    upload_endpoint = f"{railway_url}/api/v1/auth/upload-session"

    print("=" * 60)
    print("[INFO] Packaging local authenticated Google Flow session...")
    print("=" * 60)

    if not LOCAL_PROFILE.exists():
        print(f"[ERROR] Local profile not found at {LOCAL_PROFILE}")
        return

    # Create tar.gz of browser profile
    with tarfile.open(TAR_FILE, "w:gz") as tar:
        tar.add(str(LOCAL_PROFILE), arcname=".")

    size_mb = TAR_FILE.stat().st_size / (1024 * 1024)
    print(f"[SUCCESS] Session archive created ({size_mb:.2f} MB)")

    print(f"[INFO] Uploading session to Railway: {upload_endpoint} ...")
    try:
        with open(TAR_FILE, "rb") as f:
            files = {"file": ("session.tar.gz", f, "application/gzip")}
            with httpx.Client(timeout=180.0) as client:
                r = client.post(upload_endpoint, files=files)
                
        if r.status_code == 200:
            print("\n" + "=" * 60)
            print("[SUCCESS] Session successfully synced to Railway!")
            print(f"[RESPONSE] {r.json()}")
            print("=" * 60)
        else:
            print(f"\n[FAILED] Upload returned status {r.status_code}: {r.text}")
    except Exception as e:
        print(f"\n[ERROR] Failed to upload session: {e}")
    finally:
        TAR_FILE.unlink(missing_ok=True)

if __name__ == "__main__":
    main()
