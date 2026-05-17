# Tapo C200 Security Pipeline: Scrypted + Docker Sidecar + Telegram

## 1. General Description

This repository provides a production-grade, highly optimized architectural solution to automate home security alerts. It delivers **Instant Photo Snapshots** followed by a **5-second Video Clip** straight to a Telegram chat whenever a camera detects motion. 

Designed specifically for resource-constrained edge hardware like a **Raspberry Pi**, this pipeline maintains a **near-0% idle CPU footprint** and protects your physical storage (SD card/SSD) from wear and tear. It bypasses commercial paid NVR features by implementing a lightweight **Docker Sidecar Pattern** using Python and FFmpeg, hooking directly into Scrypted's internal RTSP rebroadcast layer.

---

## 2. Scrypted Installation & ONVIF Plugin Setup

### Step 1: Deploy Scrypted via Docker
Run the following command to spin up the official Scrypted container with persistent storage and necessary port mappings:

```bash
docker run -d \
  --name scrypted \
  --restart unless-stopped \
  -v ~/.scrypted://.scrypted \
  -p 10443:10443 \
  -p 40985:40985 \
  -p 36375:36375 \
  koush/scrypted
```
*Once initialized, open your browser and access the management console at `https://localhost:10443` (or your server's local IP).*

### Step 2: Install the ONVIF Plugin
1. In the Scrypted web UI, navigate to the **Plugins** management section in the left sidebar.
2. Search for the official **ONVIF** plugin.
3. Click **Install**. This plugin allows Scrypted to handle PTZ controls and, crucially, subscribe to native hardware motion webhooks from the camera.

---

## 3. ONVIF Camera Configuration

1. Inside Scrypted, click on the **ONVIF Plugin** and select **Add Device**. 
2. Enter your Tapo C200 local IP address, along with the device's local account username and password (configured via the Tapo App).
3. Once the camera is added, go to its settings and select the **Streams** tab -> **Stream: Mainstream**.
4. Change the **RTSP Parser** option to **`FFmpeg (TCP)`**. This ensures absolute stream stability against Wi-Fi micro-drops and prevents green screen artifacts.
5. Look for the **RTSP Rebroadcast Url** field (e.g., `rtsp://localhost:36375/5f3892d1...`) and copy it. You will need this string for your backend setup, replacing `localhost` with `scrypted`.

---

## 4. Telegram Bot Configuration

Before deploying the codebase, you must set up your automated Telegram pipeline endpoints:

1. **Get a Bot Token:** Chat with `@BotFather` on Telegram, send the `/newbot` command, and follow the steps to generate your unique `TELEGRAM_BOT_TOKEN`.
2. **Get your Chat ID:** Start a conversation/group with your newly created bot, send any message, and retrieve your `YOUR_TELEGRAM_CHAT_ID` by visiting `https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates` in your browser.

---

## 5. Automation Script Deployment

1. In the Scrypted console, create a new Automation rule.
2. Set the **Trigger** to listen to the native motion detection event of your newly added ONVIF camera.
3. Under the **Actions** section, select **Script** (JavaScript) as the execution block.
4. Copy the contents of the `script.js` file provided in this repository, paste it into the editor, fill in your Telegram credentials, and click **Save**.

---

## 6. Video Recorder Sidecar Deployment (app.py & Dockerfile)

### Step 1: Create the Source Files
In a dedicated local directory (e.g., `~/grabador-telegram`), create your Python backend `app.py` and your configuration `Dockerfile`.

**Dockerfile:**
```dockerfile
FROM python:3.10-slim
RUN apt-get update && apt-get install -y ffmpeg && rm -rf /var/lib/apt/lists/*
RUN pip install flask requests
WORKDIR /app
COPY app.py .
CMD ["python", "app.py"]
```

### Step 2: Set Up the Docker Network Link
To allow the sidecar recorder to safely pull streams from Scrypted without exposing credentials publicly, tie them together inside an internal Docker network bridge:

```bash
# 1. Create a private virtual network bridge
docker network create red-domotica

# 2. Attach your running Scrypted container to this network
docker network connect red-domotica scrypted

# 3. Build your custom Sidecar image from your local directory
docker build -t telegram-recorder .

# 4. Run the Sidecar container attached to the same network bridge
docker run -d --name telegram-recorder --network red-domotica telegram-recorder
```

### 💡 Production Optimization for Raspberry Pi (Disk Protection)
To completely prevent storage hardware degradation from constant input/output video writes, you can configure the temporary files to run purely inside your physical RAM space via Linux's native `/dev/shm` shared memory structure.

1. In your `app.py`, change the video output path line to:
   ```python
   output_path = "/dev/shm/clip.mp4"
   ```
2. Spin up your Docker execution command mounting the shared RAM system volume explicitly:
   ```bash
   docker run -d --name telegram-recorder --network red-domotica -v /dev/shm:/dev/shm telegram-recorder
   ```

---

## 📄 License
This project is open-source software licensed under the MIT License.
