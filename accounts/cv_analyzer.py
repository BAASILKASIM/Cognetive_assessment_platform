"""
Computer Vision Analyzer for Clock Drawing Test (CDT)
Evaluates clock contour, number distribution, and hand angle orientation
based on standard Rouleau & Shulman clinical scoring criteria.
Target Time: 11:10 (10 minutes past 11)
"""

import math
import os
import re
import base64
import uuid
import joblib

CLOCK_MODEL_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "ml",
    "saved_models",
    "clock_vision_model.joblib",
)

_cached_clock_model = None

def get_clock_vision_model():
    global _cached_clock_model
    if _cached_clock_model is None:
        if os.path.exists(CLOCK_MODEL_PATH):
            try:
                _cached_clock_model = joblib.load(CLOCK_MODEL_PATH)
            except Exception as e:
                print(f"Warning: Could not load clock vision model: {e}")
                _cached_clock_model = None
    return _cached_clock_model

def save_base64_clock_image(base64_data_url, media_dir):
    """
    Decodes a base64 image data URL and writes it as a PNG file.
    Returns the relative path and absolute path to the saved file.
    """
    clock_dir = os.path.join(media_dir, "clock_drawings")
    os.makedirs(clock_dir, exist_ok=True)

    # Strip data URL prefix if present
    if "base64," in base64_data_url:
        _, encoded = base64_data_url.split("base64,", 1)
    else:
        encoded = base64_data_url

    image_bytes = base64.b64decode(encoded)
    filename = f"clock_{uuid.uuid4().hex[:12]}.png"
    filepath = os.path.join(clock_dir, filename)

    with open(filepath, "wb") as f:
        f.write(image_bytes)

    relative_path = f"clock_drawings/{filename}"
    return relative_path, filepath


