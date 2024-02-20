from google.cloud import vision
import io
from PIL import Image, ImageDraw

def detect_text_google(path):
    """Detects text in the file."""
    client = vision.ImageAnnotatorClient()

    with io.open(path, 'rb') as image_file:
        content = image_file.read()

    image = vision.Image(content=content)

    response = client.text_detection(image=image)
    texts = response.text_annotations

    print('Texts:')

    for text in texts:
        print('\n"{}"'.format(text.description))

        vertices = (['({},{})'.format(vertex.x, vertex.y)
                     for vertex in text.bounding_poly.vertices])

        print('bounds: {}'.format(','.join(vertices)))

    if response.error.message:
        raise Exception(
            '{}\nFor more info on error messages, check: '
            'https://cloud.google.com/apis/design/errors'.format(
                response.error.message))

def detect_text_and_draw_boxes(image_path):
    """Detects text in the image file and draws boxes around the text."""
    client = vision.ImageAnnotatorClient()

    with io.open(image_path, 'rb') as image_file:
        content = image_file.read()

    image = vision.Image(content=content)
    response = client.text_detection(image=image)
    texts = response.text_annotations

    if texts:
        # Load the original image to draw on
        img = Image.open(image_path)
        draw = ImageDraw.Draw(img)

        # Draw boxes around each text detection
        for text in texts[1:]:  # Skip the first element, which is the overall image text
            vertices = [(vertex.x, vertex.y) for vertex in text.bounding_poly.vertices]
            draw.polygon(vertices, outline='red')

        # Save or display the modified image
        img.save('output_image.jpg')
        img.show()

    if response.error.message:
        raise Exception(
            '{}\nFor more info on error messages, check: '
            'https://cloud.google.com/apis/design/errors'.format(
                response.error.message))



if __name__ == "__main__":
    # Replace 'path/to/your/image/file.jpg' with the path to your image file
    detect_text_and_draw_boxes('window_capture.jpg')
    # Replace the path below with the path to your image file
    #detect_text('window_capture.jpg')
