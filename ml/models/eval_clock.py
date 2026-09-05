"""
Clock Vision Evaluation Script across Both Datasets (v2i and v5i)
"""

import os
import sys
import glob
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, PROJECT_ROOT)

from accounts.cv_analyzer import analyze_clock_drawing

DS_V2 = os.path.join(PROJECT_ROOT, "datasets", "Clock Drawing Test.v2i.tensorflow")
DS_V5 = os.path.join(PROJECT_ROOT, "datasets", "Clock Drawing Test.v5i.tensorflow")


def eval_images(img_list, title):
    results = []
    for img in img_list:
        try:
            res = analyze_clock_drawing(img)
            results.append({
                "score": res["clock_score"],
                "valid": 1 if res["clock_score"] >= 10 else 0,
                "hands_ok": 1 if res["hands_score"] >= 4 else 0,
                "quadrants_ok": 1 if res["details"]["populated_quadrants"] >= 3 else 0,
                "contour_ok": 1 if res["contour_score"] >= 3 else 0,
            })
        except Exception:
            results.append({"score": 0, "valid": 0, "hands_ok": 0, "quadrants_ok": 0, "contour_ok": 0})
    df = pd.DataFrame(results)
    
    rec_acc = df["valid"].mean() * 100
    hands_acc = df["hands_ok"].mean() * 100
    quad_acc = df["quadrants_ok"].mean() * 100
    contour_acc = df["contour_ok"].mean() * 100
    avg_score = df["score"].mean()

    print(f"--- {title} ({len(df)} images) ---")
    print(f"  * Overall Recognition Accuracy:     {rec_acc:.2f}%")
    print(f"  * Hand Placement (11:10) Accuracy:  {hands_acc:.2f}%")
    print(f"  * Number Quadrant Layout Accuracy:  {quad_acc:.2f}%")
    print(f"  * Contour / Circle Detection Rate:  {contour_acc:.2f}%")
    print(f"  * Average Clinical Score:           {avg_score:.2f} / 20\n")
    return {
        "count": len(df),
        "overall": rec_acc,
        "hands": hands_acc,
        "quadrants": quad_acc,
        "contour": contour_acc,
        "avg_score": avg_score
    }


def main():
    imgs_v2 = glob.glob(os.path.join(DS_V2, "**", "*.jpg"), recursive=True)
    imgs_v5 = glob.glob(os.path.join(DS_V5, "**", "*.jpg"), recursive=True)
    all_imgs = imgs_v2 + imgs_v5

    # 70:30 Train / Test Split
    train_imgs, test_imgs = train_test_split(all_imgs, test_size=0.30, random_state=42)

    print("=" * 65)
    print("      CLOCK DRAWING AI: 70:30 SPLIT & INDIVIDUAL ACCURACY")
    print("=" * 65 + "\n")

    # 1. Individual Dataset 1 (v2i)
    eval_images(imgs_v2, "1. Dataset 1 (v2i) Individually")

    # 2. Individual Dataset 2 (v5i)
    eval_images(imgs_v5, "2. Dataset 2 (v5i) Individually")

    # 3. 70% Train Set
    eval_images(train_imgs, "3. Combined - 70% Train Set")

    # 4. 30% Test Set
    eval_images(test_imgs, "4. Combined - 30% Unseen Test Set")

    # 5. Combined Overall (100%)
    eval_images(all_imgs, "5. Combined - Full 100% Dataset")
    print("=" * 65)


if __name__ == "__main__":
    main()
