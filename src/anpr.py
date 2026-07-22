import cv2
import re
import numpy as np
import easyocr

# Initialize EasyOCR Reader
reader = easyocr.Reader(['en'], gpu=False)

def clean_plate_text(text):
    """Cleans raw OCR output and returns standard alphanumeric license plate string."""
    if not text:
        return None
    clean = re.sub(r'[^A-Z0-9]', '', text.upper())
    if 4 <= len(clean) <= 8:
        return clean
    return None

def detect_and_draw_plates(frame):
    """
    Detects license plate candidates using morphological contour analysis,
    draws bounding boxes, runs OCR, and annotates text on top of the frame.
    """
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    
    # Preprocessing for plate edge localization
    blur = cv2.GaussianBlur(gray, (5, 5), 0)
    sobelx = cv2.Sobel(blur, cv2.CV_8U, 1, 0, ksize=3)
    _, thresh = cv2.threshold(sobelx, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (17, 3))
    morph = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
    
    contours, _ = cv2.findContours(morph, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    detected_texts = []

    for cnt in contours:
        x, y, w, h = cv2.boundingRect(cnt)
        aspect_ratio = w / float(h)
        
        # Filter typical rectangular dimensions of vehicle license plates
        if 2.0 <= aspect_ratio <= 6.5 and w > 45 and h > 12:
            # Crop region with padding
            pad_w, pad_h = int(w * 0.1), int(h * 0.1)
            y1, y2 = max(0, y - pad_h), min(frame.shape[0], y + h + pad_h)
            x1, x2 = max(0, x - pad_w), min(frame.shape[1], x + w + pad_w)
            
            plate_crop = gray[y1:y2, x1:x2]

            # Draw green bounding box around detected vehicle plate
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

            # OCR Extraction
            ocr_results = reader.readtext(plate_crop)
            plate_str = None
            for _, text, prob in ocr_results:
                cleaned = clean_plate_text(text)
                if cleaned and prob > 0.2:
                    plate_str = cleaned
                    detected_texts.append(plate_str)
                    break

            # Label box
            label = plate_str if plate_str else "PLATE"
            cv2.rectangle(frame, (x, y - 22), (x + w, y), (0, 255, 0), -1)
            cv2.putText(frame, label, (x + 3, y - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 2)

    return frame, detected_texts

def extract_license_plate_from_bytes(file_bytes):
    """Extracts plate text from manual upload."""
    try:
        np_arr = np.frombuffer(file_bytes.read(), np.uint8)
        img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
        _, plates = detect_and_draw_plates(img)
        return plates[0] if plates else "UNKNOWN"
    except Exception:
        return "UNKNOWN"