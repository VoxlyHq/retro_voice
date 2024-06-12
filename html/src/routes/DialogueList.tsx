import React, { useState, useEffect } from 'react';

interface DialogueLine {
  id: number;
  text: string;
  translation: string;
  audioUrl: string;
}

interface DialogueListProps {
  dialogues: DialogueLine[];
  selectedLineId: number | null;
  showTranslation: boolean;
  onLineSelect: (id: number) => void;
}

const DialogueList: React.FC<DialogueListProps> = ({ dialogues, selectedLineId, showTranslation, onLineSelect }) => {
  const [currentAudio, setCurrentAudio] = useState<HTMLAudioElement | null>(null);

  useEffect(() => {
    if (selectedLineId !== null) {
      const selectedDialogue = dialogues.find(dialogue => dialogue.id === selectedLineId);
      if (selectedDialogue && selectedDialogue.audioUrl) {
        playAudio(selectedDialogue.audioUrl);
      }
    }
  }, [selectedLineId, dialogues]);

  const playAudio = (audioUrl: string) => {
    if (currentAudio) {
      currentAudio.pause();
    }
    const audio = new Audio(audioUrl);
    audio.play();
    setCurrentAudio(audio);
  };

  return (
    <div>
      {dialogues.map(dialogue => (
        <div
          key={dialogue.id}
          style={{
            padding: '10px',
            backgroundColor: selectedLineId === dialogue.id ? 'lightyellow' : 'white',
            border: selectedLineId === dialogue.id ? '2px solid orange' : '1px solid gray',
            borderRadius: '5px',
            marginBottom: '10px',
            display: 'flex',
            alignItems: 'center'
          }}
        >
          <div style={{ flexGrow: 1 }}>
            <p style={{ margin: 0 }}>{dialogue.text}</p>
            {showTranslation && <p style={{ margin: 0, fontStyle: 'italic', color: 'gray' }}>{dialogue.translation}</p>}
          </div>
          <button onClick={() => onLineSelect(dialogue.id)}>Play</button>
        </div>
      ))}
    </div>
  );
};

export default DialogueList;