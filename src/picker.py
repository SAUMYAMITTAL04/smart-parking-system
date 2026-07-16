import cv2
import json
import os

# Paths configuration
VIDEO_PATH = os.path.join('data', 'parking_video.mp4')
OUTPUT_JSON = os.path.join('data', 'slots.json')

current_slot = []
all_slots = []

def mouse_callback(event, x, y, flags, param):
    global current_slot, all_slots
    
    # Left click to add a point to the current parking slot polygon
    if event == cv2.EVENT_LBUTTONDOWN:
        current_slot.append([x, y])
        print(f"Point recorded: ({x}, {y})")
        
        # Once 4 points are selected, finalize the slot polygon mapping
        if len(current_slot) == 4:
            slot_id = len(all_slots) + 1
            all_slots.append({"id": slot_id, "coordinates": current_slot.copy()})
            print(f"--- Slot {slot_id} successfully saved! ---")
            current_slot.clear()

def main():
    if not os.path.exists('data'):
        os.makedirs('data')

    cap = cv2.VideoCapture(VIDEO_PATH)
    success, frame = cap.read()
    cap.release()
    
    if not success:
        print("Error: Could not read video file. Place a valid video in data/parking_video.mp4")
        return

    print("\n Instructions:")
    print("1. Click 4 points in clockwise order to define a parking slot layout box.")
    print("2. Repeat for all available parking slots in view.")
    print("3. Press 'S' to save mapping file and exit. Press 'Q' to quit without saving.\n")

    cv2.namedWindow("Parking Slot Picker Setup")
    cv2.setMouseCallback("Parking Slot Picker Setup", mouse_callback)

    while True:
        img_copy = frame.copy()
        
        # Render finalized slot boundaries onto configuration display window
        for slot in all_slots:
            pts = np.array(slot["coordinates"], np.int32)
            cv2.polylines(img_copy, [pts], True, (0, 255, 0), 2)
            cv2.putText(img_copy, f"ID:{slot['id']}", tuple(slot["coordinates"][0]), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 2)
            
        # Draw dynamic preview lines for currently ongoing click mappings
        for pt in current_slot:
            cv2.circle(img_copy, tuple(pt), 4, (0, 0, 255), -1)

        cv2.imshow("Parking Slot Picker Setup", img_copy)
        key = cv2.waitKey(1) & 0xFF
        
        if key == ord('s') or key == ord('S'):
            with open(OUTPUT_JSON, 'w') as f:
                json.dump(all_slots, f, indent=4)
            print(f"Configuration profile written to path: {OUTPUT_JSON}")
            break
        elif key == ord('q') or key == ord('Q'):
            break

if __name__ == "__main__":
    import numpy as np
    main()