import cv2
import numpy as np

def imdecode_bytes(image_bytes: bytes):
    arr = np.frombuffer(image_bytes, dtype=np.uint8)
    img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    return img

def to_rgb(img):
    return cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

def resize_max_side(img, max_side=1600):
    h, w = img.shape[:2]
    m = max(h, w)
    if m <= max_side:
        return img
    scale = max_side / m
    return cv2.resize(img, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_LINEAR)

def _rotate_bound(image, angle):
    (h, w) = image.shape[:2]
    (cX, cY) = (w // 2, h // 2)
    M = cv2.getRotationMatrix2D((cX, cY), angle, 1.0)
    cos = np.abs(M[0, 0])
    sin = np.abs(M[0, 1])
    nW = int((h * sin) + (w * cos))
    nH = int((h * cos) + (w * sin))
    M[0, 2] += (nW / 2) - cX
    M[1, 2] += (nH / 2) - cY
    return cv2.warpAffine(image, M, (nW, nH), flags=cv2.INTER_LINEAR)

def deskew(img):
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    gray = cv2.fastNlMeansDenoising(gray, h=3)
    edges = cv2.Canny(gray, 50, 150, apertureSize=3)
    lines = cv2.HoughLines(edges, 1, np.pi / 180, 150)
    if lines is None:
        return img, 0.0
    angles = []
    for rho, theta in lines[:, 0]:
        angle = (theta * 180 / np.pi) - 90
        if -45 <= angle <= 45:
            angles.append(angle)
    if not angles:
        return img, 0.0
    median = float(np.median(angles))
    rotated = _rotate_bound(img, median)
    return rotated, median

def clahe_gray(gray):
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    return clahe.apply(gray)

def adaptive_thresh(gray):
    return cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 31, 9)

def unsharp_gray(gray):
    blur = cv2.GaussianBlur(gray, (0, 0), 1.0)
    sharp = cv2.addWeighted(gray, 1.5, blur, -0.5, 0)
    return sharp

def adjust_gamma(img, gamma=1.1):
    inv = 1.0 / max(gamma, 1e-6)
    table = np.array([(i / 255.0) ** inv * 255 for i in np.arange(0, 256)]).astype("uint8")
    return cv2.LUT(img, table)

def to_gray(img):
    return cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

def build_variants(image_bytes: bytes):
    img = imdecode_bytes(image_bytes)
    img = resize_max_side(img, 1600)
    base, angle = deskew(img)
    variants = []
    variants.append(("original", to_rgb(base)))
    g = to_gray(base)
    g1 = clahe_gray(g)
    v1 = adaptive_thresh(g1)
    variants.append(("clahe_thresh", v1))
    g2 = unsharp_gray(g1)
    v2 = adaptive_thresh(g2)
    variants.append(("unsharp_clahe_thresh", v2))
    g3 = to_gray(adjust_gamma(base, 1.2))
    v3 = adaptive_thresh(clahe_gray(g3))
    variants.append(("gamma12_clahe_thresh", v3))
    return variants, angle
