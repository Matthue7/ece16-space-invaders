import serial
import time
import numpy as np
import ECE16Lib.DSP as dsp

# ---- Serial Setup ----
SERIAL_PORT = "/dev/cu.BTDemo"  # Change this to your ESP32 port
BAUD_RATE = 115200

# ---- Orientation Detection Parameters ----
DEAD_ZONE = 5  # Degrees - Ignore movements below this angle
TILT_THRESHOLD = 10  # Degrees - Minimum tilt to detect Left/Right

# ---- Offset & Scaling Correction ----
OFFSET_CORRECTION = 45  # Shift roll by this amount to center it at 0°
SCALE_FACTOR = 90 / (50 - 40)  # Stretch the final readings to match -90° to 90°

def process_orientation():
    """ Reads accelerometer data, applies DSP, and detects orientation """
    ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
    time.sleep(2)  # Allow time for serial connection to stabilize

    while True:
        try:
            line = ser.readline().decode().strip()
            if not line:
                continue

            # Parse CSV data
            data = line.split(",")
            if len(data) != 4:
                continue

            # Convert to integers
            try:
                ax, ay, az, button = map(int, data)
            except ValueError:
                print(f"ERROR: Could not convert to int -> {data}")
                continue

            # ---- Apply DSP Filtering ----
            ax = dsp.moving_average(np.array([ax]), win=5)[0]  # Smooth out noise
            ay = dsp.moving_average(np.array([ay]), win=5)[0]
            az = dsp.moving_average(np.array([az]), win=5)[0]

            # ---- Compute Tilt Angles ----
            roll = np.arctan2(ay, az) * (180 / np.pi)  # Left/Right

            # ---- Apply Offset & Scaling ----
            roll_corrected = (roll - OFFSET_CORRECTION) * SCALE_FACTOR  # Normalize roll

            # ---- Determine Orientation ----
            if abs(roll_corrected) < DEAD_ZONE:
                orientation = "Neutral"
            elif roll_corrected < -TILT_THRESHOLD:
                orientation = "Left"
            elif roll_corrected > TILT_THRESHOLD:
                orientation = "Right"
            else:
                orientation = "Neutral"

            # ---- Print Processed Output ----
            print(f"Ax: {ax:.2f}, Ay: {ay:.2f}, Az: {az:.2f} | Roll: {roll_corrected:.2f}° | Orientation: {orientation} | Button: {'Pressed' if button else 'Not Pressed'}")

        except KeyboardInterrupt:
            print("\nStopping script...")
            ser.close()
            break

# ---- Run Processing ----
if __name__ == "__main__":
    process_orientation()