import cv2
import os
from pathlib import Path
import tkinter as tk

def adjust_labels(image_dir, output_dir):
    image_dir = Path(image_dir)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    classes = ["ticket_num", "placa", "peso_neto", "ingreso_fecha_hora", "salida_fecha_hora"]

    screen_width = 1920  # Replace with your screen width
    screen_height = 1080  # Replace with your screen height

    for idx, image_file in enumerate(image_dir.glob("*.jpeg")):
        if idx >= 15:  # Process only the first 15 images
            break

        print(f"Adjusting labels for: {image_file}")
        img = cv2.imread(str(image_file))
        original_height, original_width, _ = img.shape

        # Resize image to fit screen
        scale = min(screen_width / original_width, screen_height / original_height, 1.0)
        resized_width = int(original_width * scale)
        resized_height = int(original_height * scale)
        img = cv2.resize(img, (resized_width, resized_height))

        bounding_boxes = []
        used_classes = set()
        selected_class = [None]  # Use a mutable object to store the selected class

        def select_class(class_name):
            selected_class[0] = class_name
            print(f"Selected class: {class_name}")

        def draw_rectangle(event, x, y, flags, param):
            if event == cv2.EVENT_LBUTTONDOWN:
                bounding_boxes.append([x, y])
            elif event == cv2.EVENT_LBUTTONUP:
                if selected_class[0] is None:
                    print("No class selected. Skipping this bounding box.")
                    bounding_boxes.pop()  # Remove incomplete bounding box
                    return
                bounding_boxes[-1].extend([x, y])
                class_id = classes.index(selected_class[0])
                bounding_boxes[-1].append(class_id)
                used_classes.add(selected_class[0])
                cv2.rectangle(img, (bounding_boxes[-1][0], bounding_boxes[-1][1]), (bounding_boxes[-1][2], bounding_boxes[-1][3]), (0, 255, 0), 2)
                cv2.putText(img, selected_class[0], (bounding_boxes[-1][0], bounding_boxes[-1][1] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
                cv2.imshow("Adjust Labels", img)
                selected_class[0] = None  # Reset selected class

        root = tk.Tk()
        root.title("Class Selection")

        def update_buttons():
            for widget in root.winfo_children():
                widget.destroy()
            for class_name in classes:
                state = tk.DISABLED if class_name in used_classes else tk.NORMAL
                button = tk.Button(root, text=class_name, state=state, command=lambda c=class_name: select_class(c))
                button.pack(side=tk.LEFT)

        while len(used_classes) < len(classes):
            update_buttons()
            print("Select a class before proceeding.")
            root.update()

            while selected_class[0] is None:
                root.update()

            cv2.imshow("Adjust Labels", img)
            cv2.setMouseCallback("Adjust Labels", draw_rectangle)
            print("Click and drag to draw bounding boxes. Press 's' to save and move to the next image.")

            while True:
                key = cv2.waitKey(1) & 0xFF
                if key == ord('s'):
                    break

            cv2.destroyAllWindows()

        root.destroy()

        # Save bounding boxes to .txt file
        label_file = output_dir / f"{image_file.stem}.txt"
        with open(label_file, "w") as f:
            for box in bounding_boxes:
                if len(box) < 5:  # Skip incomplete bounding boxes
                    continue
                # Adjust bounding box coordinates back to original scale
                x1 = int(box[0] / scale)
                y1 = int(box[1] / scale)
                x2 = int(box[2] / scale)
                y2 = int(box[3] / scale)
                x_center = ((x1 + x2) / 2) / original_width
                y_center = ((y1 + y2) / 2) / original_height
                box_width = (x2 - x1) / original_width
                box_height = (y2 - y1) / original_height
                f.write(f"{box[4]} {x_center} {y_center} {box_width} {box_height}\n")

        # Save the image with bounding boxes
        output_image_file = output_dir / f"{image_file.stem}_labeled.jpeg"
        cv2.imwrite(str(output_image_file), img)

if __name__ == "__main__":
    uploads_dir = "c:\\Users\\Soporte\\Documents\\ProjectPythonOCR\\uploads"
    output_dir = "c:\\Users\\Soporte\\Documents\\ProjectPythonOCR\\processed"
    adjust_labels(uploads_dir, output_dir)