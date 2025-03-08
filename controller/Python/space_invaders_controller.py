"""
@author: Ramsin Khoshabeh
"""

import time
import socket
import numpy as np
import cv2
import pyautogui  # For screen capture
import threading  # I thought I removed threading but it is still needed for an event

from ECE16Lib.Communication import Communication
import ECE16Lib.DSP as dsp

# ---- Socket Setup ----
host = "127.0.0.1"
port = 65432
mySocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
mySocket.connect((host, port))
mySocket.setblocking(False)

# ---- Orientation Detection Parameters ----
DEAD_ZONE = 5       # Degrees - Ignore small tilt
TILT_THRESHOLD = 10 # Degrees - Minimum tilt to detect Left/Right

# ---- Offset & Scaling Correction ----
OFFSET_CORRECTION = 45
SCALE_FACTOR = 90 / (50 - 40)  # Stretch final roll from ~-90° to 90°

# ---- Lives Tracking Parameters ----
LIVES_REGION = (1175, 240, 95, 80)  # Region for capturing lives
last_lives = 3                      # Start with 3 lives
hit_detected = False
last_image = None  # For comparing screenshots

def capture_lives_section():
    """Capture the lives section from the screen and convert it to grayscale."""
    screenshot = pyautogui.screenshot(region=LIVES_REGION)
    img = np.array(screenshot)
    gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
    return gray

def count_lives():
    """Use edge detection and contour finding to count the number of ships."""
    global last_image, last_lives

    lives_img = capture_lives_section()

    # Only process if the screen changed significantly
    if last_image is not None:
        diff = cv2.absdiff(lives_img, last_image)
        if np.mean(diff) < 2:  # No significant change
            return last_lives

    last_image = lives_img

    # Apply edge detection
    edges = cv2.Canny(lives_img, 50, 200)

    # Find contours
    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    # Filter out small contours
    min_contour_area = 50
    spaceship_contours = [cnt for cnt in contours if cv2.contourArea(cnt) > min_contour_area]

    return len(spaceship_contours)


class PygameController:
    def __init__(self, serial_name, baud_rate):
        self.comms = Communication(serial_name, baud_rate)
        self.running = True

        # Event used to lock loop frequency to ~50 Hz
        self.movement_update_event = threading.Event()

        # Track when we last did a lives capture
        self.lives_check_timer = time.perf_counter()

    def process_orientation(self, message):
        """
        Takes in raw accelerometer data, applies DSP, and determines orientation.
        """
        try:
            data = message.split(",")

            if len(data) != 5:  # Expecting ax, ay, az, button, sensitivity
                return None, None, None

            ax, ay, az, button, sensitivity = map(int, data)

            # Update the sensitivity threshold dynamically
            self.sensitivity_threshold = sensitivity

            # Simple moving average to reduce noise
            ax = dsp.moving_average(np.array([ax]), win=5)[0]
            ay = dsp.moving_average(np.array([ay]), win=5)[0]
            az = dsp.moving_average(np.array([az]), win=5)[0]

            # Compute roll (left/right tilt)
            roll = np.arctan2(ay, az) * (180 / np.pi)

            # Apply offset + scale
            roll_corrected = (roll - OFFSET_CORRECTION) * SCALE_FACTOR

            # Determine orientation dynamically using `self.sensitivity_threshold`
            if abs(roll_corrected) < DEAD_ZONE:
                orientation = "Neutral"
            elif roll_corrected < -self.sensitivity_threshold:
                print(roll)
                print(ay,az)
                orientation = "Left"
            elif roll_corrected > self.sensitivity_threshold:
                orientation = "Right"
            else:
                orientation = "Neutral"

            return orientation, button, self.sensitivity_threshold

        except ValueError:
            print(f"ERROR: Could not convert to int -> {message}")
            return None, None, None

    def run(self):
        """Main loop at ~50 Hz, also checks lives at ~5 Hz in the same loop."""
        global last_lives, hit_detected

        # Stop any existing data streaming on Arduino
        self.comms.send_message("stop")
        input("Ready to start? Hit enter to begin.\n")
        self.comms.send_message("start")

        print("Use <CTRL+C> to exit the program.\n")

        # Clear the serial buffer once before we begin
        self.comms.clear()

        # 50 Hz => 20 ms per iteration
        desired_period = 1.0 / 50.0

        try:
            while self.running:
                loop_start = time.perf_counter()

                # 1. Read incoming accelerometer message
                message = self.comms.receive_message()
                if message is not None:
                    orientation, button, sensitivity = self.process_orientation(message)
                    # 2. Send movement commands
                    if orientation == "Left":
                        mySocket.send("LEFT".encode("UTF-8"))
                    elif orientation == "Right":
                        mySocket.send("RIGHT".encode("UTF-8"))

                    if button == 1:
                        mySocket.send("FIRE".encode("UTF-8"))

                # 3. Check if it's time to update lives (every 200 ms)
                now = time.perf_counter()
                if (now - self.lives_check_timer) >= 0.2:
                    current_lives = count_lives()

                    if current_lives < last_lives:
                        print(f"💥 HIT! Lives decreased from {last_lives} → {current_lives}")
                        hit_detected = True
                    else:
                        hit_detected = False

                    if current_lives == 0:
                        print("💀 GAME OVER! No lives remaining.")

                    # Send lives count and hit detection to Arduino
                    lives_message = f"LIVES,{current_lives},{int(hit_detected)}"
                    self.comms.send_message(lives_message)

                    last_lives = current_lives
                    self.lives_check_timer = now

        except (Exception, KeyboardInterrupt) as e:
            print(e)
            self.running = False

        # Cleanup
        print("Exiting the program.")
        self.comms.send_message("stop")
        self.comms.close()
        mySocket.send("QUIT".encode("UTF-8"))
        mySocket.close()


if __name__ == "__main__":
    serial_name = "/dev/cu.BTDemo"
    baud_rate = 115200
    controller = PygameController(serial_name, baud_rate)

    try:
        controller.run()
    except KeyboardInterrupt:
        print("\nUser exited program.")
        controller.running = False