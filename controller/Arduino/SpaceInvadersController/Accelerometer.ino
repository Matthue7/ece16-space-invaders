// ----------------------------------------------------------------------------------------------------
// =========== Accelerometer Sensor with Calibration ============ 
// ----------------------------------------------------------------------------------------------------

/*
 * Configure the analog input pins to the accelerometer's 3 axes
 */
const int X_PIN = A4;
const int Y_PIN = A3;
const int Z_PIN = A2;
const int CALIBRATION_BUTTON = 13;  // Button for calibration

/*
 * Set the "zero" states when each axis is neutral
 */
int X_ZERO = 1850;
int Y_ZERO = 1850;
int Z_ZERO = 1950;

/*
 * Configure the analog pins to be treated as inputs by the MCU
 */
void setupAccelSensor() {
  pinMode(X_PIN, INPUT);
  pinMode(Y_PIN, INPUT);
  pinMode(Z_PIN, INPUT);
  pinMode(CALIBRATION_BUTTON, INPUT_PULLUP); // Use internal pull-up

  Serial.println("Press button on GPIO 12 to calibrate accelerometer.");
}

/*
 * Read a sample from the accelerometer's 3 axes
 */
void readAccelSensor() {
  ax = analogRead(X_PIN);
  ay = analogRead(Y_PIN);
  az = analogRead(Z_PIN);
}

/*
 * Calibrate the accelerometer by setting new zero values
 */
void calibrateAccelerometer() {
  Serial.println("Calibrating accelerometer... Keep it flat!");

  delay(1000); // Give time to adjust position
  
  X_ZERO = analogRead(X_PIN);
  Y_ZERO = analogRead(Y_PIN);
  Z_ZERO = analogRead(Z_PIN);

  Serial.print("New X_ZERO: "); Serial.println(X_ZERO);
  Serial.print("New Y_ZERO: "); Serial.println(Y_ZERO);
  Serial.print("New Z_ZERO: "); Serial.println(Z_ZERO);

  writeDisplay("Calibrated!", 1, true);
  delay(500);
}

/*
 * Get the orientation of the accelerometer
 * Returns orientation as an integer:
 * 0 == flat
 * 1 == up
 * 2 == down
 * 3 == left
 * 4 == right
 */
int getOrientation() {
  int orientation = 0;

  // Subtract out the zeros
  int x = ax - X_ZERO;
  int y = ay - Y_ZERO;
  int z = az - Z_ZERO;

  // Dead zone threshold (adjustable)
  const int DEAD_ZONE = 80;  // Ignore movements below this threshold

  // If ax has biggest magnitude, it's either left or right
  if(abs(x) >= abs(y) && abs(x) >= abs(z) && abs(x) > DEAD_ZONE) {
    if (x < 0) // left
      orientation = 3;
    else
      orientation = 4;
  }
  // If ay has biggest magnitude, it's either up or down
  else if(abs(y) >= abs(x) && abs(y) >= abs(z) && abs(y) > DEAD_ZONE) {
    if (y < 0) // up
      orientation = 1;
    else // down
      orientation = 2;
  }
  // If az biggest magnitude, it's flat (or upside-down)
  else if(abs(z) > abs(x) && abs(z) >= abs(y)) {
    orientation = 0; // flat
  }

  return orientation;
}