#include <Servo.h>

// --- Config ---
const int PIN_SERVO_WET = 8;
const int PIN_SERVO_DRY = 9;

// --- ORIGINAL Ultrasonic (Wet Bin) ---
const int PIN_TRIG = 11;
const int PIN_ECHO = 12;

// --- ADDED Ultrasonic (Dry Bin) ---
const int PIN_TRIG2 = 6;
const int PIN_ECHO2 = 7;

const int FULL_THRESHOLD_CM = 10; // If distance < 10cm, Bin is Full

Servo wetServo;
Servo dryServo;

long duration;
int distance;
bool isFull = false;   // OLD wet-bin status

// Debounce variables (OLD)
unsigned long blockStartTime = 0;
bool blockageDetected = false;

// --- NEW variables for second ultrasonic (Dry bin) ---
long duration2;
int distance2;
bool isFullDry = false;
unsigned long blockStartTime2 = 0;
bool blockageDetected2 = false;

void setup() {
  Serial.begin(9600);

  wetServo.attach(PIN_SERVO_WET);
  dryServo.attach(PIN_SERVO_DRY);

  wetServo.write(0);
  dryServo.write(0);

  // ORIGINAL Ultrasonic
  pinMode(PIN_TRIG, OUTPUT);
  pinMode(PIN_ECHO, INPUT);

  // NEW Dry-bin ultrasonic
  pinMode(PIN_TRIG2, OUTPUT);
  pinMode(PIN_ECHO2, INPUT);
}

void loop() {

  // ---------------------------------------------------
  // 1. Measure Distance (WET bin – ORIGINAL)
  // ---------------------------------------------------
  digitalWrite(PIN_TRIG, LOW);
  delayMicroseconds(2);
  digitalWrite(PIN_TRIG, HIGH);
  delayMicroseconds(10);
  digitalWrite(PIN_TRIG, LOW);
  
  duration = pulseIn(PIN_ECHO, HIGH);
  distance = duration * 0.034 / 2;

  // ---------------------------------------------------
  // 1B. Measure Distance for DRY bin (NEW SENSOR)
  // ---------------------------------------------------
  digitalWrite(PIN_TRIG2, LOW);
  delayMicroseconds(2);
  digitalWrite(PIN_TRIG2, HIGH);
  delayMicroseconds(10);
  digitalWrite(PIN_TRIG2, LOW);

  duration2 = pulseIn(PIN_ECHO2, HIGH);
  distance2 = duration2 * 0.034 / 2;

  // ---------------------------------------------------
  // 2. Check FULL status for WET bin (ORIGINAL LOGIC)
  // ---------------------------------------------------
  if (distance > 0 && distance < FULL_THRESHOLD_CM) {
    if (!blockageDetected) {
      blockageDetected = true;
      blockStartTime = millis();
    } else {
      if (millis() - blockStartTime > 2000) {
        if (!isFull) {
          isFull = true;
          Serial.println("WET_FULL");
        }
      }
    }
  } else {
    blockageDetected = false;
    if (isFull) {
      isFull = false;
      Serial.println("WET_OK");
    }
  }

  // ---------------------------------------------------
  // 2B. Check FULL status for DRY bin (NEW)
  // ---------------------------------------------------
  if (distance2 > 0 && distance2 < FULL_THRESHOLD_CM) {
    if (!blockageDetected2) {
      blockageDetected2 = true;
      blockStartTime2 = millis();
    } else {
      if (millis() - blockStartTime2 > 2000) {
        if (!isFullDry) {
          isFullDry = true;
          Serial.println("DRY_FULL");
        }
      }
    }
  } else {
    blockageDetected2 = false;
    if (isFullDry) {
      isFullDry = false;
      Serial.println("DRY_OK");
    }
  }

  // ---------------------------------------------------
  // 3. Execute Commands (Only if both bins NOT full)
  // ---------------------------------------------------
  if (Serial.available() > 0) {
    char c = Serial.read();

    // Prevent servo opening if its respective bin is FULL
    if (c == 'W' && !isFull) {
      wetServo.write(90);
      delay(3000);
      wetServo.write(0);
    }
    else if (c == 'D' && !isFullDry) {
      dryServo.write(90);
      delay(3000);
      dryServo.write(0);
    }
  }

  delay(100);
}
