import cv2
import time
import serial
import threading
from flask import Flask, render_template, Response, jsonify, request
from ultralytics import YOLO

# --- Configuration ---
MODEL_PATH = 'yolov8m-cls.pt' 
CAMERA_ID = 0           
ARDUINO_PORT = 'COM7'   # IMPORTANT: Change this to your Arduino Port (e.g., COM3, /dev/ttyUSB0)
BAUD_RATE = 9600
CONFIDENCE_THRESHOLD = 0.60

app = Flask(__name__)

# --- Global State ---
state = {
    "prediction": "Ready",
    "waste_type": "None", 
    "arduino_status": "Disconnected",
    "confidence": 0.0,
    "manual_trigger": False,
    "auto_mode": False,
    "bin_full": False
}

# --- Waste Classes ---
dry_classes = (
    'water_bottle', 'pop_bottle', 'beer_bottle', 'wine_bottle', 'paper_towel', 'envelope', 'book_jacket',
    'comic_book', 'menu', 'cardboard_box', 'carton', 'plastic_bag', 'garbage_truck', 'tin_can', 'milk_can',
    'beer_can', 'pill_bottle', 'packet', 'matchstick', 'nail', 'screw', 'ballpoint_pen', 'pencil_box',
    'paper_clip', 'rubber_eraser', 'wooden_spoon', 'plate', 'bowl', 'cup', 'beer_glass', 'wine_glass',
    'coffee_mug', 'Smartphone', 'iPod', 'analog_clock', 'wall_clock',
    'sunglasses','candle', 'nail', 'paintbrush', 'diaper', 'rubber_eraser', 'toilet_tissue','file', 'necklace', 'notebook', 'perfume','purse', 'remote_control',
    'scale', 'soup_bowl', 'comic_book',
    'vase', 'tray', 'tennis_ball', 'safety_pin', 'pencil_sharpener', 'mask', 'lotion', 'lighter', 'lens_cap','golf_ball',
    'handkerchief', 'coffeepot', 'Crock_Pot', 'bottlecap', 'can_opener','cleaver',
    'bath_towel', 'packet', 'apron', 'lighter' )

wet_classes = (
    'banana', 'apple', 'strawberry', 'orange', 'lemon', 'pineapple', 'jackfruit', 'custard_apple', 'pomegranate',
    'fig', 'guava', 'mango', 'grapes', 'watermelon', 'cucumber', 'eggplant',
    'bell_pepper', 'head_cabbage', 'broccoli', 'cauliflower', 'zucchini', 'spaghetti_squash', 'acorn_squash',
    'butternut_squash', 'mushroom', 'corn', 'ice_cream', 'pizza', 'dough', 'meat_loaf',
    'burrito', 'chocolate_sauce', 'red_wine', 'guacamole', 'consomme', 'trifle', 'ice_lolly', 
    'French_loaf', 'bagel', 'cheeseburger', 'hotdog', 'mashed_potato', 'rotisserie', 'drumstick', 'buckeye'
)    

# --- Hardware Setup ---
try:
    model = YOLO(MODEL_PATH)
    print("YOLO Model Loaded.")
except Exception as e:
    print(f"Error Loading Model: {e}")
    model = None

arduino = None
try:
    arduino = serial.Serial(ARDUINO_PORT, BAUD_RATE, timeout=1)
    state["arduino_status"] = "Connected"
except:
    state["arduino_status"] = "Simulation Mode"

def send_signal(waste_type):
    """Sends command to Arduino"""
    if arduino and arduino.is_open:
        try:
            if waste_type == 'wet':
                arduino.write(b'W')
            elif waste_type == 'dry':
                arduino.write(b'D')
        except Exception as e:
            print(f"Serial Write Error: {e}")

def arduino_listener():
    """Background thread to listen for Full/Empty signals from Arduino"""
    global arduino
    while True:
        if arduino and arduino.is_open:
            try:
                if arduino.in_waiting > 0:
                    # Read line from Arduino
                    line = arduino.readline().decode('utf-8', errors='ignore').strip()
                    
                    if "STATUS_FULL" in line:
                        if not state["bin_full"]:
                            print("ALERT: Bin is Full!")
                        state["bin_full"] = True
                        state["prediction"] = "BIN IS FULL!"
                    
                    elif "STATUS_OK" in line:
                        if state["bin_full"]:
                            print("Bin Cleared. Resuming.")
                        state["bin_full"] = False
                        
            except Exception as e:
                print(f"Serial Read Error: {e}")
                state["arduino_status"] = "Error"
        time.sleep(0.5)

# --- Camera Loop ---
def generate_frames():
    cap = cv2.VideoCapture(CAMERA_ID)
    
    while True:
        success, frame = cap.read()
        if not success:
            break

        # --- LOGIC GUARD: If bin is full, stop processing ---
        if state["bin_full"]:
            # Draw big red warning on video
            overlay = frame.copy()
            cv2.rectangle(overlay, (0, 0), (frame.shape[1], frame.shape[0]), (0, 0, 255), -1)
            cv2.addWeighted(overlay, 0.3, frame, 0.7, 0, frame)
            
            cv2.putText(frame, "BIN FULL", (50, 200), cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 0, 255), 5)
            cv2.putText(frame, "Please Empty Bin", (50, 280), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
            
            state["manual_trigger"] = False
        
        else:
            # Normal Processing
            if state["auto_mode"] or state["manual_trigger"]:
                if model:
                    results = model.predict(source=frame, verbose=False)
                    top5_indices = results[0].probs.top5
                    top5_confs = results[0].probs.top5conf
                    top5_names = [model.names[i] for i in top5_indices]

                    found_waste = False
                    for name, conf in zip(top5_names, top5_confs):
                        if conf < CONFIDENCE_THRESHOLD: continue
                        
                        if name in wet_classes:
                            state["waste_type"] = "wet"
                            state["prediction"] = "Wet Waste" # Changed to generic text
                            found_waste = True
                        elif name in dry_classes:
                            state["waste_type"] = "dry"
                            state["prediction"] = "Dry Waste" # Changed to generic text
                            found_waste = True
                        
                        if found_waste:
                            state["confidence"] = float(conf)
                            send_signal(state["waste_type"])
                            break
                    
                    if not found_waste:
                        state["prediction"] = "Unknown Object"
                        state["waste_type"] = "None"
                
                state["manual_trigger"] = False

            # Visual Feedback on Frame
            if state["waste_type"] == 'wet':
                cv2.putText(frame, "WET WASTE", (30, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 3)
            elif state["waste_type"] == 'dry':
                cv2.putText(frame, "DRY WASTE", (30, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 3)

        # Encode frame for web
        ret, buffer = cv2.imencode('.jpg', frame)
        frame_bytes = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

# --- Flask Routes ---
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/status')
def get_status():
    return jsonify(state)

@app.route('/trigger', methods=['POST'])
def trigger():
    if state["bin_full"]:
        return jsonify({"success": False, "message": "Bin is Full"})
    state["manual_trigger"] = True
    return jsonify({"success": True})

@app.route('/toggle_auto', methods=['POST'])
def toggle_auto():
    state["auto_mode"] = not state["auto_mode"]
    return jsonify({"auto_mode": state["auto_mode"]})

if __name__ == '__main__':
    # Start the Serial Listener in background
    t = threading.Thread(target=arduino_listener)
    t.daemon = True 
    t.start()
    
    print("Starting Web Server on Port 5000...")
    app.run(debug=True, port=5000, threaded=True)