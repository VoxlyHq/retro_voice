from doctr.models import ocr_predictor
from doctr.io import DocumentFile
import time


model = ocr_predictor(det_arch='db_resnet50', reco_arch='crnn_vgg16_bn', pretrained=True)
single_img_doc = DocumentFile.from_images("ff2_en_1.png")
start_time = time.time()  # Start timing
result = model(single_img_doc)
end_time = time.time()  # End timing
print(f"Execution time: {end_time - start_time} seconds")
print(result)