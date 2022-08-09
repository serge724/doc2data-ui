import numpy as np
from doctr.models import ocr_predictor
from datetime import datetime

ocr_model = ocr_predictor(det_arch='db_resnet50', reco_arch='crnn_vgg16_bn', pretrained = True)

def run_doctr_ocr(image):
    result = ocr_model([np.array(image)])
    page = result.export()['pages'][0]
    tokens = []
    c = 0
    for b in page['blocks']:
        for l in b['lines']:
            for w in l['words']:
                tokens.append({
                    'id': c,
                    'bbox': w['geometry'][0] + w['geometry'][1],
                    'word': w['value'],
                    'type': 'ocr_token',
                    'timestamp': datetime.now().__str__()
                })
                c += 1
    return tokens

# from doc2data.pdf import PDFCollection
# coll = PDFCollection('example_docs/')
# coll.process_files()
# page = coll.pdfs['262192.pdf'][0]
# image = page.read_content('image', dpi = 100, force_rgb = True)
# res = run_doctr_ocr(image)
