from pathlib import Path
from PIL import Image
from collections import defaultdict
import matplotlib.pyplot as plt
import sys
import os
import time

parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(parent_dir)

class Dataset:
    def __init__(self, folder_path, text_detector=None):
        self.folder_path = Path(folder_path)
        self.image_files = [i for i in self.folder_path.iterdir() if i.is_file()]
        self.metadata = self._extract_metadata()
        self.text_detector = text_detector 
    
    def _extract_metadata(self):
        metadata = []
        for image_file in self.image_files:
            filename = image_file.stem
            name_of_game, lang, number = filename.split("_")
            metadata.append((name_of_game, lang, number))
        return metadata
    
    def __getitem__(self, idx):
        image_path = self.image_files[idx]
        image = Image.open(image_path).convert('RGB')
        name_of_game, lang, number = self.metadata[idx]
        return image, name_of_game, lang, number
    
    def __len__(self):
        return len(self.image_files)
    
    def stats(self):
        dataset_size = len(self)
        game_counter = defaultdict(int)
        lang_counter = defaultdict(int)

        for name_of_game, lang, _ in self.metadata:
            game_counter[name_of_game] += 1
            lang_counter[lang] += 1
        
        return dataset_size, dict(game_counter), dict(lang_counter)
    
    def plot_stats(self, dialogue_stats, no_dialogue_stats, title, xlabel, ylabel):
        categories = list(dialogue_stats.keys())
        dialogue_counts = [dialogue_stats.get(category, 0) for category in categories]
        no_dialogue_counts = [no_dialogue_stats.get(category, 0) for category in categories]

        plt.figure(figsize=(10, 5))
        plt.bar(categories, dialogue_counts, label='Dialogue')
        plt.bar(categories, no_dialogue_counts, bottom=dialogue_counts, label='No Dialogue')
        plt.title(title)
        plt.xlabel(xlabel)
        plt.ylabel(ylabel)
        plt.xticks(rotation=45)
        plt.legend()
        plt.tight_layout()
        plt.show()

    def dialogue_stats(self):
        if self.text_detector is None:
            print("No Text Detector provided, skipping dialogue statistics calculation.")
            return None, None
        
        start_time = time.time()
        game_dialogue_counter = defaultdict(int)
        game_no_dialogue_counter = defaultdict(int)
        lang_dialogue_counter = defaultdict(int)
        lang_no_dialogue_counter = defaultdict(int)

        for idx, (name_of_game, lang, number) in enumerate(self.metadata):
            image, _, _, _ = self.__getitem__(idx)
            if self.text_detector.has_text(image):
                game_dialogue_counter[name_of_game] += 1
                lang_dialogue_counter[lang] += 1
            else:
                game_no_dialogue_counter[name_of_game] += 1
                lang_no_dialogue_counter[lang] += 1

        end_time = time.time()
        print(f"Time taken to calculate dialogue stats: {end_time - start_time:.2f} seconds")

        return (dict(game_dialogue_counter), dict(game_no_dialogue_counter)), (dict(lang_dialogue_counter), dict(lang_no_dialogue_counter))
    
    def get_images_by_dialogue_status(self, dialogue=True, max_images=10):
        if self.text_detector is None:
            print("No Text Detector provided, skipping dialogue detection.")
            return None
        
        selected_images = []
        for idx in range(len(self.image_files)):
            if len(selected_images) >= max_images:
                break
            image, name_of_game, lang, number = self.__getitem__(idx)
            has_text = self.text_detector.has_text(image)
            if dialogue and has_text:
                selected_images.append((image, name_of_game, lang, number))
            elif not dialogue and not has_text:
                selected_images.append((image, name_of_game, lang, number))
        return selected_images

def display_images(images, title):
    num_images = len(images)
    cols = 5
    rows = (num_images // cols) + int(num_images % cols > 0)
    fig, axes = plt.subplots(rows, cols, figsize=(15, 3 * rows))
    fig.suptitle(title, fontsize=16)

    for i, (image, name_of_game, lang, number) in enumerate(images):
        ax = axes[i // cols, i % cols]
        ax.imshow(image)
        ax.set_title(f"{name_of_game}_{lang}_{number}")
        ax.axis('off')

    for i in range(len(images), rows * cols):
        fig.delaxes(axes[i // cols, i % cols])

    plt.tight_layout()
    plt.subplots_adjust(top=0.95)
    plt.show()

if __name__ == "__main__":
    from text_detector_fast import TextDetectorFast
    textDetector = TextDetectorFast("weeeee", checkpoint="pretrained/fast_base_tt_640_finetune_ic17mlt.pth")

    folder_path = 'eval_data/'
    dataset = Dataset(folder_path, textDetector)

    image, name_of_game, lang, number = dataset[3]

    dataset_size, game_stats, lang_stats = dataset.stats()
    print(f"Dataset size: {dataset_size}")
    print("Game breakdown:", game_stats)
    print("Language breakdown:", lang_stats)

    # Displaying an example image
    plt.imshow(image)
    plt.title(f"Name of Game: {name_of_game}, Language: {lang}, Number: {number}")
    plt.axis('off')
    plt.show()

    # Dialogue statistics
    dialogue_stats = dataset.dialogue_stats()
    if dialogue_stats[0] is not None and dialogue_stats[1] is not None:
        (game_dialogue_stats, game_no_dialogue_stats), (lang_dialogue_stats, lang_no_dialogue_stats) = dialogue_stats
        print("Game Dialogue breakdown:", game_dialogue_stats)
        print("Game No Dialogue breakdown:", game_no_dialogue_stats)
        print("Language Dialogue breakdown:", lang_dialogue_stats)
        print("Language No Dialogue breakdown:", lang_no_dialogue_stats)

        # Plotting dialogue statistics for games
        dataset.plot_stats(game_dialogue_stats, game_no_dialogue_stats, "Breakdown of Images by Game (Dialogue vs No Dialogue)", "Game", "Number of Images")

        # Plotting dialogue statistics for languages
        dataset.plot_stats(lang_dialogue_stats, lang_no_dialogue_stats, "Breakdown of Images by Language (Dialogue vs No Dialogue)", "Language", "Number of Images")
    else:
        print("Dialogue statistics were not calculated.")

    # Displaying 10 dialogue images
    dialogue_images = dataset.get_images_by_dialogue_status(dialogue=True, max_images=10)
    if dialogue_images:
        display_images(dialogue_images, "Dialogue Images")

    # Displaying 10 non-dialogue images
    non_dialogue_images = dataset.get_images_by_dialogue_status(dialogue=False, max_images=10)
    if non_dialogue_images:
        display_images(non_dialogue_images, "Non-Dialogue Images")