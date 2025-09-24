import os
from ultralytics import YOLO
import cv2

def test_yolo(model_path, image_dir, output_dir):
    """
    Test the YOLO model on a set of images.

    Args:
        model_path (str): Path to the trained YOLO model (.pt file).
        image_dir (str): Directory containing test images.
        output_dir (str): Directory to save the output images with detections.
    """
    # Load the YOLO model
    model = YOLO(model_path)

    # Ensure the output directory exists
    os.makedirs(output_dir, exist_ok=True)

    # Iterate through all images in the directory
    for image_name in os.listdir(image_dir):
        image_path = os.path.join(image_dir, image_name)

        # Read the image
        image = cv2.imread(image_path)
        if image is None:
            print(f"Skipping invalid image: {image_name}")
            continue

        # Perform detection
        results = model.predict(source=image, save=False, imgsz=640)

        # Annotate the image with detections
        annotated_image = results[0].plot()

        # Save the annotated image
        output_path = os.path.join(output_dir, image_name)
        cv2.imwrite(output_path, annotated_image)
        print(f"Processed {image_name}, results saved to {output_path}")

if __name__ == "__main__":
    # Path to the trained YOLO model
    model_path = "C:/Users/Soporte/Documents/ProjectPythonOCR/runs/detect/train4/weights/best.pt"

    # Directory containing test images
    image_dir = "C:/Users/Soporte/Documents/ProjectPythonOCR/dataset/images"

    # Directory to save the output images
    output_dir = "C:/Users/Soporte/Documents/ProjectPythonOCR/dataset/output"

    # Run the test
    test_yolo(model_path, image_dir, output_dir)