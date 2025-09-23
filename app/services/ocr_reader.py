import os
from functools import lru_cache
import easyocr

@lru_cache(maxsize=1)
def get_reader():
    langs = os.getenv("OCR_LANGUAGES", "es,en").split(",")
    gpu = os.getenv("OCR_GPU", "false").lower() in {"1", "true", "yes", "y"}
    return easyocr.Reader(langs, gpu=gpu)

def read_ndarray(img):
    return get_reader().readtext(img)
