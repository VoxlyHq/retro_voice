document.getElementById('captureBtn').addEventListener('click', async () => {
    try {
        const captureStream = await navigator.mediaDevices.getDisplayMedia({video: true});
        const videoTrack = captureStream.getVideoTracks()[0];
        const imageCapture = new ImageCapture(videoTrack);

        // Function to capture and upload image
        async function captureAndUpload() {
            try {
                const imageBitmap = await imageCapture.grabFrame();
                const canvas = document.createElement('canvas');
                canvas.width = imageBitmap.width;
                canvas.height = imageBitmap.height;
                const ctx = canvas.getContext('2d');
                ctx.drawImage(imageBitmap, 0, 0, canvas.width, canvas.height);
                canvas.toBlob(async (blob) => {
                    const formData = new FormData();
                    formData.append('image', blob, 'screenshot.png');

                    // Await the fetch to ensure it finishes before continuing
                    await fetch('/upload_screenshot', {
                        method: 'POST',
                        body: formData,
                    }).then(response => {
                        if (!response.ok) {
                            throw new Error('Network response was not ok');
                        }
                        console.log('Image uploaded successfully');
                    }).catch(error => {
                        console.error('There has been a problem with your fetch operation:', error);
                    });

                    // Wait for 1 second to pass before capturing and uploading the next image
                    setTimeout(captureAndUpload, 1000);
                }, 'image/png');
            } catch (error) {
                console.error('Error capturing or uploading image:', error);
            }
        }

        // Start the capture and upload process
        captureAndUpload();
    } catch (err) {
        console.error('Error: ', err);
    }
});
