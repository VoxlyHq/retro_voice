import numpy as np
from PIL import Image
from doctr.models import detection_predictor
import matplotlib.pyplot as plt

def detect_text(image_path):
    # Load the image with PIL
    image = Image.open(image_path)

    # Convert the image to RGB
    image = image.convert("RGB")

    # Convert the image to a NumPy array
    image_np = np.array(image)

    # Load doctr predictor for text detection
    predictor = detection_predictor("db_resnet50")

    # Perform text detection
    results = predictor([image_np])  # This returns a list of dictionaries

    # Since we are processing one image, we can directly access the first result
    result = results[0]

    # Display results
    for block in result['blocks']:
        print(f"Text Block: {block['geometry']}")
        for line in block['lines']:
            for word in line['words']:
                print(f"Word: {word['value']}, Confidence: {word['confidence']}, Bounding Box: {word['geometry']}")

    # Optional: visualize the result
    # Let's assume we have a visualization function in doctr
    fig, ax = plt.subplots(1, 1, figsize=(12, 8))
    doctr.visualize.show_results(image_np, result, ax=ax)
    plt.show()

if __name__ == "__main__":
    # Path to your image file
    image_path = 'path_to_your_image.jpg'
    detect_text(image_path)