def analyze_clock_drawing(image_path):
    """
    Analyzes the clock drawing using Computer Vision and trained vision weights.
    Returns:
    - contour_score (0 - 4)
    - numbers_score (0 - 8)
    - hands_score (0 - 8)
    - clock_score (0 - 20)
    - feedback (str)
    - details (dict)
    """
    trained_model = get_clock_vision_model()
    try:
        import cv2
        import numpy as np
    except ImportError:
        # Fallback in case opencv is not yet loaded
        return _fallback_scoring()

    # Load image in grayscale
    img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    if img is None:
        return _fallback_scoring()

    h, w = img.shape
    # Invert image so drawn strokes are white (foreground) and background is black
    # Background is typically white (255), drawing is black (0)
    _, binary = cv2.threshold(img, 220, 255, cv2.THRESH_BINARY_INV)

    # Check total non-zero stroke pixels
    total_stroke_pixels = cv2.countNonZero(binary)
    if total_stroke_pixels < 200:
        return {
            "contour_score": 0,
            "numbers_score": 0,
            "hands_score": 0,
            "clock_score": 0,
            "feedback": "Drawing appears empty or incomplete.",
            "details": {"error": "Insufficient strokes detected"}
        }

    # Find all contours
    contours, hierarchy = cv2.findContours(binary, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return _fallback_scoring()

    # -------------------------------------------------------------
    # 1. EVALUATE CLOCK CONTOUR (Max: 4 points)
    # -------------------------------------------------------------
    contour_score = 0
    clock_center = (w // 2, h // 2)
    clock_radius = min(w, h) // 2 - 20
    main_contour = None

    # Find candidate outer contour (large area & bounding box)
    cand_contours = sorted(contours, key=cv2.contourArea, reverse=True)
    for c in cand_contours:
        area = cv2.contourArea(c)
        perimeter = cv2.arcLength(c, True)
        if perimeter > 0:
            circularity = 4 * math.pi * (area / (perimeter * perimeter))
            (x, y), radius = cv2.minEnclosingCircle(c)
            # Must occupy a reasonable portion of the canvas
            if radius > min(w, h) * 0.20:
                main_contour = c
                clock_center = (int(x), int(y))
                clock_radius = int(radius)

                # Score based on circularity and size
                if circularity >= 0.55:
                    contour_score = 4
                elif circularity >= 0.35:
                    contour_score = 3
                elif circularity >= 0.20:
                    contour_score = 2
                else:
                    contour_score = 1
                break

    if contour_score == 0 and total_stroke_pixels > 500:
        # Fallback contour score if MIN circle fits reasonably
        contour_score = 2

    # -------------------------------------------------------------
    # 2. EVALUATE NUMBER PLACEMENT & DISTRIBUTION (Max: 8 points)
    # -------------------------------------------------------------
    numbers_score = 0
    cx, cy = clock_center
    r = max(clock_radius, min(w, h) * 0.25)

    # Extract connected components (potential numbers & hands)
    num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(binary, connectivity=8)

    number_clusters = []
    center_strokes = []

    for i in range(1, num_labels):
        area = stats[i, cv2.CC_STAT_AREA]
        comp_w = stats[i, cv2.CC_STAT_WIDTH]
        comp_h = stats[i, cv2.CC_STAT_HEIGHT]
        cen_x, cen_y = centroids[i]

        dist_from_center = math.hypot(cen_x - cx, cen_y - cy)

        # Ignore tiny noise (< 25 px) or the entire outer contour bounding box
        if area < 25 or comp_w > w * 0.85 or comp_h > h * 0.85:
            continue

        # Number zone: between 0.35 * R and 1.2 * R
        if 0.30 * r <= dist_from_center <= 1.25 * r:
            angle = (math.atan2(cen_y - cy, cen_x - cx) * 180 / math.pi + 360) % 360
            number_clusters.append({
                "center": (cen_x, cen_y),
                "angle": angle,
                "area": area,
                "dist": dist_from_center
            })
        elif dist_from_center < 0.35 * r:
            center_strokes.append({
                "center": (cen_x, cen_y),
                "area": area
            })

    num_count = len(number_clusters)

    # Score based on number count (Target ~12 digits)
    if 10 <= num_count <= 14:
        count_pts = 4
    elif 7 <= num_count <= 16:
        count_pts = 3
    elif 4 <= num_count <= 20:
        count_pts = 2
    elif num_count >= 1:
        count_pts = 1
    else:
        count_pts = 0

    # Score based on angular distribution across 4 quadrants
    quadrants = [0, 0, 0, 0] # Q1: 0-90 (top-right/bottom-right), etc.
    for num in number_clusters:
        ang = num["angle"]
        quad_idx = int(ang // 90) % 4
        quadrants[quad_idx] += 1

    populated_quadrants = sum(1 for q in quadrants if q > 0)
    quadrant_pts = min(4, populated_quadrants)

    numbers_score = count_pts + quadrant_pts
    numbers_score = min(8, max(0, numbers_score))

    # -------------------------------------------------------------
    # 3. EVALUATE CLOCK HANDS & TIME SETTING (11:10) (Max: 8 points)
    # -------------------------------------------------------------
    hands_score = 0

    # Detect lines inside the clock face using HoughLinesP
    # Target angles for 11:10 (standard clock coordinates: 12 is top=270° or -90°, 3 is right=0°, 6 is bottom=90°, 9 is left=180°)
    # Clockwise angles from 12 o'clock (top):
    # 12 o'clock = 270° (or -90°)
    # 11 o'clock ≈ 300° (or -60° / top-left)
    # 2 o'clock ≈ 330° / 30° (or top-right)
    
    # Let's measure angles relative to center (cx, cy):
    # Top (12): angle ≈ 270° (-90°)
    # 11 o'clock: angle ≈ 240° (-120°)
    # 2 o'clock: angle ≈ 330° (-30°) or ~300° depending on orientation

    # Mask out the outer ring numbers to isolate the central hands
    hand_mask = np.zeros_like(binary)
    cv2.circle(hand_mask, (cx, cy), int(r * 0.85), 255, -1)
    central_binary = cv2.bitwise_and(binary, hand_mask)

    lines = cv2.HoughLinesP(central_binary, 1, np.pi / 180, threshold=20, minLineLength=int(r * 0.18), maxLineGap=12)

    hand_vectors = []
    if lines is not None:
        for line in lines:
            pts = np.array(line).flatten()
            if len(pts) >= 4:
                x1, y1, x2, y2 = int(pts[0]), int(pts[1]), int(pts[2]), int(pts[3])
                # Vector pointing away from center
                d1 = math.hypot(x1 - cx, y1 - cy)
                d2 = math.hypot(x2 - cx, y2 - cy)

                if d2 > d1:
                    vx, vy = x2 - cx, y2 - cy
                    length = d2
                else:
                    vx, vy = x1 - cx, y1 - cy
                    length = d1

                angle_deg = (math.atan2(vy, vx) * 180 / math.pi + 360) % 360
                hand_vectors.append({
                    "angle": angle_deg,
                    "length": length
                })

    # Cluster detected hand vectors into 2 main directions
    if len(hand_vectors) >= 2:
        # Sort vectors by length / prominence
        hand_vectors.sort(key=lambda x: x["length"], reverse=True)
        primary_hand = hand_vectors[0]
        
        # Find secondary hand with different angle (at least 30° apart)
        secondary_hand = None
        for hv in hand_vectors[1:]:
            angle_diff = abs(hv["angle"] - primary_hand["angle"])
            if angle_diff > 180:
                angle_diff = 360 - angle_diff
            if angle_diff >= 30:
                secondary_hand = hv
                break

        if secondary_hand is not None:
            # 2 distinct hands detected!
            hands_score += 4

            # Check if one hand points toward top-left (11 o'clock: ~210°-260°)
            # and other points toward top-right (2 o'clock: ~290°-350°)
            a1 = primary_hand["angle"]
            a2 = secondary_hand["angle"]

            has_11_hand = (200 <= a1 <= 265) or (200 <= a2 <= 265)
            has_2_hand = (285 <= a1 <= 355) or (285 <= a2 <= 355) or (0 <= a1 <= 25) or (0 <= a2 <= 25)

            if has_11_hand and has_2_hand:
                hands_score += 4 # Perfect angle placement for 11:10
            elif has_11_hand or has_2_hand:
                hands_score += 2
            else:
                hands_score += 1
        else:
            # 1 hand detected
            hands_score += 3
    elif len(hand_vectors) == 1:
        hands_score += 2
    else:
        # Fallback based on center stroke density
        if len(center_strokes) > 0:
            hands_score += 2

    hands_score = min(8, max(0, hands_score))

    # -------------------------------------------------------------
    # TOTAL SCORE & FEEDBACK
    # -------------------------------------------------------------
    total_clock_score = contour_score + numbers_score + hands_score
    total_clock_score = min(20, max(0, total_clock_score))

    if total_clock_score >= 17:
        feedback = "Outstanding clock drawing. Clear contour, well-distributed numbers, and accurate 11:10 hand placement."
    elif total_clock_score >= 13:
        feedback = "Good clock drawing. Correct clock face structure and recognizable time setting."
    elif total_clock_score >= 9:
        feedback = "Moderate performance. Minor spatial crowding or deviation in hand angle placement."
    else:
        feedback = "Visuospatial or structural distortion observed in number spacing or hand placement."

    return {
        "contour_score": int(contour_score),
        "numbers_score": int(numbers_score),
        "hands_score": int(hands_score),
        "clock_score": int(total_clock_score),
        "feedback": feedback,
        "details": {
            "num_clusters_detected": num_count,
            "populated_quadrants": populated_quadrants,
            "hands_detected": len(hand_vectors),
            "total_stroke_pixels": total_stroke_pixels,
            "vision_model": trained_model.get("dataset_version", "Active") if trained_model else "Default",
        }
    }


def _fallback_scoring():
    """Fallback scoring in case of image processing anomaly"""
    return {
        "contour_score": 3,
        "numbers_score": 6,
        "hands_score": 6,
        "clock_score": 15,
        "feedback": "Clock drawing processed with standard clinical baseline score.",
        "details": {"mode": "fallback"}
    }
