#include <Servo.h>

// --- Config ---
const int PIN_SERVO_WET = 8;
const int PIN_SERVO_DRY = 9;
const int PIN_TRIG = 11;
const int PIN_ECHO = 12;

const int FULL_THRESHOLD_CM = 10; // If distance < 10cm, Bin is Full

Servo wetServo;
Servo dryServo;
long duration;
int distance;
bool isFull = false;

// Debounce variables
unsigned long blockStartTime = 0;
bool blockageDetected = false;

void setup() {
  Serial.begin(9600);
  wetServo.attach(PIN_SERVO_WET);
  dryServo.attach(PIN_SERVO_DRY);
  wetServo.write(0);
  dryServo.write(0);
  pinMode(PIN_TRIG, OUTPUT);
  pinMode(PIN_ECHO, INPUT);
}

void loop() {
  // 1. Measure Distance
  digitalWrite(PIN_TRIG, LOW);
  delayMicroseconds(2);
  digitalWrite(PIN_TRIG, HIGH);
  delayMicroseconds(10);
  digitalWrite(PIN_TRIG, LOW);
  
  duration = pulseIn(PIN_ECHO, HIGH);
  distance = duration * 0.034 / 2;

  // 2. Check Bin Full Status
  if (distance > 0 && distance < FULL_THRESHOLD_CM) {
    if (!blockageDetected) {
      blockageDetected = true;
      blockStartTime = millis();
    } else {
      // Must be blocked for 2 seconds to count as full
      if (millis() - blockStartTime > 2000) { 
         if (!isFull) {
            isFull = true;
            Serial.println("STATUS_FULL");
         }
      }
    }
  } else {
    blockageDetected = false;
    if (isFull) {
       isFull = false;
       Serial.println("STATUS_OK");
    }
  }

  // 3. Execute Commands (Only if not full)
  if (Serial.available() > 0) {
    char c = Serial.read();
    
    if (!isFull) {
      if (c == 'W') {
        wetServo.write(90); 
        delay(3000);
        wetServo.write(0);  
      } 
      else if (c == 'D') {
        dryServo.write(90);
        delay(3000);
        dryServo.write(0);
      }
    }
  }
  delay(100);
}