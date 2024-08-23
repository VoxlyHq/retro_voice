import numpy as np
from PIL import Image, ImageOps, ImageEnhance
from diskcache import Cache
from imagehash import phash, average_hash, dhash, whash
import difflib

class OCRCache:
    def __init__(self, cache_dir='./ocr_cache', max_cache_size=1e9, hash_method='average', threshold=0):
        self.cache = Cache(cache_dir, size_limit=int(max_cache_size))
        self.threshold = threshold

        # Select the hashing function based on the user's choice
        self.hash_function = {
            'average': average_hash,
            'phash': phash,
            'dhash': dhash,
            'whash': whash
        }.get(hash_method, average_hash)

    def _apply_preprocessing(self, image, preprocess_steps):
        for step, params in preprocess_steps:
            if step == 'resize':
                image = image.resize(params)
            elif step == 'grayscale':
                image = ImageOps.grayscale(image)
            elif step == 'normalize':
                image_data = np.array(image).astype(np.float32)
                image = Image.fromarray(((image_data - np.min(image_data)) / (np.max(image_data) - np.min(image_data)) * 255).astype(np.uint8))
            elif step == 'contrast':
                enhancer = ImageEnhance.Contrast(image)
                image = enhancer.enhance(params)
            elif step == 'threshold':
                image = image.point(lambda p: p > params and 255)
        return image

    def _hash_distance(self, hash1, hash2):
        return np.count_nonzero(np.frombuffer(hash1.hash, dtype=np.uint8) != np.frombuffer(hash2.hash, dtype=np.uint8))

    def _find_closest_hash(self, target_hash):
        min_distance = float('inf')
        closest_hash = None
        for cached_hash in self.cache.iterkeys():
            distance = self._hash_distance(target_hash, cached_hash)
            if distance < min_distance and distance <= self.threshold:
                min_distance = distance
                closest_hash = cached_hash
        return closest_hash

    def get_cached_ocr(self, image, preprocess_steps):
        # Apply preprocessing steps
        processed_image = self._apply_preprocessing(image, preprocess_steps)
        
        # Compute hash of the processed image
        image_hash = self.hash_function(processed_image)
        
        # Find if there's a similar hash in the cache
        if self.threshold == 0:
            cached_text = self.cache.get(image_hash)
        else:
            closest_hash = self._find_closest_hash(image_hash)
            cached_text = self.cache.get(closest_hash) if closest_hash else None
        
        return cached_text

    def cache_ocr(self, image, ocr_text, preprocess_steps):
        # Apply preprocessing steps
        processed_image = self._apply_preprocessing(image, preprocess_steps)
        
        # Compute hash of the processed image
        image_hash = self.hash_function(processed_image)
        
        # Cache the OCR result
        self.cache.set(image_hash, ocr_text)

    def clear_cache(self):
        self.cache.clear()

    def close(self):
        self.cache.close()

class TranscriptCache:
    def __init__(self, transcript_lines, cache_dir='./transcript_cache', max_cache_size=1e9):
        self.cache = Cache(cache_dir, size_limit=int(max_cache_size))
        self.transcript_lines = transcript_lines

    def _find_best_match(self, ocr_text):
        """Find the best match for the OCR output in the transcript using difflib."""
        match = difflib.get_close_matches(ocr_text, self.transcript_lines, n=1, cutoff=0.5)
        if match:
            return match[0]
        return None

    def get_cached_transcript(self, ocr_text):
        # Check if the OCR text is already cached
        cached_match = self.cache.get(ocr_text)
        if cached_match:
            return cached_match
        
        # Find the best match in the transcript
        best_match = self._find_best_match(ocr_text)
        if best_match:
            # Cache the matched transcript text
            self.cache.set(ocr_text, best_match)
        return best_match

    def cache_transcript(self, ocr_text, matched_transcript):
        self.cache.set(ocr_text, matched_transcript)

    def clear_cache(self):
        self.cache.clear()

    def close(self):
        self.cache.close()

class TranslationCache:
    def __init__(self, cache_dir='./translation_cache', max_cache_size=1e9, default_target_language='en'):
        self.cache = Cache(cache_dir, size_limit=int(max_cache_size))
        self.default_target_language = default_target_language

    def _generate_cache_key(self, sentence, target_language):
        # Create a unique cache key based on the sentence and target language
        return f"{sentence}::{target_language}"

    def get_cached_translation(self, sentence, target_language=None):
        if target_language is None:
            target_language = self.default_target_language
        cache_key = self._generate_cache_key(sentence, target_language)
        return self.cache.get(cache_key)

    def cache_translation(self, sentence, translation, target_language=None):
        if target_language is None:
            target_language = self.default_target_language
        cache_key = self._generate_cache_key(sentence, target_language)
        self.cache.set(cache_key, translation)

    def clear_cache(self):
        self.cache.clear()

    def close(self):
        self.cache.close()
    

# Example Usage without Context Manager
if __name__ == "__main__":
    # Sample transcript lines
    transcript_lines = [
        "Cecil: I received it on Mt. Ordeals.",
        "One to be born from a dragon hoisting the light and the dark...",
        "Elder: I do not know what it is nor do I know what the legend means...",
        "Palom: Thanks, old man! Porom: Calm down! And let's go!"
    ]

    # Initialize the caches
    ocr_cache = OCRCache(cache_dir='./ocr_cache', hash_method='phash', threshold=5)
    transcript_cache = TranscriptCache(transcript_lines, cache_dir='./transcript_cache')

    # Define preprocessing steps
    preprocess_steps = [('grayscale', None), ('resize', (200, 200)), ('contrast', 1.5)]

    # Load your image
    image = Image.open("sample_image.png")

    # Try to retrieve cached OCR result
    cached_text = ocr_cache.get_cached_ocr(image, preprocess_steps)
    if not cached_text:
        # Perform OCR if not cached (assuming a dummy OCR function here)
        ocr_text = "Cecil: I received it on Mt. Ordeals."
        ocr_cache.cache_ocr(image, ocr_text, preprocess_steps)
        cached_text = ocr_text

    # Now match OCR text with the transcript using the TranscriptCache
    matched_transcript = transcript_cache.get_cached_transcript(cached_text)
    if matched_transcript:
        print(f"Matched Transcript: {matched_transcript}")
    else:
        print("No matching transcript found.")

    # Close the caches when done
    ocr_cache.close()
    transcript_cache.close()

    # Initialize the TranslationCache with a default target language
    translation_cache = TranslationCache(default_target_language='es')  # Default to Spanish

    # Sample sentence and its translation
    sentence = "Hello, how are you?"
    translation = "Hola, ¿cómo estás?"

    # Cache the translation
    translation_cache.cache_translation(sentence, translation, target_language='es')

    # Retrieve the cached translation
    cached_translation = translation_cache.get_cached_translation(sentence, target_language='es')
    if cached_translation:
        print(f"Cached Translation: {cached_translation}")
    else:
        print("No cached translation found.")

    # Close the cache when done
    translation_cache.close()
