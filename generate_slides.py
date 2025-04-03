import cv2
import numpy as np
import mss
import mediapipe as mp
from datetime import datetime
import os
import time
import threading
import queue
import pytesseract
from skimage.metrics import structural_similarity as ssim
import requests
import re
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# === Config ===
class Config:
    """Configuration settings for the application."""
    SCREEN_INDEX = 2  # 0 = all screens, since mss on macOS treats all as one virtual screen
    CAPTURE_INTERVAL = 2  # seconds between checks
    SSIM_THRESHOLD = 0.95  # lower = more sensitive to change
    FACE_AREA_THRESHOLD = 0.25  # proportion of screen covered by faces
    TEXT_SIMILARITY_THRESHOLD = 0.8  # text similarity threshold (0-1)
    OUTPUT_DIR = "captured_slides"
    MAX_TITLE_LENGTH = 50  # maximum length of generated title
    OCR_QUEUE_SIZE = 100  # maximum number of images to queue for OCR processing
    DEBUG_MODE = False  # Set to True to save processed images for debugging

    @classmethod
    def initialize(cls):
        """Initialize directories based on configuration."""
        os.makedirs(cls.OUTPUT_DIR, exist_ok=True)
        if cls.DEBUG_MODE:
            cls.DEBUG_DIR = os.path.join(cls.OUTPUT_DIR, "debug")
            os.makedirs(cls.DEBUG_DIR, exist_ok=True)


# === Screen Capture Module ===
class ScreenCapture:
    """Handles screen capture functionality."""
    
    @staticmethod
    def capture_screen(screen_index=None):
        """Capture a screenshot from the specified screen index."""
        if screen_index is None:
            screen_index = Config.SCREEN_INDEX
            
        with mss.mss() as sct:
            monitor = sct.monitors[screen_index]
            screenshot = sct.grab(monitor)
            img = np.array(screenshot)
            return cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)


# === Image Processing Module ===
class ImageProcessor:
    """Handles image processing and analysis."""
    
    # Initialize face detection
    mp_face_detection = mp.solutions.face_detection
    face_detector = mp_face_detection.FaceDetection(
        model_selection=0, min_detection_confidence=0.5)
    
    @classmethod
    def get_face_area_fraction(cls, image):
        """Calculate the fraction of the image covered by faces."""
        height, width, _ = image.shape
        face_area_total = 0

        # Convert BGR to RGB for mediapipe
        results = cls.face_detector.process(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))

        if results.detections:
            for detection in results.detections:
                bbox = detection.location_data.relative_bounding_box
                box_area = bbox.width * bbox.height
                face_area_total += box_area

        return face_area_total
    
    @staticmethod
    def image_similarity(img1, img2):
        """Calculate similarity between two images using SSIM."""
        gray1 = cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY)
        gray2 = cv2.cvtColor(img2, cv2.COLOR_BGR2GRAY)

        if gray1.shape != gray2.shape:
            return 0  # consider as very different

        score, _ = ssim(gray1, gray2, full=True)
        return score
    
    @staticmethod
    def text_similarity(img1, img2):
        """Calculate the similarity between OCR text from two images."""
        try:
            # Extract text from both images
            text1 = OCRProcessor.extract_text_from_image(img1)
            text2 = OCRProcessor.extract_text_from_image(img2)
            
            # If both texts are empty, consider them identical
            if not text1 and not text2:
                return 1.0
            
            # If only one text is empty, they are completely different
            if not text1 or not text2:
                return 0.0
            
            # Calculate Jaccard similarity (intersection over union of words)
            words1 = set(text1.lower().split())
            words2 = set(text2.lower().split())
            
            intersection = len(words1.intersection(words2))
            union = len(words1.union(words2))
            
            if union == 0:  # Safeguard against division by zero
                return 1.0
                
            return intersection / union
        except Exception as e:
            print(f"❌ Text similarity error: {e}")
            return 0


