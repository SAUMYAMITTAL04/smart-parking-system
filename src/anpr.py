import io
import cv2
import numpy as np
import easyocr

# Initialize EasyOCR Reader globally so it loads into memory once
# Set gpu=True if CUDA is available on your environment
try:
    reader = easyocr.Reader(['en'], gpu=False)
except Exception as e:
    print(f"[ANPR Warning] Could not initialize EasyOCR Reader: {e}")
    reader = None


def preprocess_image(img):
    """
    Applies grayscale, bilateral filter, and Canny edge detection
    to enhance plate boundaries.
    """
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    # Bilateral filter preserves edges while smoothing noise
    filtered = cv2.bilateralFilter(gray, 11, 17, 17)
    edged = cv2.Canny(filtered, 30, 200)
    return gray, edged


def detect_and_draw_plates(frame):
    """
    Processes a live OpenCV video frame:
    1. Finds rectangular contours matching license plate aspect ratios.
    2. Runs OCR on detected sub-regions.
    3. Draws green bounding boxes and labels on the frame.
    Returns: (annotated_frame, list_of_detected_plates)
    """
    if frame is None:
        return frame, []

    annotated = frame.copy()
    detected_plates = []

    if reader is None:
        return annotated, detected_plates

    gray, edged = preprocess_image(frame)

    # Find contours in the edge map
    contours, _ = cv2.findContours(edged.copy(), cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    contours = sorted(contours, key=cv2.contourArea, reverse=True)[:10]

    for c in contours:
        perimeter = cv2.arcLength(c, True)
        approx = cv2.approxPolyDP(c, 0.018 * perimeter, True)

        # License plates are generally 4-sided quadrilaterals
        if len(approx) == 4:
            x, y, w, h = cv2.boundingRect(approx)
            aspect_ratio = w / float(h)

            # Standard plate aspect ratio roughly ranges between 2.0 and 5.5
            if 2.0 <= aspect_ratio <= 6.0 and w > 60 and h > 20:
                # Crop plate region from gray frame
                plate_crop = gray[y:y+h, x:x+w]

                # Run OCR on crop
                results = reader.readtext(plate_crop)

                for _, text, prob in results:
                    clean_text = "".join(e for e in text if e.isalnum()).upper()
                    if len(clean_text) >= 4 and prob > 0.25:
                        detected_plates.append(clean_text)

                        # Draw green bounding box & text overlay on active frame
                        cv2.rectangle(annotated, (x, y), (x + w, y + h), (0, 255, 0), 2)
                        cv2.putText(
                            annotated,
                            clean_text,
                            (x, max(y - 10, 20)),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            0.7,
                            (0, 255, 0),
                            2
                        )
                        break

    return annotated, detected_plates


def extract_license_plate_from_bytes(uploaded_file):
    """
    Converts Streamlit UploadedFile or BytesIO buffer into an OpenCV image
    and executes EasyOCR scanning.
    Returns: String (Detected Plate Number or Status)
    """
    if uploaded_file is None:
        return "NO_FILE"

    if reader is None:
        return "OCR_NOT_INITIALIZED"

    try:
        # Step 1: Extract bytes stream safely from Streamlit upload buffer
        if hasattr(uploaded_file, "getvalue"):
            file_bytes = uploaded_file.getvalue()
        elif hasattr(uploaded_file, "read"):
            file_bytes = uploaded_file.read()
        else:
            file_bytes = uploaded_file

        # Step 2: Convert byte buffer into numpy array and decode to OpenCV BGR image
        np_array = np.frombuffer(file_bytes, np.uint8)
        img = cv2.imdecode(np_array, cv2.IMREAD_COLOR)

        if img is None:
            return "INVALID_IMAGE"

        # Step 3: Resize high-res camera uploads for better OCR detection
        height, width = img.shape[:2]
        if width > 1000:
            scale = 1000.0 / width
            img = cv2.resize(img, (1000, int(height * scale)))

        # Step 4: Full-image EasyOCR scan
        results = reader.readtext(img)

        candidates = []
        for bbox, text, prob in results:
            # Clean non-alphanumeric characters (keep numbers and uppercase letters)
            clean_text = "".join(e for e in text if e.isalnum()).upper()
            
            # Typical license plates are between 4 and 10 characters
            if 4 <= len(clean_text) <= 10 and prob > 0.20:
                candidates.append((clean_text, prob))

        if candidates:
            # Pick highest confidence match
            candidates.sort(key=lambda x: x[1], reverse=True)
            return candidates[0][0]

        # Step 5: Fallback scan using preprocessed grayscale if raw OCR returned nothing
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        fallback_results = reader.readtext(gray)

        for bbox, text, prob in fallback_results:
            clean_text = "".join(e for e in text if e.isalnum()).upper()
            if 4 <= len(clean_text) <= 10 and prob > 0.15:
                return clean_text

        return "NO_PLATE_FOUND"

    except Exception as e:
        print(f"[ANPR Scan Error] {e}")
        return "ERROR_PROCESSING"
