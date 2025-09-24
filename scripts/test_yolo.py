import sys
sys.path.append("c:\\Users\\Soporte\\Documents\\ProjectPythonOCR")

import os
import cv2
from pathlib import Path
from app.services.yolo_detector import YOLODetector

def process_images_with_yolo(image_dir, model_path='c:\\Users\\Soporte\\Documents\\ProjectPythonOCR\\yolov8s.pt'):
    detector = YOLODetector(model_path)
    image_dir = Path(image_dir)

    for image_file in image_dir.glob("*.jpeg"):
        print(f"Processing: {image_file}")
        img = cv2.imread(str(image_file))
        regions = detector.detect_regions(img)

        for region in regions:
            x1, y1, x2, y2 = region['bbox']
            confidence = region['confidence']
            cls = region['class']
            print(f"Detected region: bbox=({x1}, {y1}, {x2}, {y2}), confidence={confidence}, class={cls}")

if __name__ == "__main__":
    uploads_dir = "c:\\Users\\Soporte\\Documents\\ProjectPythonOCR\\uploads"
    process_images_with_yolo(uploads_dir)