from flask import Flask, request
import time
from urllib.parse import urlparse
from PIL import Image
import base64
import io
import json

app = Flask(__name__)

def load_image(image_data):
    if type(image_data) == Image.Image:
        return image_data
    byte_data = base64.b64decode(image_data)
    image = Image.open(io.BytesIO(byte_data))
    image = image.convert("RGB")
    return image

@app.route("/", methods=["GET"])
def index():
    return """
    <html>
        <head><title></title></head>
        <body>Hello, Retroarch AI Backend</body>
    </html>
    """

@app.route("/", methods=["POST"])
def process_request():
    start_time = time.time()

    print('URL : ', end = '\t')
    print(request.url)

    query = urlparse(request.url).query
    print('query :\t', query)

    if query:
        output_format = query.split('=')[1].split(',')

    print('output_format:\t', output_format)

    data = request.get_data()
    data = json.loads(data)

    result = _process_request(data, output_format)
    print('Request took: ', time.time() - start_time)

    if result.get('text', None):
        print('result:\t', result['text'])

    output = json.dumps(result)

    response = app.response_class(
        response=output,
        status=200,
        mimetype='application/json'
    )

    return response

def _process_request(body, query):

    image_data = body.get("image")

    image = load_image(image_data)

    image.save('tmp_input.jpg')

    place_holder_text_strings = ["PLACEHOLDER 1"]

    return_output = {"text" : place_holder_text_strings[0], "auto" : "auto"}
    return return_output

if __name__ == "__main__":
    local_server_host = "localhost"
    local_server_port = 4404

    app.run(host=local_server_host, port=local_server_port, debug=True)