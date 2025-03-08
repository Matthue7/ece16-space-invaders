import cv2
import numpy as np

# Start video capture
cap = cv2.VideoCapture(0)  # 0 for default webcam

while True:
    # Read frame from the camera
    ret, frame = cap.read()
    if not ret:
        break

    # Convert to grayscale
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    # Apply Gaussian blur
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)

    # Apply Canny edge detection
    edges = cv2.Canny(blurred, 50, 150)

    # Find contours
    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    for contour in contours:
        area = cv2.contourArea(contour)

        # **Filter out small noise contours**
        if area < 1000:  # Adjust this threshold based on testing
            continue

        # Approximate the contour
        perimeter = cv2.arcLength(contour, True)
        epsilon = 0.02 * perimeter
        approx = cv2.approxPolyDP(contour, epsilon, True)

        # Convex hull for solidity calculation
        hull = cv2.convexHull(contour)
        hull_area = cv2.contourArea(hull)
        solidity = area / hull_area if hull_area > 0 else 0

        # Get bounding box for text placement
        x, y, w, h = cv2.boundingRect(approx)
        cx, cy = x + w // 2, y + h // 2

        # Identify shape
        num_vertices = len(approx)
        shape_name = "Unknown"

        if num_vertices == 3:
            shape_name = "Triangle"
        elif num_vertices == 4:
            aspect_ratio = w / float(h)
            if 0.9 <= aspect_ratio <= 1.1:
                shape_name = "Square"
            else:
                shape_name = "Rectangle"
        elif num_vertices == 5:
            shape_name = "Pentagon"
        elif num_vertices > 5:
            # **Check circularity to confirm it's a circle**
            circularity = (4 * np.pi * area) / (perimeter ** 2)
            if 0.7 <= circularity <= 1.2:  # Close to 1 means a good circle
                shape_name = "Circle"

        # **Confidence Filtering**
        if solidity < 0.85 and shape_name != "Circle":  # Filter out bad shapes
            continue

        # Draw the shape and label it
        cv2.drawContours(frame, [approx], -1, (0, 255, 0), 2)
        cv2.putText(frame, shape_name, (cx - 40, cy), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 0), 2)

    # Show the frame
    cv2.imshow("Live Shape Detection", frame)

    # Press 'q' to quit
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Release resources
cap.release()
cv2.destroyAllWindows()