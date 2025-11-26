# predict_live_yolo.py (Simplified)
# This script runs a LIVE camera feed, finds the largest object,
# and classifies it CONTINUOUSLY using the YOLO model.
# It will ONLY display 'Wet Waste' or 'Dry Waste'.

import cv2
import numpy as np
import os
from ultralytics import YOLO

# --- Configuration ---
MODEL_PATH = 'yolov8m-cls.pt' # Using the YOLO classification model
CAMERA_ID = 0           # Use 0 for the default built-in laptop webcam
CONFIDENCE_THRESHOLD = 0.50 # Min confidence to accept a top-5 prediction
MIN_OBJECT_AREA = 8000  # Min pixel area to be considered an object

# --- Class Definitions ---
dry_classes = (
    'water_bottle', 'pop_bottle', 'beer_bottle', 'wine_bottle', 'paper_towel', 'envelope', 'book_jacket',
    'comic_book', 'menu', 'cardboard_box', 'carton', 'plastic_bag', 'garbage_truck', 'tin_can', 'milk_can',
    'beer_can', 'pill_bottle', 'packet', 'matchstick', 'nail', 'screw', 'ballpoint_pen', 'pencil_box',
    'paper_clip', 'rubber_eraser', 'wooden_spoon', 'plate', 'bowl', 'cup', 'beer_glass', 'wine_glass',
    'coffee_mug', 'cellular_telephone', 'desktop_computer', 'notebook_computer', 'electric_fan', 'lamp',
    'television', 'CD_player', 'iPod', 'digital_clock', 'analog_clock', 'wall_clock', 'hourglass',
    'sunglasses', 'sunglass', 'binoculars', 'electric_guitar', 'acoustic_guitar', 'violin', 'cellular_telephone',
    'mouse_trap', 'projectile', 'missile', '', 'candle', 'space_shuttle', 'nail', 'paintbrush', 'syringe',
    'gasmask', 'diaper','airship', 'rubber_eraser', 'ballpoint', 'mailbag', 'toilet_tissue', 'switch',
    'knot', 'file', 'necklace', 'notebook', 'perfume','purse', 'remote_control', 'radio', 'rugby_ball',
    'scale', 'screw_driver', 'soap_dispenser', 'soup_bowl', 'spatula', 'swab', 'comic_book', 'wool',
    'wooden_spoon', 'whistle', 'whiskey_jug', 'coral_reef', 'crossword_puzzle', 'street_sign', 'hot_pot',
    'vase', 'tray', 'toaster', 'tennis_ball', 'snorkel', 'soccer_ball', 'sunscreen', 'safety_pin', 'saltshaker',
    'scoreboard', 'screwdriver', 'shopping_basket', 'parachute', 'pencil_sharpener', 'Petri_dish', 'picket_fence',
    'pinwheel', 'pirate', 'plane', 'planetarium', 'pole', 'modem', 'hook', 'lab_coat', 'measuring_cup', 'mask',
    'magnetic_compass', 'lotion', 'lighter', 'letter_opener', 'lens_cap', 'lampshade', 'ladle', 'golf_ball', 'flagpole',
    'handkerchief', 'coffeepot', 'Crock_Pot', 'croquet_ball', 'bottlecap', 'can_opener', 'carton', 'cleaver', 'bolo_tie',
    'bath_towel', 'binder', 'packet', 'conch', 'binder', 'apron', 'monitor', 'lighter', 'pay-phone', 'tree_frog', 'nematode', 'tree_frog', 'American_alligator'
)

