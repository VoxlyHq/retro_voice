from doctr.models import ocr_predictor

def detect_text(image_path):
    model = ocr_predictor(det_arch='db_resnet50', reco_arch='crnn_vgg16_bn', pretrained=True)
    single_img_doc = DocumentFile.from_images(image_path)
    result = model(single_img_doc)
    print(result)

if __name__ == "__main__":
    # Path to your image file
    image_path = '~/Desktop/ff2_en_1.png'
    detect_text(image_path)
