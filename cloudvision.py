from google.cloud import vision
import io
from PIL import Image, ImageDraw
import json

def detect_text_google(path):
    """Detects text in the file."""
    client = vision.ImageAnnotatorClient()

    with io.open(path, 'rb') as image_file:
        content = image_file.read()

    image = vision.Image(content=content)

    response = client.text_detection(image=image)
    texts = response.text_annotations

    detected_texts = []
    print('Texts:')

    for text in texts:
        print('\n"{}"'.format(text.description))

        vertices = (['({},{})'.format(vertex.x, vertex.y)
                     for vertex in text.bounding_poly.vertices])

        print('bounds: {}'.format(','.join(vertices)))
        detected_texts.append(text.description)

    if response.error.message:
        raise Exception(
            '{}\nFor more info on error messages, check: '
            'https://cloud.google.com/apis/design/errors'.format(
                response.error.message))
    
    return detected_texts


# Initialize a counter for the output image file names
image_counter = 0

def detect_text_and_draw_boxes(image_path):
    """Detects text in the image file and draws boxes around the text."""
    global image_counter  # Use the global counter
    client = vision.ImageAnnotatorClient()

    with io.open(image_path, 'rb') as image_file:
        content = image_file.read()

    image = vision.Image(content=content)
    response = client.text_detection(image=image)
    texts = response.text_annotations

    detected_texts = []
    print('Texts:')

    if texts:
        # Increment the image counter for each invocation
        output_image_filename = f'output_image_{image_counter}.jpg'
        output_json_filename = f'detected_texts_{image_counter}.json'
        image_counter += 1

        # Load the original image to draw on
        img = Image.open(image_path)
        draw = ImageDraw.Draw(img)

        # Draw boxes around each text detection
        for text in texts[1:]:  # Skip the first element, which is the overall image text
            vertices = [(vertex.x, vertex.y) for vertex in text.bounding_poly.vertices]
            draw.polygon(vertices, outline='red')
            detected_texts.append(text.description)

        # Save the modified image with a unique name
        img.save(output_image_filename) 
        print(f'Modified image saved as {output_image_filename}')

        # Write detected texts to a JSON file
        with open(output_json_filename, 'w') as json_file:
            json.dump(detected_texts, json_file)
        print(f'Detected texts saved to {output_json_filename}')

    if response.error.message:
        raise Exception(
            '{}\nFor more info on error messages, check: '
            'https://cloud.google.com/apis/design/errors'.format(
                response.error.message))

    return detected_texts

if __name__ == "__main__":
    # Replace 'path/to/your/image/file.jpg' with the path to your image file
    detect_text_and_draw_boxes('window_capture.jpg')
    # Replace the path below with the path to your image file
    #detect_text('window_capture.jpg')
