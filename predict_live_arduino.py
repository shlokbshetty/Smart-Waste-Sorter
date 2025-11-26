# predict_on_trigger_yolo_arduino.py (Simplified)
# This script runs a LIVE camera feed, finds the largest object,
# classifies it using YOLO, and sends an Arduino signal
# when you press the SPACEBAR.
# It ONLY shows 'Wet Waste' or 'Dry Waste' on a successful ID.

import cv2
import numpy as np
import serial
import time
import os
from ultralytics import YOLO

# --- Configuration ---
MODEL_PATH = 'yolov8m-cls.pt' # Using the YOLO classification model
CAMERA_ID = 0           # Use 0 for the default built-in laptop webcam
ARDUINO_PORT = 'COM7'   # IMPORTANT: Update to your Arduino's COM port
BAUD_RATE = 9600
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

# --- Arduino Communication Setup ---
def setup_arduino(port, baud_rate):
    """Initializes and returns the serial connection to the Arduino."""
    try:
        print(f"Connecting to Arduino on {port}...")
        ser = serial.Serial(port, baud_rate, timeout=1)
        time.sleep(2)  # Wait for the connection to establish
        print("Arduino connected successfully.")
        return ser
    except serial.SerialException as e:
        print(f"Error connecting to Arduino: {e}")
        print(f"Please check your COM port: '{port}'")
        print("Running in simulation mode. No signals will be sent.")
        return None

def send_to_arduino(ser, waste_type):
    """Sends a signal ('W' for wet, 'D' for dry) to the Arduino."""
    if ser is not None and ser.is_open:
        if waste_type == 'wet':
            ser.write(b'W')
            print("Sent 'W' (Wet) signal to Arduino")
        elif waste_type == 'dry':
            ser.write(b'D')
            print("Sent 'D' (Dry) signal to Arduino")

# --- Main Application Logic ---
def main():
    """Main function to run the live prediction loop."""
    
    # --- 1. Load Model and Setup Arduino ---
    print("Loading YOLO model...")
    try:
        model = YOLO(MODEL_PATH)
        print("YOLO model loaded successfully.")
    except Exception as e:
        print(f"Error loading model: {e}")
        print(f"Please make sure the '{MODEL_PATH}' file exists and 'ultralytics' is installed.")
        return
        
    arduino = setup_arduino(ARDUINO_PORT, BAUD_RATE)
    
    # --- 2. Start Camera Feed ---
    cap = cv2.VideoCapture(CAMERA_ID)
    
    if not cap.isOpened():
        print(f"Error: Could not open camera (ID: {CAMERA_ID}).")
        return

    print("\nStarting live prediction... Press SPACE to identify, 'q' to quit.")
    
    # --- 3. State Variables ---
    prediction_text = "Press SPACE to identify"
    box_coords = None
    box_color = (255, 255, 255) # White
    
    # --- 4. Prediction Loop ---
    while True:
        ret, frame = cap.read()
        if not ret:
            print("Failed to grab frame.")
            break
            
        display_frame = frame.copy()
        
        # --- 5. Check for User Input ---
        key = cv2.waitKey(1) & 0xFF

        if key == ord('q'):
            break
            
        if key == ord(' '): # SPACEBAR was pressed
            print("Identifying...")
            
            # --- 6. Run Detection & Prediction (ONCE) ---
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            blurred = cv2.GaussianBlur(gray, (7, 7), 0)
            _, thresh = cv2.threshold(blurred, 100, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
            contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            object_detected = False
            waste_type_found = False
            
            if contours:
                largest_contour = max(contours, key=cv2.contourArea)
                
                if cv2.contourArea(largest_contour) > MIN_OBJECT_AREA:
                    object_detected = True
                    x, y, w, h = cv2.boundingRect(largest_contour)
                    box_coords = (x, y, w, h) # Store coords for drawing
                    
                    roi = frame[y:y+h, x:x+w]
                    if roi.size > 0:
                        
                        results = model.predict(source=roi, verbose=False)
                        top5_indices = results[0].probs.top5
                        top5_confs = results[0].probs.top5conf
                        top5_names = [model.names[i] for i in top5_indices]

                        waste_type = None

                        for name, conf in zip(top5_names, top5_confs):
                            if conf < CONFIDENCE_THRESHOLD:
                                continue 

                            if name in wet_classes:
                                waste_type = 'wet'
                                break 
                            elif name in dry_classes:
                                waste_type = 'dry'
                                break 
                        
                        # --- Update State & Send Signal ---
                        if waste_type:
                            waste_type_found = True
                            prediction_text = f"{waste_type.capitalize()} Waste"
                            box_color = (0, 255, 0) # Green
                            print(f"Confident prediction: {prediction_text}")
                            send_to_arduino(arduino, waste_type)
            
            # --- If ANY check failed, reset to default state ---
            if not object_detected or not waste_type_found:
                print("Identification failed or object is not waste.")
                prediction_text = "Press SPACE to identify"
                box_color = (255, 255, 255) # White
                box_coords = None # Clear any previous box

        # --- 7. Draw Last Result (Every Frame) ---
        if box_coords:
            x, y, w, h = box_coords
            cv2.rectangle(display_frame, (x, y), (x + w, y + h), box_color, 3)
        
        # Draw the text
        (text_width, text_height), _ = cv2.getTextSize(prediction_text, cv2.FONT_HERSHEY_SIMPLEX, 1.2, 3)
        text_x = (display_frame.shape[1] - text_width) // 2
        text_y = 50 # Put text at the top
        cv2.putText(display_frame, prediction_text, (text_x, text_y), cv2.FONT_HERSHEY_SIMPLEX, 1.2, box_color, 3)

        # --- 8. Show the Final Frame ---
        cv2.imshow('Live Waste Classification', display_frame)

    # --- 9. Cleanup ---
    cap.release()
    cv2.destroyAllWindows()
    if arduino and arduino.is_open:
        arduino.close()
        print("Arduino connection closed.")

if __name__ == '__main__':
    main()