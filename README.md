Smart Waste Sorter 
A complete system to sort Wet vs. Dry waste using AI, prevent bin overflow using sensors, and control servos for automation.
Features
AI Sorting: Uses YOLOv8 to identify trash.
Dual Bins: Separate servo motors for Wet (Pin 8) and Dry (Pin 9).
Overflow Protection: Ultrasonic sensor (Pin 11/12) locks system if bin is full.
Web GUI: Live video feed and controls via browser.

Setup Guide

1. Hardware Connections (Arduino)
Wet Servo: Signal Pin -> 8
Dry Servo: Signal Pin -> 9
Ultrasonic Sensor Trig: Pin -> 11
Ultrasonic Sensor Echo: Pin -> 12
Power: Ensure external power for Servos if they are large.

2. Software Installation
Install Python (v3.8+).
Install libraries:
pip install -r requirements.txt
Place your model file 'yolov8m-cls.pt' inside this folder.

3. Running the Project
Plug in Arduino.
Check Device Manager for COM Port (e.g., COM3).
Update 'server.py' line: ARDUINO_PORT = 'COM3' (or whatever yours is).
Run the server:
python server.py
Open browser to: https://www.google.com/search?q=http://127.0.0.1:5000
