import React, { useEffect, useRef, forwardRef } from 'react';

const VideoWithAnnotations = forwardRef(({ annotationsData }, videoRef) => {
  const videoContainerRef = useRef(null);

  useEffect(() => {
    const videoContainer = videoContainerRef.current;

    // Remove existing annotations
    const oldAnnotations = videoContainer.querySelectorAll('.annotation');
    oldAnnotations.forEach(annotation => annotation.remove());

    // Function to add annotation divs
    const addAnnotationDiv = (pos, text, className) => {
      const [x, y] = pos;
      const div = document.createElement('div');
      div.className = `annotation ${className}`;
      div.style.left = `${x}px`;
      div.style.top = `${y}px`;
      div.innerText = text;
      videoContainer.appendChild(div);
    };

    // Add new annotations
    annotationsData.annotations.forEach(({ pos, text }) => {
      addAnnotationDiv(pos, text, 'foreign-text');
    });

    annotationsData.debug_bbox.forEach(({ pos, text }) => {
      addAnnotationDiv(pos, text, 'debug-text');
    });

    annotationsData.translations.forEach(({ pos, text }) => {
      addAnnotationDiv(pos, text, 'translation-text');
    });
  }, [annotationsData]);

  return (
    <div ref={videoContainerRef} style={{ position: 'relative', display: 'inline-block' }}>
      <video ref={videoRef} width="960" height="540" controls autoPlay>
        <source src="your-video.mp4" type="video/mp4" />
        Your browser does not support the video tag.
      </video>
    </div>
  );
});

VideoWithAnnotations.displayName = 'VideoWithAnnotations';

export default VideoWithAnnotations;