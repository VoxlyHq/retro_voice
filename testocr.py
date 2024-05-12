import matplotlib.pyplot as plt
from PIL import Image
from doctr.models import detection_predictor

def detect_text(image_path):
    # Load the image with PIL
    image = Image.open(image_path)

    # Convert the image to RGB
    image = image.convert("RGB")

    # Load doctr predictor for text detection
    predictor = detection_predictor("db_resnet50")

    # Perform text detection
    result = predictor([image])

    # Display results
    for page in result.pages:
        for block in page.blocks:
            print(f"Text Block: {block.geometry}")
            for line in block.lines:
                for word in line.words:
                    print(f"Word: {word.value}, Confidence: {word.confidence}, Bounding Box: {word.geometry}")

    # Optional: visualize the result
    fig = result.show(doc=[image])
    plt.show()

if __name__ == "__main__":
    # Path to your image file
    image_path = 'ff2_en_1.png'
    detect_text(image_path)
