import cv2
import numpy as np
import mss
import mediapipe as mp
from datetime import datetime
import os
import time
from skimage.metrics import structural_similarity as ssim

# === Config ===
SCREEN_INDEX = 2  # 0 = all screens, since mss on macOS treats all as one virtual screen
CAPTURE_INTERVAL = 2  # seconds between checks
SSIM_THRESHOLD = 0.95  # lower = more sensitive to change
FACE_AREA_THRESHOLD = 0.25  # proportion of screen covered by faces
OUTPUT_DIR = "captured_slides"

os.makedirs(OUTPUT_DIR, exist_ok=True)

# === Mediapipe Face Detection Setup ===
mp_face_detection = mp.solutions.face_detection
face_detector = mp_face_detection.FaceDetection(
    model_selection=0, min_detection_confidence=0.5)


def capture_screen():
    with mss.mss() as sct:
        monitor = sct.monitors[SCREEN_INDEX]
        screenshot = sct.grab(monitor)
        img = np.array(screenshot)
        return cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)


def get_face_area_fraction(image):
    height, width, _ = image.shape
    face_area_total = 0

    # Convert BGR to RGB for mediapipe
    results = face_detector.process(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))

    if results.detections:
        for detection in results.detections:
            bbox = detection.location_data.relative_bounding_box
            box_area = bbox.width * bbox.height
            face_area_total += box_area

    return face_area_total


def image_similarity(img1, img2):
    gray1 = cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY)
    gray2 = cv2.cvtColor(img2, cv2.COLOR_BGR2GRAY)

    if gray1.shape != gray2.shape:
        return 0  # consider as very different

    score, _ = ssim(gray1, gray2, full=True)
    return score


def save_image(image):
    timestamp = datetime.now().strftime("%y%m%d-%H%M%S")
    filepath = os.path.join(OUTPUT_DIR, f"{timestamp}.png")
    cv2.imwrite(filepath, image)
    print(f"[+] Slide captured: {filepath}")


def main():
    print("🔍 Starting TL_lecture-slide-builder with mediapipe...")
    last_image = None

    while True:
        current_image = capture_screen()
        face_area_ratio = get_face_area_fraction(current_image)

        if face_area_ratio > FACE_AREA_THRESHOLD:
            print(
                f"👤 Skipped: {face_area_ratio*100:.1f}% of screen is face(s)")
        else:
            if last_image is None:
                save_image(current_image)
                last_image = current_image
            else:
                similarity = image_similarity(current_image, last_image)
                if similarity < SSIM_THRESHOLD:
                    save_image(current_image)
                    last_image = current_image
                else:
                    print(f"📋 Skipped: slides are {similarity:.2f} similar")

        time.sleep(CAPTURE_INTERVAL)


if __name__ == "__main__":
    main()
