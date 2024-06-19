import React, { useEffect, useRef, forwardRef } from 'react';

const VideoWithAnnotations = forwardRef(({ annotations }, videoRef) => {
  const videoContainerRef = useRef(null);

  useEffect(() => {
    const videoContainer = videoContainerRef.current;

    // Remove existing annotations
    debugger;
    while (videoContainer.firstChild && videoContainer.firstChild.nodeName === 'DIV') {
      videoContainer.removeChild(videoContainer.firstChild);
    }

    // Add new annotations
    annotations.forEach((annotation) => {
      const coords = annotation[0];
      const text = annotation[1];

      const x = coords[0][0];
      const y = coords[0][1];
      const width = coords[1][0] - coords[0][0];
      const height = coords[2][1] - coords[0][1];

      const div = document.createElement('div');
      div.className = 'annotation';
      div.style.left = `${x}px`;
      div.style.top = `${y}px`;
      div.style.width = `${width}px`;
      div.style.height = `${height}px`;
      div.innerText = text;

      videoContainer.appendChild(div);
    });
  }, [annotations]);

  return (
    <div ref={videoContainerRef} style={{ position: 'relative', display: 'inline-block' }}>
      <video id="video" width="960" height="540" ref={videoRef} autoPlay playsInline></video>
    </div>
  );
});

VideoWithAnnotations.displayName = 'VideoWithAnnotations';

export default VideoWithAnnotations;