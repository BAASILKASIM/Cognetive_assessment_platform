"""
Interactive Manual Testing Tool for Cognitive Assessment Model
Run this script:
    python ml/models/test_manual.py
"""

import os
import sys
import pandas as pd

# Add project root to path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, PROJECT_ROOT)

from ml.utils.predictor import predict_cognitive_score, get_model

def print_banner():
    print("=" * 60)
    print("       COGNITIVE ASSESSMENT MODEL - MANUAL TESTER")
    print("=" * 60)

def test_preset_profiles():
    print("\n--- Testing 3 Real-World Example People ---")
    
    profiles = [
        {
            "name": "Person A (Healthy Adult - Good sleep, fast reaction)",
            "data": {
                "age": 28,
                "gender": "Male",
                "sleep_duration": 8.0,
                "stress_level": 2,
                "screen_time": 3.0,
                "exercise_frequency": "High",
                "reaction_time": 220,     # Fast (220 ms)
                "memory_score": 92        # High memory (92/100)
            }
        },
        {
            "name": "Person B (Stressed & Sleep-Deprived)",
            "data": {
                "age": 45,
                "gender": "Female",
                "sleep_duration": 4.5,
                "stress_level": 9,
                "screen_time": 8.0,
                "exercise_frequency": "Low",
                "reaction_time": 480,     # Slower (480 ms)
                "memory_score": 55        # Moderate (55/100)
            }
        },
        {
            "name": "Person C (Elderly Senior with Moderate Delay)",
            "data": {
                "age": 72,
                "gender": "Female",
                "sleep_duration": 6.0,
                "stress_level": 4,
                "screen_time": 2.0,
                "exercise_frequency": "Medium",
                "reaction_time": 560,     # Slow (560 ms)
                "memory_score": 42        # Low memory (42/100)
            }
        }
    ]

    for p in profiles:
        print(f"\n[Profile: {p['name']}]")
        for k, v in p["data"].items():
            print(f"  - {k.replace('_', ' ').title()}: {v}")
        
        result = predict_cognitive_score(p["data"])
        print(f"  --> AI Predicted Cognitive Score: {result['ai_predicted_score']} / 100")
        print(f"  --> Performance Tier:             {result['performance_tier']}")

def test_dataset_sample():
    csv_path = os.path.join(PROJECT_ROOT, "datasets", "human_cognitive_performance.csv")
    if not os.path.exists(csv_path):
        print("Dataset not found.")
        return

    print("\n--- Comparing Actual vs AI Predicted from 5 Random Dataset Records ---")
    df = pd.read_csv(csv_path).sample(5, random_state=123)
    
    for idx, row in df.iterrows():
        user_dict = {
            "age": row["Age"],
            "gender": row["Gender"],
            "sleep_duration": row["Sleep_Duration"],
            "stress_level": row["Stress_Level"],
            "screen_time": row["Daily_Screen_Time"],
            "exercise_frequency": row["Exercise_Frequency"],
            "reaction_time": row["Reaction_Time"],
            "memory_score": row["Memory_Test_Score"]
        }
        res = predict_cognitive_score(user_dict)
        actual = row["Cognitive_Score"]
        pred = res["ai_predicted_score"]
        diff = abs(actual - pred)
        print(f"User {row['User_ID']} | Actual: {actual:>5.2f} | AI Predicted: {pred:>5.2f} | Difference: {diff:>4.2f} pts")

def main():
    print_banner()
    test_preset_profiles()
    test_dataset_sample()

if __name__ == "__main__":
    main()
