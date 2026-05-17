(async () => {
    // ⚠️ PLACEHOLDERS: Replace these with your actual Telegram Bot Token, Chat ID, and Scrypted Camera ID
    const token = "YOUR_TELEGRAM_BOT_TOKEN";
    const chatId = "YOUR_TELEGRAM_CHAT_ID";
    const cameraId = "YOUR_SCRYPTED_CAMERA_ID"; 

    console.log("[Scrypted Container] Unified pipeline initiated...");

    const camera = systemManager.getDeviceById(cameraId);
    if (!camera) {
        console.log("[Scrypted Container] Error: Camera ID " + cameraId + " not found.");
        return;
    }

    // ==========================================
    // STEP 1: INSTANT SNAPSHOT (NATIVE & FAST)
    // ==========================================
    try {
        console.log("[Scrypted Container] 1/2. Capturing snapshot...");
        const photoMedia = await camera.takePicture();
        const photoBuffer = await mediaManager.convertMediaObjectToBuffer(photoMedia, 'image/jpeg');
        
        const photoForm = new FormData();
        photoForm.append('chat_id', chatId);
        photoForm.append('photo', new Blob([photoBuffer], { type: 'image/jpeg' }), 'snapshot.jpg');
        photoForm.append('caption', '🚨 Motion detected! Snapshot captured. Processing video clip...');

        await fetch(`https://api.telegram.org/bot${token}/sendPhoto`, { method: 'POST', body: photoForm });
        console.log("[Scrypted Container] Snapshot dispatched successfully.");
    } catch (err) {
        console.log("[Scrypted Container] Error in snapshot sub-pipeline: " + err.message);
    }

    // ==========================================
    // STEP 2: ASYNCHRONOUS TRIGGER TO SIDECAR (RAM)
    // ==========================================
    try {
        console.log("[Scrypted Container] 2/2. Triggering video recording container...");
        
        // Fires an async POST request to the sidecar container over the Docker internal network
        fetch('http://telegram-recorder:5000/trigger-video', { method: 'POST' })
            .catch(e => console.log("[Scrypted Container] Asynchronous trigger error: " + e.message));
            
        console.log("[Scrypted Container] Video recorder trigger dispatched.");
    } catch (videoErr) {
        console.log("[Scrypted Container] Failed to communicate with Sidecar container: " + videoErr.message);
    }
})();