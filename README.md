# FlowBot-Railway 🚂

A dedicated Google Flow Image Generation Backend API ready for 1-click deployment on **Railway**.

---

## 🚀 How to Deploy on Railway

1. Go to [Railway.app](https://railway.app) and create a **New Project**.
2. Select **Deploy from GitHub repo** and choose **`RukshanAmodya/FlowBot-Railway`**.
3. Railway will automatically detect the `Dockerfile` and deploy the service.
4. Under your Service **Settings** > **Networking**, click **Generate Domain** to get your public URL (e.g. `https://flowbot-railway-production.up.railway.app`).

---

## 🔑 Syncing Authenticated Google Session

Once deployed on Railway, run this single command on your PC to upload your Google Flow login session to Railway:

```powershell
python sync_session_to_railway.py https://YOUR-RAILWAY-URL.up.railway.app
```

---

## 📡 API Endpoints

### 1. Check Status
```http
GET /api/v1/status
```

### 2. Generate Image (9:16 Portrait, Nano Banana 2)
```http
POST /api/v1/generate
Content-Type: application/json

{
  "prompt": "Cinematic portrait of a warrior princess in ancient palace, 8k, highly detailed",
  "aspect_ratio": "9:16",
  "count": 1,
  "reference_image_base64": "<OPTIONAL_BASE64_STRING>"
}
```

### 3. Interactive API Documentation (Swagger)
Open `https://YOUR-RAILWAY-URL.up.railway.app/docs` in your browser.
