import React, { useState, useEffect } from 'react';
import DialogueList from './DialogueList';

interface DialogueLine {
  id: number;
  text: string;
  translation: string;
  audioUrl: string;
}

interface DialogueComponentProps {
  selectedGame: string;
  selectedLineId: number | null;
  setSelectedLineId: (id: number | null) => void;
}

const DialogueComponent: React.FC<DialogueComponentProps> = ({ selectedGame, selectedLineId, setSelectedLineId }) => {
  const [showTranslation, setShowTranslation] = useState(true);
  const [dialogues, setDialogues] = useState<DialogueLine[]>([]);


  useEffect(() => {
    const fetchDialogues = async () => {
      try {
        const response = await fetch(`/app/api/script.json?game=${selectedGame}`);
        const data = await response.json();
        const formattedData = data.map((item: any) => ({
          id: item.id,
          text: `${item.name}: ${item.dialogue}`,
          translation: item.translation, 
          audioUrl: `/audio/${item.id}.mp3` // Assuming audio files are named by ID
        }));
        setDialogues(formattedData);
      } catch (error) {
        console.error('Error fetching dialogues:', error);
      }
    };

    fetchDialogues();
  }, [selectedGame]);

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