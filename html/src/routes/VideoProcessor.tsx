import React, { useEffect, useRef } from 'react';

const VideoProcessor = ({ videoStream, cropHeight }) => {
  const videoRef = useRef(null);
  const canvasRef = useRef(null);

  useEffect(() => {
    if (!videoStream) return;

    const video = videoRef.current;
    video.srcObject = videoStream;

    const canvas = document.createElement('canvas');
    const context = canvas.getContext('2d');

    const videoTrack = videoStream.getVideoTracks()[0];
    const processor = new MediaStreamTrackProcessor({ track: videoTrack });
    const generator = new MediaStreamTrackGenerator({ kind: 'video' });

    const reader = processor.readable.getReader();
    const writer = generator.writable.getWriter();

    const { width, height } = videoTrack.getSettings();
    const cropHeightInt = parseInt(cropHeight, 10);
    canvas.width = width;
    canvas.height = height - cropHeightInt; // Subtract the specified crop height from the height

    const processFrames = async () => {
      while (true) {
        const { done, value: frame } = await reader.read();
        if (done) {
          writer.close();
          return;
        }

        // Convert the VideoFrame to an ImageBitmap
        const bitmap = await createImageBitmap(frame);

        // Draw the ImageBitmap onto the canvas, cropping the specified number of pixels from the top
        context.drawImage(bitmap, 0, cropHeightInt, width, height - cropHeightInt, 0, 0, width, height - cropHeightInt);

        // Create a new VideoFrame from the canvas
        const croppedFrame = new VideoFrame(canvas, { timestamp: frame.timestamp });

        // Write the cropped frame to the generator
        await writer.write(croppedFrame);

        // Close the frame and bitmap to release resources
        frame.close();
        bitmap.close();
        croppedFrame.close();
      }
    };

    processFrames();

    // Create a new stream from the generator and set it as the source for the video element
    const processedStream = new MediaStream([generator]);
    video.srcObject = processedStream;

    return () => {
      reader.cancel();
      writer.close();
      video.srcObject = null;
    };
  }, [videoStream, cropHeight]);

  return (
    <div>
      <video ref={videoRef} autoPlay playsInline />
      <canvas ref={canvasRef} style={{ display: 'none' }} />
    </div>
  );
};

export default VideoProcessor;