# === File Management Module ===
class FileManager:
    """Handles file operations for saving and renaming images."""
    
    @staticmethod
    def save_image(image, output_dir=None):
        """Save an image with a timestamp filename."""
        if output_dir is None:
            output_dir = Config.OUTPUT_DIR
            
        timestamp = datetime.now().strftime("%y%m%d-%H%M%S")
        filepath = os.path.join(output_dir, f"{timestamp}.png")
        cv2.imwrite(filepath, image)
        print(f"[+] Slide captured: {filepath}")
        return filepath
    
    @staticmethod
    def rename_file_with_title(filepath, title):
        """Rename the file with the generated title."""
        if not title:
            return filepath
        
        try:
            directory = os.path.dirname(filepath)
            filename = os.path.basename(filepath)
            name, ext = os.path.splitext(filename)
            
            new_filename = f"{name}_{title}{ext}"
            new_filepath = os.path.join(directory, new_filename)
            
            os.rename(filepath, new_filepath)
            print(f"✅ Renamed: {filename} -> {new_filename}")
            return new_filepath
        except Exception as e:
            print(f"❌ File rename error: {e}")
            return filepath


# === OCR Module ===
class OCRProcessor:
    """Handles OCR processing of images."""
    
    @staticmethod
    def extract_text_from_image(image, filename=None):
        """Extract text from an image using OCR with preprocessing for better results."""
        try:
            # Convert to grayscale
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Apply adaptive thresholding to handle different lighting conditions
            thresh = cv2.adaptiveThreshold(
                gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
            )
            
            # Noise removal using median blur
            processed = cv2.medianBlur(thresh, 3)
            
            # Save processed image for debugging if enabled
            if Config.DEBUG_MODE and filename:
                debug_base = os.path.basename(filename)
                debug_name, debug_ext = os.path.splitext(debug_base)
                
                cv2.imwrite(os.path.join(Config.DEBUG_DIR, f"{debug_name}_gray{debug_ext}"), gray)
                cv2.imwrite(os.path.join(Config.DEBUG_DIR, f"{debug_name}_thresh{debug_ext}"), thresh)
                cv2.imwrite(os.path.join(Config.DEBUG_DIR, f"{debug_name}_processed{debug_ext}"), processed)
            
            # OCR with multiple language support and page segmentation mode for slide layout
            text = pytesseract.image_to_string(
                processed, 
                config='--psm 1 --oem 3 -l eng'  # Page segmentation mode 1 (auto), OCR Engine mode 3 (default)
            )
            
            # If text extraction fails or returns very little text, try with original image
            if not text or len(text.strip()) < 10:
                print("⚠️ Initial OCR produced limited text, trying with original image...")
                text = pytesseract.image_to_string(image)
            
            return text.strip()
        except Exception as e:
            print(f"❌ OCR error: {e}")
            return ""


# === Title Generation Module ===
class TitleGenerator:
    """Handles generation of titles from OCR text."""
    
    @staticmethod
    def generate_title_from_text(text):
        """Generate a title from OCR text using Deepseek API."""
        if not text:
            return None
        
        try:
            # Check if API key is available
            api_key = os.environ.get('DEEPSEEK_API_KEY')
            if not api_key:
                print("⚠️ DEEPSEEK_API_KEY not found in environment variables. Using fallback title generation.")
                return TitleGenerator.generate_fallback_title(text)
            
            # Prepare prompt for Deepseek
            prompt = f"""Based on the following text from a lecture slide, generate a concise, descriptive title.
            The title should be under {Config.MAX_TITLE_LENGTH} characters, with words separated by underscores.
            The title should capture the main topic or concept of the slide.
            
            Text from slide:
            {text[:1000]}  # Limit text length to avoid token limits
            
            Return only the title with no additional text or explanation."""
            
            # Use Deepseek API to generate title
            response = requests.post(
                "https://api.deepseek.com/v1/chat/completions",
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {api_key}"
                },
                json={
                    "model": "deepseek-chat",
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.7,
                    "max_tokens": 50
                },
                timeout=10  # Add timeout to prevent hanging
            )
            
            if response.status_code == 200:
                title = response.json()["choices"][0]["message"]["content"].strip()
                # Clean up the title - remove spaces and special characters
                title = TitleGenerator._clean_title(title)
                return title
            else:
                print(f"❌ Deepseek API error: {response.status_code} - {response.text}")
                return TitleGenerator.generate_fallback_title(text)
        except Exception as e:
            print(f"❌ Title generation error: {e}")
            return TitleGenerator.generate_fallback_title(text)
    
    @staticmethod
    def generate_fallback_title(text):
        """Generate a simple title from text when API is not available."""
        try:
            # Extract the first few words (max 5) from the text
            words = text.split()[:5]
            # Join them with underscores and limit length
            title = "_".join(words)
            # Clean up the title
            title = TitleGenerator._clean_title(title)
            return title
        except Exception as e:
            print(f"❌ Fallback title generation error: {e}")
            return "untitled"
    
    @staticmethod
    def _clean_title(title):
        """Clean up a title string by removing special characters and limiting length."""
        # Remove spaces and special characters
        title = re.sub(r'[^\w]', '_', title)
        title = re.sub(r'_+', '_', title)  # Replace multiple underscores with a single one
        title = title.strip('_')
        
        if len(title) > Config.MAX_TITLE_LENGTH:
            title = title[:Config.MAX_TITLE_LENGTH]
            
        return title


