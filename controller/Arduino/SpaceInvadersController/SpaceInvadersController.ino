/*
 * Global variables
 */
// Acceleration values recorded from the readAccelSensor() function
int ax = 0; int ay = 0; int az = 0;
int ppg = 0;        // PPG from readPhotoSensor() (in Photodetector tab)
int sampleTime = 0; // Time of last sample (in Sampling tab)
bool sending;

// Super Awesome solution no bueno controller
int lastButtonState = HIGH;  // Store previous state
unsigned long lastDebounceTime = 0;
const unsigned long debounceDelay = 50;  // 50ms debounce time

// ---- Sensitivity Levels ----
int sensitivityLevels[] = {10, 20, 35};  // Low, Medium, High
String sensitivityLabels[] = {"Low", "Medium", "High"};  // Display names
int currentSensitivityIndex = 0;         // Default to Low sensitivity (10°)
int lastButton14State = HIGH;            // Store previous state for pin 14
unsigned long lastDebounceTime14 = 0;    // Debounce timing for pin 14
const unsigned long debounceDelay14 = 300; // 300ms delay to prevent rapid cycling

/*
 * Initialize the various components of the wearable
 */
void setup() {
  setupAccelSensor();
  setupCommunication();
  setupDisplay();
  setupPhotoSensor();
  sending = false;

  pinMode(12, INPUT_PULLUP);  // **ENABLE INTERNAL PULL-UP RESISTOR**
  pinMode(14, INPUT_PULLUP);  // **Button for sensitivity adjustment**
  pinMode(17, OUTPUT);        // **LED indicator for hits**

  writeDisplay("Ready...", 1, true);
  writeDisplay("Set...", 2, false);
  writeDisplay("Play!", 3, false);
  writeDisplay("Sens: Low", 3, true);  // Default sensitivity display
}

/*
 * The main processing loop
 */
void loop() {
  // Read accelerometer values
  readAccelSensor();

  // ---- Button Handling for Fire Button (Pin 12) ----
  int buttonState = 0;  // Default to not pressed
  int buttonReading = digitalRead(12);
  
  if (buttonReading != lastButtonState) {
    lastDebounceTime = millis();  // Reset debounce timer
  }

  if ((millis() - lastDebounceTime) > debounceDelay) {
    if (buttonReading == LOW && lastButtonState == LOW) {  
      buttonState = 1;  // Register button press
    }
  }

  lastButtonState = buttonReading;  // Store current state for next loop

  // ---- Button Handling for Sensitivity Adjustment (Pin 14) ----
  int button14Reading = digitalRead(14);
  
  if (button14Reading != lastButton14State) {
    lastDebounceTime14 = millis();  // Reset debounce timer
  }

  if ((millis() - lastDebounceTime14) > debounceDelay14) {
    if (button14Reading == LOW && lastButton14State == LOW) {  
      currentSensitivityIndex = (currentSensitivityIndex + 1) % 3;  // Cycle 0 → 1 → 2 → 0
      // Update display with new sensitivity level
      String sensitivityMessage = "Sens: " + sensitivityLabels[currentSensitivityIndex];
      writeDisplay(sensitivityMessage.c_str(), 3, true);
      delay(50);
      Serial.print("Sensitivity changed to: ");
      Serial.println(sensitivityLevels[currentSensitivityIndex]); // Debugging message

    }
  }

  lastButton14State = button14Reading;  // Store state for next loop

  // ---- Format and Send Accelerometer Data ----
  String response = String(ax) + "," + String(ay) + "," + String(az) + "," 
                  + String(buttonState) + "," + String(sensitivityLevels[currentSensitivityIndex]);
  sendMessage(response);

  // ---- Parse Command from Python ----
  String command = receiveMessage();

  if (command == "stop") {
    sending = false;
    writeDisplay("Controller: Off", 0, true);
  }
  else if (command == "start") {
    sending = true;
    writeDisplay("Controller: On", 0, true);
  }
  else if (command.startsWith("LIVES")) { 
    // Expected format: LIVES,<lives>,<hit_flag>
    int firstComma = command.indexOf(',');
    int secondComma = command.indexOf(',', firstComma + 1);

    if (firstComma != -1 && secondComma != -1) {
      int currentLives = command.substring(firstComma + 1, secondComma).toInt();
      int hitFlag = command.substring(secondComma + 1).toInt();

      // Update display with the number of lives
      String livesMessage = "Lives: " + String(currentLives);
      writeDisplay(livesMessage.c_str(), 1, true);

      // Turn LED on if hit, off otherwise
      if (hitFlag == 1) {
        digitalWrite(17, HIGH);
        delay(50);
      } else {
        digitalWrite(17, LOW);
      }
    }
  }

  delay(20);  // Maintain 50Hz update rate
}