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
    # replaced single bin flag with two separate flags
    "bin_full_wet": False,
    "bin_full_dry": False
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
    """Sends command to Arduino, but block if that specific bin is full."""
    if arduino and arduino.is_open:
        try:
            if waste_type == 'wet':
                if state.get("bin_full_wet"):
                    print("Skipped sending W: Wet bin is full.")
                    state["prediction"] = "WET BIN FULL - Command skipped"
                    return
                arduino.write(b'W')
            elif waste_type == 'dry':
                if state.get("bin_full_dry"):
                    print("Skipped sending D: Dry bin is full.")
                    state["prediction"] = "DRY BIN FULL - Command skipped"
                    return
                arduino.write(b'D')
        except Exception as e:
            print(f"Serial Write Error: {e}")

def arduino_listener():
    """Background thread to listen for Full/Empty signals from Arduino.
       Expecting: WET_FULL / WET_OK / DRY_FULL / DRY_OK (or similar strings)."""
    global arduino
    while True:
        if arduino and arduino.is_open:
            try:
                if arduino.in_waiting > 0:
                    # Read line from Arduino
                    line = arduino.readline().decode('utf-8', errors='ignore').strip()
                    if not line:
                        continue

                    # Normalize for easier checks
                    text = line.upper()
                    print(f"[ARDUINO] {text}")

                    # Wet bin signals
                    if "WET_FULL" in text or "WET_FULL" == text or "STATUS_WET_FULL" in text:
                        if not state["bin_full_wet"]:
                            print("ALERT: WET bin is Full!")
                        state["bin_full_wet"] = True
                        state["prediction"] = "WET BIN IS FULL!"

                    elif "WET_OK" in text or "WET_CLEAR" in text or "STATUS_WET_OK" in text:
                        if state["bin_full_wet"]:
                            print("WET bin Cleared. Resuming wet operations.")
                        state["bin_full_wet"] = False

                    # Dry bin signals
                    elif "DRY_FULL" in text or "STATUS_DRY_FULL" in text:
                        if not state["bin_full_dry"]:
                            print("ALERT: DRY bin is Full!")
                        state["bin_full_dry"] = True
                        state["prediction"] = "DRY BIN IS FULL!"

                    elif "DRY_OK" in text or "DRY_CLEAR" in text or "STATUS_DRY_OK" in text:
                        if state["bin_full_dry"]:
                            print("DRY bin Cleared. Resuming dry operations.")
                        state["bin_full_dry"] = False

                    # Backwards compatibility: if Arduino still sends STATUS_FULL / STATUS_OK
                    elif "STATUS_FULL" in text:
                        print("ALERT: Generic STATUS_FULL received - marking both bins full (compat mode).")
                        state["bin_full_wet"] = True
                        state["bin_full_dry"] = True
                        state["prediction"] = "BIN IS FULL!"
                    elif "STATUS_OK" in text:
                        print("STATUS_OK received - clearing both bins (compat mode).")
                        state["bin_full_wet"] = False
                        state["bin_full_dry"] = False

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

        # If either bin is full, show overlay and prevent actions
        if state["bin_full_wet"] or state["bin_full_dry"]:
            overlay = frame.copy()
            cv2.rectangle(overlay, (0, 0), (frame.shape[1], frame.shape[0]), (0, 0, 255), -1)
            cv2.addWeighted(overlay, 0.3, frame, 0.7, 0, frame)

            y = 150
            if state["bin_full_wet"]:
                cv2.putText(frame, "WET BIN FULL", (50, y), cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 0, 255), 5)
                y += 90
            if state["bin_full_dry"]:
                cv2.putText(frame, "DRY BIN FULL", (50, y), cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 0, 255), 5)
                y += 90

            cv2.putText(frame, "Please Empty Bin(s)", (50, y+20), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)

            # Prevent manual trigger while any bin is full
            state["manual_trigger"] = False

        else:
            # Normal Processing
            if state["auto_mode"] or state["manual_trigger"]:
                if model:
                    results = model.predict(source=frame, verbose=False)
                    # assume classifier model that gives probs.top5 & top5conf
                    top5_indices = results[0].probs.top5
                    top5_confs = results[0].probs.top5conf
                    top5_names = [model.names[i] for i in top5_indices]

                    found_waste = False
                    for name, conf in zip(top5_names, top5_confs):
                        if conf < CONFIDENCE_THRESHOLD:
                            continue

                        if name in wet_classes:
                            state["waste_type"] = "wet"
                            state["prediction"] = "Wet Waste"
                            found_waste = True
                        elif name in dry_classes:
                            state["waste_type"] = "dry"
                            state["prediction"] = "Dry Waste"
                            found_waste = True

                        if found_waste:
                            state["confidence"] = float(conf)
                            # send signal, but send_signal will itself check per-bin full flags
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
    # If either bin is full block trigger and inform user which bin(s)
    if state["bin_full_wet"] or state["bin_full_dry"]:
        msg = "Bin(s) full:"
        if state["bin_full_wet"]:
            msg += " WET"
        if state["bin_full_dry"]:
            msg += " DRY"
        return jsonify({"success": False, "message": msg.strip()})
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