# === Slide Capture Application ===
class SlideCapture:
    """Main application class that coordinates the slide capture process."""
    
    def __init__(self):
        """Initialize the slide capture application."""
        self.ocr_queue = queue.Queue(maxsize=Config.OCR_QUEUE_SIZE)
        self.last_image = None
        self.ocr_thread = None
    
    def start(self):
        """Start the slide capture application."""
        print("🔍 Starting TL_lecture-slide-builder with mediapipe...")
        
        # Initialize configuration
        Config.initialize()
        
        # Start OCR worker thread
        self.ocr_thread = threading.Thread(target=self._ocr_worker, daemon=True)
        self.ocr_thread.start()
        
        self._main_loop()
    
    def _main_loop(self):
        """Main loop for capturing and processing slides."""
        while True:
            current_image = ScreenCapture.capture_screen()
            face_area_ratio = ImageProcessor.get_face_area_fraction(current_image)

            if face_area_ratio > Config.FACE_AREA_THRESHOLD:
                print(f"👤 Skipped: {face_area_ratio*100:.1f}% of screen is face(s)")
            else:
                if self.last_image is None:
                    self._process_new_slide(current_image)
                else:
                    # Use text similarity instead of image similarity
                    text_similarity = ImageProcessor.text_similarity(current_image, self.last_image)
                    
                    if text_similarity < Config.TEXT_SIMILARITY_THRESHOLD:
                        print(f"📝 New slide detected: text similarity is {text_similarity:.2f}")
                        self._process_new_slide(current_image)
                    else:
                        print(f"📋 Skipped: text similarity is {text_similarity:.2f}")

            time.sleep(Config.CAPTURE_INTERVAL)
    
    def _process_new_slide(self, image):
        """Process a new slide image."""
        filepath = FileManager.save_image(image)
        self.last_image = image
        
        # Add to OCR queue for processing
        try:
            self.ocr_queue.put((filepath, image), block=False)
        except queue.Full:
            print("⚠️ OCR queue is full, skipping OCR for this image")
    
    def _ocr_worker(self):
        """Worker thread for OCR processing."""
        print("🔍 Starting OCR worker thread...")
        
        while True:
            try:
                filepath, image = self.ocr_queue.get()
                filename = os.path.basename(filepath)
                
                try:
                    print(f"🔤 Processing OCR for {filename}...")
                    text = OCRProcessor.extract_text_from_image(image, filepath if Config.DEBUG_MODE else None)
                    
                    if text:
                        print(f"📝 Generating title for {filename}...")
                        title = TitleGenerator.generate_title_from_text(text)
                        
                        if title:
                            FileManager.rename_file_with_title(filepath, title)
                    else:
                        print(f"⚠️ No text extracted from {filename}")
                except Exception as e:
                    print(f"❌ Error processing {filename}: {e}")
                finally:
                    # Always mark the task as done
                    self.ocr_queue.task_done()
            except Exception as e:
                print(f"❌ OCR worker error: {e}")
                # Continue processing even if there's an error with one image
                continue


def main():
    """Main entry point for the application."""
    app = SlideCapture()
    app.start()


if __name__ == "__main__":
    main()
