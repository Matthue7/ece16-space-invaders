import cv2
import numpy as np
import pyautogui  # Now installed
import time

# Define region of the screen where the "Lives" counter is
LIVES_REGION = (1175, 240, 95, 80)  # Adjust this based on your screen

def capture_lives_section():
    """ Captures the lives section from the screen and converts it to grayscale. """
    screenshot = pyautogui.screenshot(region=LIVES_REGION)
    img = np.array(screenshot)
    gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)  # Convert to grayscale
    return gray

def count_lives():
    """ Uses edge detection and contour finding to count the number of ships. """
    lives_img = capture_lives_section()

    # Apply edge detection to highlight ships
    edges = cv2.Canny(lives_img, 50, 200)

    # Find contours (shapes) in the image
    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    # Filter out noise: Only count reasonably sized contours
    min_contour_area = 50  # Adjust this based on testing
    spaceship_contours = [cnt for cnt in contours if cv2.contourArea(cnt) > min_contour_area]

    # Count the number of detected spaceship lives
    num_lives = len(spaceship_contours)
    return num_lives

def track_lives():
    """ Continuously tracks lives in real-time. """
    print("🎮 Tracking lives in real-time. Press CTRL+C to stop.")

    while True:
        num_lives = count_lives()

        if num_lives == 0:
            print("💀 GAME OVER! No lives remaining.")
        else:
            print(f"🚀 Lives Remaining: {num_lives}")

        time.sleep(1)  # Update every second

if __name__ == "__main__":
    try:
        track_lives()
    except KeyboardInterrupt:
        print("\nTracking stopped.")