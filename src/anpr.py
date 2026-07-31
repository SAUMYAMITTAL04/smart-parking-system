import cv2
import easyocr
import numpy as np
import re

# Initialize EasyOCR Reader once
reader = easyocr.Reader(['en'], gpu=False)


def clean_plate_text(text):
    """Cleans raw OCR output and returns standard alphanumeric license plate string."""
    if not text:
        return None
    clean = re.sub(r'[^A-Z0-9]', '', text.upper())
    if 5 <= len(clean) <= 8:
        return clean
    return None


def detect_and_draw_plates(frame):
    """Detects license plates and draws bounding boxes."""
    img_h, img_w = frame.shape[:2]
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    blur = cv2.GaussianBlur(gray, (5, 5), 0)
    sobelx = cv2.Sobel(blur, cv2.CV_8U, 1, 0, ksize=3)
    _, thresh = cv2.threshold(
        sobelx, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU
    )

    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (17, 3))
    morph = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)

    contours, _ = cv2.findContours(
        morph, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
    )

    detected_texts = []

    for cnt in contours:
        x, y, w, h = cv2.boundingRect(cnt)
        aspect_ratio = w / float(h)
        area = w * h

        # ROI check: lower road level only
        if y < int(img_h * 0.35):
            continue

        if 2.5 <= aspect_ratio <= 6.0 and 80 <= w <= 350 and 20 <= h <= 100:
            hull = cv2.convexHull(cnt)
            hull_area = cv2.contourArea(hull)
            if hull_area == 0:
                continue
            if (area / float(hull_area)) < 0.6:
                continue

            pad_w, pad_h = int(w * 0.1), int(h * 0.1)
            y1, y2 = max(0, y - pad_h), min(img_h, y + h + pad_h)
            x1, x2 = max(0, x - pad_w), min(img_w, x + w + pad_w)

            plate_crop = gray[y1:y2, x1:x2]
            if plate_crop.size == 0:
                continue

            ocr_results = reader.readtext(
                plate_crop, allowlist='ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
            )
            plate_str = None

            for _, text, prob in ocr_results:
                cleaned = clean_plate_text(text)
                if cleaned and prob > 0.4:
                    plate_str = cleaned
                    detected_texts.append(plate_str)
                    break

            if plate_str:
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                cv2.rectangle(
                    frame, (x, y - 24), (x + w, y), (0, 255, 0), -1
                )
                cv2.putText(
                    frame,
                    plate_str,
                    (x + 5, y - 6),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    (0, 0, 0),
                    2,
                )

    return frame, detected_texts


def extract_license_plate_from_bytes(file_bytes):
    """Extracts plate text from manual upload image."""
    try:
        np_arr = np.frombuffer(file_bytes.read(), np.uint8)
        img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
        _, plates = detect_and_draw_plates(img)
        return plates[0] if plates else "UNKNOWN"
    except Exception:
        return "UNKNOWN"