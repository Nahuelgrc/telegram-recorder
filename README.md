# Tapo C200 Security Pipeline: Scrypted + Docker Sidecar + Telegram

This repository contains a production-ready architectural solution optimized for automating security alerts (Instant Snapshot + 5-second Video Clip) triggered by motion events from **TP-Link Tapo C200** cameras (or any ONVIF-compatible camera).

The solution is specifically designed for resource-constrained environments (like a **Raspberry Pi**), keeping CPU usage close to **0% at rest** and protecting physical storage against continuous write wear and tear by leveraging RAM storage.

---

## 🏗️ System Architecture

To bypass expensive video processing analytics and commercial paid NVR modules, a **Sidecar Pattern** was implemented using an isolated Python microservice that interacts privately with the free Scrypted core.

```
[ Tapo C200 ] --- (Hardware Detection / ONVIF Webhook) ---> [ Scrypted Container ]
                                                                       |
                                         +-----------------------------+
                                         | (Immediate Action)          | (Async POST Trigger)
                                         v                             v
                                  [ Telegram API ]             [ telegram-recorder ] (Sidecar)
                                  📸 Send Snapshot                     |
                                                                       |-- Capture RTSP from Scrypted
                                                                       |-- Hybrid Muxing with FFmpeg
                                                                       v
                                                                [ Telegram API ]
                                                                📹 Send Video Clip (.mp4)
```

### Key Architectural Strengths:
1. **Native Hardware Detection (0% CPU):** Scrypted does not analyze pixels via software; it subscribes to the camera's ONVIF webhook. The CPU impact on the host is zero.
2. **Minimal Snapshot Latency:** The Action Script inside Scrypted dispatches the snapshot to Telegram instantly when the event is triggered.
3. **Concurrent Stream Bypass:** The Sidecar recorder does not overload the camera by requesting a second video stream; it hooks into the *RTSP Rebroadcast* that Scrypted already keeps open in memory.
4. **Lightweight Hybrid Muxing:** FFmpeg performs a direct copy of the H.264 video stream (0% CPU) and only transcodes the PCM audio to AAC to ensure native playback compatibility on mobile devices and Telegram.

---

## 📁 Suggested Repository Structure

* `app.py`: Code for the Python Flask server exposing the recording and dispatch microservice.
* `script.js`: JavaScript code (Async/Await) to configure inside the Scrypted automation engine.
* `Dockerfile`: Docker image build recipe for the video recorder.
* `README.md`: This guide file.

---

## 🛠️ Deployment & Installation Guide

### 1. Local Environment and Files
Create a dedicated folder on your server or development computer (e.g., `C:\grabador-telegram` or `~/grabador-telegram`) and place the `app.py` and the following `Dockerfile` there:

```dockerfile
FROM python:3.10-slim
RUN apt-get update && apt-get install -y ffmpeg && rm -rf /var/lib/apt/lists/*
RUN pip install flask requests
WORKDIR /app
COPY app.py .
CMD ["python", "app.py"]
```

> ⚠️ **Important:** Make sure to configure the corresponding environment variables or constants for your **Telegram Token**, **Chat ID**, and the internal Scrypted **RTSP URL** inside your `app.py`.

### 2. Virtual Network and Container Configuration
Run the following sequence of commands in your terminal to build the image and establish the internal Docker DNS communication bridge:

```bash
# Create the private Docker virtual network
docker network create red-domotica

# Connect your existing Scrypted container to the new network
# (Change 'scrypted' to your container's real name if it differs)
docker network connect red-domotica scrypted

# Build the local Sidecar recorder image
docker build -t telegram-recorder .

# Initialize the Sidecar container integrated into the network
docker run -d --name telegram-recorder --network red-domotica telegram-recorder
```

### 3. Device Configuration in Scrypted
1. Add the camera using the native **ONVIF** plugin. This allows receiving hardware motion triggers from the Tapo.
2. Go to the **Streams** tab -> **Stream: Mainstream**.
3. In the **RTSP Parser** option, select **`FFmpeg (TCP)`**. This ensures immunity against Wi-Fi micro-drops and prevents green artifacts in the stream.
4. Copy the URL listed under **RTSP Rebroadcast Url** (e.g., `rtsp://localhost:36375/XXXXX`). In your `app.py`, use this exact URL, replacing the word `localhost` with `scrypted` (so Docker can resolve the internal DNS).

### 4. Setting up the Automation
1. In Scrypted, create a new automation whose *Trigger* is the camera's ONVIF motion event.
2. In the *Actions* section, add a **Script** (JavaScript) block.
3. Paste the code from your `script.js` file.
4. Save changes.

---

## 💾 Production Configuration for Raspberry Pi (Disk Protection)

To avoid premature wear of the SD card or SSD drive on a Raspberry Pi due to constant video writing and deleting, it is highly recommended to use the native Linux shared memory RAM filesystem (`/dev/shm`).

1. In the `app.py` file, modify the temporary file path to point to the shared RAM:
   ```python
   output_path = "/dev/shm/clip.mp4"
   ```
2. When starting the Docker container, mount the physical RAM volume by adding the `-v /dev/shm:/dev/shm` flag:
   ```bash
   docker run -d --name telegram-recorder --network red-domotica -v /dev/shm:/dev/shm telegram-recorder
   ```

---

## 📄 License
This project is distributed under the MIT License. Feel free to use, modify, and adapt it to your home automation infrastructure.
