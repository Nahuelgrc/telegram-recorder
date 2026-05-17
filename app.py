import subprocess
import os
import requests
from flask import Flask

app = Flask(__name__)

# ⚠️ PLACEHOLDERS: Replace these with your actual credentials or configure environment variables
TELEGRAM_TOKEN = "YOUR_TELEGRAM_BOT_TOKEN"
CHAT_ID = "YOUR_TELEGRAM_CHAT_ID"
# Replace with your Scrypted internal RTSP rebroadcast URL (using 'scrypted' container name as host)
RTSP_URL = "rtsp://scrypted:36375/YOUR_STREAM_HASH"

@app.route('/trigger-video', methods=['POST'])
def trigger_video():
    # Temporary video path inside the container. 
    # NOTE: Change to "/dev/shm/clip.mp4" on a Raspberry Pi to use RAM disk and prevent storage wear.
    output_path = "/tmp/clip.mp4"
    
    try:
        print("[Sidecar-Recorder] Trigger received. Starting 5-second video capture...", flush=True)
        
        # Hybrid Muxing: Direct stream copy for video (0% CPU) + transcode audio to AAC for native Telegram playback
        cmd = f"ffmpeg -y -rtsp_transport tcp -i {RTSP_URL} -t 5 -c:v copy -c:a aac {output_path}"
        
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode != 0:
            raise Exception(f"FFmpeg pipeline failed. Details: {result.stderr}")
        
        print("[Sidecar-Recorder] FFmpeg execution successful. Dispatching video to Telegram...", flush=True)
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendVideo"
        
        with open(output_path, 'rb') as video_file:
            response = requests.post(
                url, 
                data={'chat_id': CHAT_ID, 'caption': '📹 Motion event video clip.'}, 
                files={'video': video_file}
            )
            print(f"[Sidecar-Recorder] Telegram API response: {response.text}", flush=True)
            
        os.remove(output_path)
        return {"status": "success"}, 200
        
    except Exception as e:
        if os.path.exists(output_path):
            os.remove(output_path)
        error_msg = f"CRITICAL ERROR: {str(e)}"
        print(error_msg, flush=True)
        return {"status": "error", "message": error_msg}, 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)