wet_classes = (
    'banana', 'apple', 'strawberry', 'orange', 'lemon', 'pineapple', 'jackfruit', 'custard_apple', 'pomegranate',
    'fig', 'guava', 'mango', 'grapes', 'watermelon', 'cantaloupe', 'hone_dew', 'cucumber', 'eggplant',
    'bell_pepper', 'head_cabbage', 'broccoli', 'cauliflower', 'zucchini', 'spaghetti_squash', 'acorn_squash',
    'butternut_squash', 'artichoke', 'cardoon', 'mushroom', 'Granny_Smith', 'earthstar', 'stinkhorn',
    'hen-of-the-woods', 'bolete', 'corn', 'buckeye', 'organ', 'brain_coral', 'coral_fungus', 'agaric',
    'gyromitra', 'face_powder', 'ice_cream', 'pizza', 'ping_pong_ball', 'ping-pong_ball', 'dough', 'meat_loaf',
    'burrito', 'chocolate_sauce', 'eggnog', 'espresso', 'strawberry', 'butternut_squash', 'carbonara', 'potpie',
    'red_wine', 'guacamole', 'consomme', 'trifle', 'ice_lolly', 'French_loaf', 'bagel', 'pretzel', 'cheeseburger',
    'hotdog', 'mashed_potato', 'rotisserie', 'drumstick', 'snail', 'slug', 'jackfruit', 'buckeye'
)

# --- Main Application Logic ---
def main():
    """Main function to run the live prediction loop."""
    
    # --- 1. Load Model ---
    print("Loading YOLO model...")
    try:
        model = YOLO(MODEL_PATH)
        print("YOLO model loaded successfully.")
    except Exception as e:
        print(f"Error loading model: {e}")
        print(f"Please make sure the '{MODEL_PATH}' file exists and 'ultralytics' is installed.")
        return
        
    # --- 2. Start Camera Feed ---
    cap = cv2.VideoCapture(CAMERA_ID)
    
    if not cap.isOpened():
        print(f"Error: Could not open camera (ID: {CAMERA_ID}).")
        return

    print("\nStarting live prediction... Press 'q' to quit.")
    
    # --- 3. Prediction Loop ---
    while True:
        ret, frame = cap.read()
        if not ret:
            print("Failed to grab frame.")
            break
        
        # --- 4. State variables (reset every frame) ---
        prediction_text = "Looking for object..."
        box_color = (255, 255, 255) # White
        box_coords = None

        # --- 5. Find Largest Object ---
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (7, 7), 0)
        _, thresh = cv2.threshold(blurred, 100, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        if contours:
            largest_contour = max(contours, key=cv2.contourArea)
            
            if cv2.contourArea(largest_contour) > MIN_OBJECT_AREA:
                x, y, w, h = cv2.boundingRect(largest_contour)
                box_coords = (x, y, w, h) # Set box for drawing
                
                # --- 6. Predict on the Detected Object (ROI) using YOLO ---
                roi = frame[y:y+h, x:x+w]
                if roi.size > 0:
                    
                    results = model.predict(source=roi, verbose=False)
                    top5_indices = results[0].probs.top5
                    top5_confs = results[0].probs.top5conf
                    top5_names = [model.names[i] for i in top5_indices]

                    waste_type = None

                    # Check top 5 guesses against our lists
                    for name, conf in zip(top5_names, top5_confs):
                        if conf < CONFIDENCE_THRESHOLD:
                            continue 

                        if name in wet_classes:
                            waste_type = 'wet'
                            break # Found a match, stop
                        elif name in dry_classes:
                            waste_type = 'dry'
                            break # Found a match, stop
                    
                    # --- 7. Update Text and Color ---
                    if waste_type:
                        prediction_text = f"{waste_type.capitalize()} Waste"
                        box_color = (0, 255, 0) # Green
                    # --- If it's not wet or dry, text stays "Looking for object..." ---

        # --- 8. Draw Results (Every Frame) ---
        if box_coords:
            x, y, w, h = box_coords
            cv2.rectangle(frame, (x, y), (x + w, y + h), box_color, 3)
        
        (text_width, text_height), _ = cv2.getTextSize(prediction_text, cv2.FONT_HERSHEY_SIMPLEX, 1.2, 3)
        text_x = (frame.shape[1] - text_width) // 2
        text_y = 50 # Put text at the top
        cv2.putText(frame, prediction_text, (text_x, text_y), cv2.FONT_HERSHEY_SIMPLEX, 1.2, box_color, 3)

        # --- 9. Show the Final Frame ---
        cv2.imshow('Live Waste Classification Test', frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    # --- 10. Cleanup ---
    cap.release()
    cv2.destroyAllWindows()
    print("Prediction stopped.")

if __name__ == '__main__':
    main()