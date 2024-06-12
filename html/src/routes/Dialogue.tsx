import React, { useState } from 'react';
import DialogueList from './DialogueList';

const DialogueComponent: React.FC = () => {
  const [selectedLineId, setSelectedLineId] = useState<number | null>(null);
  const [showTranslation, setShowTranslation] = useState(true);

  const dialogues = [
    { id: 1, text: 'Hello', translation: 'Hola', audioUrl: '/audio/hello.mp3' },
    { id: 2, text: 'How are you?', translation: '¿Cómo estás?', audioUrl: '/audio/how_are_you.mp3' },
    // Add more dialogue lines here
  ];

  return (
    <div>
      <label>
        Show Translation:
        <input
          type="checkbox"
          checked={showTranslation}
          onChange={(e) => setShowTranslation(e.target.checked)}
        />
      </label>
      <DialogueList
        dialogues={dialogues}
        selectedLineId={selectedLineId}
        showTranslation={showTranslation}
        onLineSelect={(id) => setSelectedLineId(id)}
      />
    </div>
  );
};

export default DialogueComponent;