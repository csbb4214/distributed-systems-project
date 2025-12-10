import sys
import random
from typing import Tuple

import cv2
import numpy as np


# ---------------------------------------------------------
# Simple lightweight fire detection using color heuristics
# ---------------------------------------------------------
def detect_fire(frame: np.ndarray) -> float:
    """
    Returns a fire confidence [0.0 – 1.0] using simple color thresholding.
    """

    # Convert to HSV (better for fire color range detection)
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

    # Simple fire-like color range (red/orange)
    lower = np.array([0, 170, 150], dtype=np.uint8)
    upper = np.array([10, 255, 255], dtype=np.uint8)

    mask = cv2.inRange(hsv, lower, upper)
    fire_pixels = np.sum(mask > 0)
    total_pixels = frame.shape[0] * frame.shape[1]

    confidence = fire_pixels / total_pixels
    return float(confidence)

# ---------------------------------------------------------
# Simple lightweight smoke detection using color heuristics
# ---------------------------------------------------------
def detect_smoke(frame: np.ndarray) -> float:
    """
    Returns a fire confidence [0.0 – 1.0] using simple color thresholding.
    """

    # Convert to HSV (better for fire color range detection)
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

    # Simple smoke-like color range (lightgrey/darkgrey)
    lower = np.array([0, 0, 150], dtype=np.uint8)
    upper = np.array([180, 50, 255], dtype=np.uint8)

    mask = cv2.inRange(hsv, lower, upper)
    fire_pixels = np.sum(mask > 0)
    total_pixels = frame.shape[0] * frame.shape[1]

    confidence = fire_pixels / total_pixels
    return float(confidence)


# ---------------------------------------------------------
# Wind simulation (optional, same as im Edge-Code)
# ---------------------------------------------------------
def generate_wind() -> Tuple[float, float]:
    """
    Generates wind speed and direction randomly.
    """
    direction = random.uniform(0, 360)   # degrees
    speed = random.uniform(0, 25)        # m/s
    return speed, direction


def main():
    if len(sys.argv) < 2:
        print("Usage: python test_fire.py <image_path>")
        sys.exit(1)
    
    print("test1")

    image_path = sys.argv[1]

    # Load image
    frame = cv2.imread(image_path)
    if frame is None:
        print(f"Could not read image: {image_path}")
        sys.exit(1)
    print("test2")
    # Resize like in the weather_station code
    frame_small = cv2.resize(frame, (320, 240))

    # Fire detection

    # Grenze 0.014
    conf_smoke = detect_smoke(frame_small)
   
    # Grenze 0.000
    conf_fire = detect_fire(frame_small)
    
    print("test3")
    # Optional: simulate wind (nur zum Testen, wie am Edge)
    wind_speed, wind_direction = generate_wind()

    print(f"Image: {image_path}")
    print(f"Fire confidence: {conf_fire:.4f}")
    print(f"Simulated wind speed: {wind_speed:.2f} m/s")
    print(f"Simulated wind direction: {wind_direction:.1f}°")

    # Wenn du willst, kannst du hier noch die Maske anzeigen
    # um ein Gefühl für die Erkennung zu bekommen:
    # hsv = cv2.cvtColor(frame_small, cv2.COLOR_BGR2HSV)
    # lower = np.array([0, 120, 120], dtype=np.uint8)
    # upper = np.array([30, 255, 255], dtype=np.uint8)
    # mask = cv2.inRange(hsv, lower, upper)
    # cv2.imshow("original", frame_small)
    # cv2.imshow("fire mask", mask)
    # cv2.waitKey(0)


if __name__ == "__main__":
    main()
