import cv2
import numpy as np
import torch
from ultralytics import YOLO

class YOLODetector:
    def __init__(self, model_path: str = 'yolov5s'):
        self.model = YOLO(model_path)

    def detect_regions(self, image: np.ndarray):
        results = self.model.predict(image)
        regions = []
        for result in results:
            for box in result.boxes:
                x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
                regions.append({
                    "bbox": (x1, y1, x2, y2),
                    "confidence": float(box.conf),
                    "class": int(box.cls)
                })
        return regions

# Example usage:
# detector = YOLODetector('path/to/yolo_model.pt')
# regions = detector.detect_regions(image)