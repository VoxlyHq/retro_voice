document.getElementById('captureBtn').addEventListener('click', async () => {
    try {
        // Request screen capture
        const captureStream = await navigator.mediaDevices.getDisplayMedia({video: true});

        // Assuming you want to capture the full screen at a reasonable frame rate
        const videoTrack = captureStream.getVideoTracks()[0];
        const imageCapture = new ImageCapture(videoTrack);
        const canvas = document.createElement('canvas');
        const ctx = canvas.getContext('2d');

        // Set canvas size to match the video stream
        const settings = videoTrack.getSettings();
        canvas.width = settings.width;
        canvas.height = settings.height;

        // Function to capture and send the image
        const captureAndSend = async () => {
            const bitmap = await imageCapture.grabFrame();
            ctx.drawImage(bitmap, 0, 0, canvas.width, canvas.height);
            canvas.toBlob(async (blob) => {
                const formData = new FormData();
                formData.append('image', blob, 'screenshot.png');

                // Post the image blob to your server
                await fetch('http://localhost:8000/upload_screenshot', {
                    method: 'POST',
                    body: formData,
                });
            }, 'image/png');
        };

        // Capture and send the image every second
        setInterval(captureAndSend, 1000);

    } catch (err) {
        console.error('Error: ', err);
    }
});
