"""
Inference Predictor for Cognitive Assessment AI Model
Loads the trained Scikit-Learn pipeline and generates the AI Predicted Cognitive Score.
"""

import os
import joblib
import pandas as pd
import numpy as np

MODEL_FILE_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "saved_models",
    "cognitive_model.joblib",
)

_cached_model = None


def get_model():
    global _cached_model
    if _cached_model is None:
        if os.path.exists(MODEL_FILE_PATH):
            try:
                _cached_model = joblib.load(MODEL_FILE_PATH)
            except Exception as e:
                print(f"Error loading model from {MODEL_FILE_PATH}: {e}")
                _cached_model = None
    return _cached_model


def _clean_screen_time(val):
    try:
        return float(val)
    except (ValueError, TypeError):
        val_str = str(val).strip()
        if "<2" in val_str:
            return 1.5
        elif "2-4" in val_str:
            return 3.0
        elif "4-6" in val_str:
            return 5.0
        elif "6-8" in val_str:
            return 7.0
        elif "8+" in val_str:
            return 9.5
        return 5.0


def _clean_exercise_frequency(val):
    val_str = str(val).strip().lower()
    if val_str in ["daily", "high", "3-5"]:
        return "High"
    elif val_str in ["1-2", "medium"]:
        return "Medium"
    else:
        return "Low"


def predict_cognitive_score(user_data):
    """
    Predicts AI Cognitive Score based on participant inputs and test scores.

    Parameters:
    user_data (dict):
        - age (int)
        - gender (str)
        - sleep_duration (float)
        - stress_level (int)
        - screen_time (str or float)
        - exercise_frequency (str)
        - reaction_time (float or int)
        - memory_score (int or float)

    Returns:
    dict:
        - ai_predicted_score (float)
        - performance_tier (str)
        - status (str)
    """
    model = get_model()

    age = float(user_data.get("age", 30))
    gender = str(user_data.get("gender", "Other"))
    sleep_duration = float(user_data.get("sleep_duration", 7.0))
    stress_level = float(user_data.get("stress_level", 5.0))
    screen_time = _clean_screen_time(user_data.get("screen_time", 5.0))
    exercise_freq = _clean_exercise_frequency(user_data.get("exercise_frequency", "Medium"))
    reaction_time = float(user_data.get("reaction_time", 350.0))
    memory_score = float(user_data.get("memory_score", 70.0))

    if model is not None:
        input_df = pd.DataFrame(
            [
                {
                    "Age": age,
                    "Gender": gender,
                    "Sleep_Duration": sleep_duration,
                    "Stress_Level": stress_level,
                    "Daily_Screen_Time": screen_time,
                    "Exercise_Frequency": exercise_freq,
                    "Reaction_Time": reaction_time,
                    "Memory_Test_Score": memory_score,
                }
            ]
        )

        try:
            pred_score = float(model.predict(input_df)[0])
            pred_score = max(0.0, min(100.0, round(pred_score, 2)))
        except Exception as e:
            print(f"Prediction error: {e}")
            pred_score = _heuristic_fallback(user_data)
    else:
        pred_score = _heuristic_fallback(user_data)

    # Determine Performance Tier
    if pred_score >= 85:
        tier = "Superior Cognitive Function"
    elif pred_score >= 70:
        tier = "High Normal Cognitive Function"
    elif pred_score >= 50:
        tier = "Average / Moderate Performance"
    else:
        tier = "Below Average / Follow-up Recommended"

    return {
        "ai_predicted_score": pred_score,
        "performance_tier": tier,
        "status": "success",
    }


def _heuristic_fallback(user_data):
    """Statistical fallback calculation if model is unavailable"""
    reaction = float(user_data.get("reaction_time", 350.0))
    memory = float(user_data.get("memory_score", 70.0))
    sleep = float(user_data.get("sleep_duration", 7.0))
    stress = float(user_data.get("stress_level", 5.0))

    # Normalized reaction score (200ms -> 100, 600ms -> 0)
    norm_reaction = max(0.0, min(100.0, 100.0 - ((reaction - 200.0) / 400.0) * 100.0))

    # Sleep bonus/penalty (7-9h optimal)
    sleep_mod = max(-5.0, min(5.0, (sleep - 5.0) * 2.0))

    # Stress penalty
    stress_mod = (5.0 - stress) * 1.5

    baseline = (0.35 * norm_reaction) + (0.55 * memory) + sleep_mod + stress_mod
    return max(0.0, min(100.0, round(baseline, 2)))
