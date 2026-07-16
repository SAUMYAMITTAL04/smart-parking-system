import cv2
import json
import numpy as np

class ParkingDetector:
    def __init__(self, slots_json_path, model_weight=None):
        # We load your custom parking slot configuration setup coordinates
        with open(slots_json_path, 'r') as f:
            self.slots = json.load(f)

    def process_frame(self, frame):
        occupied_count = 0
        empty_count = 0
        annotated_frame = frame.copy()
        
        # Convert frame to grayscale and blur to remove pixel noise smoothly
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        blur = cv2.GaussianBlur(gray, (3, 3), 1)

        for slot in self.slots:
            slot_pts = np.array(slot["coordinates"], np.int32)
            
            # Create an individual region mask specifically for this parking space box
            mask = np.zeros(gray.shape, dtype=np.uint8)
            cv2.fillPoly(mask, [slot_pts], 255)
            
            # Crop out and isolate just the pixels inside this slot box
            slot_crop = cv2.mean(blur, mask=mask)[0]
            
            # Calculate standard deviation of pixels to check for structural texture variance
            # Empty asphalt has low variance; cars with windows/metal parts have high variance
            rect = cv2.boundingRect(slot_pts)
            x, y, w, h = rect
            crop_roi = blur[y:y+h, x:x+w]
            
            if crop_roi.size > 0:
                variance = np.var(crop_roi)
            else:
                variance = 0

            # Hackathon Threshold Tune: Adjust this value to calibrate sensitivity flawlessly
            if variance > 900:
                is_occupied = True
            else:
                is_occupied = False

            # Render UI elements based on variance validation results
            if is_occupied:
                occupied_count += 1
                color = (0, 0, 255) # Red for occupied
            else:
                empty_count += 1
                color = (0, 255, 0) # Green for empty

            cv2.polylines(annotated_frame, [slot_pts], True, color, 2)
            cv2.putText(annotated_frame, f"ID: {slot['id']}", tuple(slot["coordinates"][0]),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.4, color, 1)

        return annotated_frame, empty_count, occupied_count