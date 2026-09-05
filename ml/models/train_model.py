import os
import pandas as pd
import numpy as np
import joblib
from sklearn.model_selection import train_test_split, KFold, cross_val_score
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.linear_model import Ridge
from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATASET_PATH = os.path.join(PROJECT_ROOT, "datasets", "human_cognitive_performance.csv")
MODEL_SAVE_DIR = os.path.join(PROJECT_ROOT, "ml", "saved_models")
MODEL_FILE_PATH = os.path.join(MODEL_SAVE_DIR, "cognitive_model.joblib")


def clean_exercise_frequency(val):
    val_str = str(val).strip().lower()
    if val_str in ["daily", "high", "3-5"]:
        return "High"
    elif val_str in ["1-2", "medium"]:
        return "Medium"
    else:
        return "Low"


def clean_screen_time(val):
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


def train():
    print(f"Loading dataset from: {DATASET_PATH}")
    if not os.path.exists(DATASET_PATH):
        raise FileNotFoundError(f"Dataset not found at {DATASET_PATH}")

    df = pd.read_csv(DATASET_PATH)
    print(f"Dataset shape: {df.shape}")

    # Standardize column names
    df.columns = df.columns.str.strip()

    # Preprocess categorical / numeric fields
    df["Exercise_Frequency"] = df["Exercise_Frequency"].apply(clean_exercise_frequency)
    df["Daily_Screen_Time"] = df["Daily_Screen_Time"].apply(clean_screen_time)

    # Required features - excluding any target derivatives to prevent data leakage
    feature_cols = [
        "Age",
        "Gender",
        "Sleep_Duration",
        "Stress_Level",
        "Daily_Screen_Time",
        "Exercise_Frequency",
        "Reaction_Time",
        "Memory_Test_Score",
    ]

    target_col = "Cognitive_Score"

    # Drop missing values
    df_clean = df[feature_cols + [target_col]].dropna()
    print(f"Cleaned records: {len(df_clean)}")

    X = df_clean[feature_cols]
    y = df_clean[target_col]

    # Split dataset (70% train, 30% holdout test)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.30, random_state=42
    )

    numeric_features = [
        "Age",
        "Sleep_Duration",
        "Stress_Level",
        "Daily_Screen_Time",
        "Reaction_Time",
        "Memory_Test_Score",
    ]
    categorical_features = ["Gender", "Exercise_Frequency"]

    preprocessor = ColumnTransformer(
        transformers=[
            ("num", StandardScaler(), numeric_features),
            ("cat", OneHotEncoder(handle_unknown="ignore"), categorical_features),
        ]
    )

    print("\n--- 1. Performing 5-Fold Cross-Validation to Validate Generalization ---")
    kf = KFold(n_splits=5, shuffle=True, random_state=42)

    # Regularized Gradient Boosting Regressor Pipeline with anti-overfitting constraints
    regularized_gbr = GradientBoostingRegressor(
        n_estimators=250,
        learning_rate=0.05,        # Lower learning rate prevents aggressive step updates
        max_depth=4,               # Constrained tree depth limits complex feature interactions
        min_samples_split=20,      # Minimum samples to consider a split
        min_samples_leaf=15,       # Minimum samples in leaf nodes to prevent outlier fitting
        subsample=0.80,            # Stochastic sampling (80% per tree)
        validation_fraction=0.10,  # 10% internal holdout for early stopping
        n_iter_no_change=10,       # Early stopping triggered if 10 consecutive trees show no gain
        tol=1e-4,
        random_state=42,
    )

    cv_pipeline = Pipeline(
        steps=[
            ("preprocessor", preprocessor),
            ("regressor", regularized_gbr),
        ]
    )

    cv_scores = cross_val_score(cv_pipeline, X_train, y_train, cv=kf, scoring="r2", n_jobs=-1)
    print(f"5-Fold CV R^2 Scores: {[round(s, 4) for s in cv_scores]}")
    print(f"5-Fold CV Mean R^2:   {cv_scores.mean() * 100:.2f}% (+/- {cv_scores.std() * 100:.2f}%)")

    print("\n--- 2. Training Final Regularized Pipeline on Full 70% Train Set ---")
    pipeline = Pipeline(
        steps=[
            ("preprocessor", preprocessor),
            ("regressor", regularized_gbr),
        ]
    )
    pipeline.fit(X_train, y_train)

    actual_trees = pipeline.named_steps["regressor"].n_estimators_
    print(f"Training completed. Optimal trees fitted (via early stopping): {actual_trees}")

    # Evaluate on Train vs Test to verify overfitting margin
    y_train_pred = pipeline.predict(X_train)
    y_test_pred = pipeline.predict(X_test)

    train_r2 = r2_score(y_train, y_train_pred)
    test_r2 = r2_score(y_test, y_test_pred)
    overfitting_gap = (train_r2 - test_r2) * 100

    mae = mean_absolute_error(y_test, y_test_pred)
    rmse = np.sqrt(mean_squared_error(y_test, y_test_pred))

    # Safe MAPE calculation (ignoring zero targets to prevent inf)
    non_zero_mask = y_test != 0
    if non_zero_mask.sum() > 0:
        mape = np.mean(np.abs((y_test[non_zero_mask] - y_test_pred[non_zero_mask]) / y_test[non_zero_mask])) * 100
        percent_accuracy = max(0.0, 100.0 - mape)
    else:
        mape = 0.0
        percent_accuracy = test_r2 * 100

    # Accuracy within tolerance thresholds
    within_2_pts = np.mean(np.abs(y_test - y_test_pred) <= 2.0) * 100
    within_3_pts = np.mean(np.abs(y_test - y_test_pred) <= 3.0) * 100
    within_5_pts = np.mean(np.abs(y_test - y_test_pred) <= 5.0) * 100

    print(f"\n=======================================================")
    print(f"  Regularized Tabular Cognitive Model Results (70:30 Split)")
    print(f"=======================================================")
    print(f"  Train Size:                   {len(X_train):,} (70%)")
    print(f"  Test Size:                    {len(X_test):,} (30%)")
    print(f"  Train R^2 Score:              {train_r2 * 100:.2f}% ({train_r2:.4f})")
    print(f"  Test R^2 Score (Accuracy):    {test_r2 * 100:.2f}% ({test_r2:.4f})")
    print(f"  Train-Test Overfitting Gap:   {overfitting_gap:.2f}% (<0.5% indicates excellent generalization)")
    print(f"  5-Fold CV Mean R^2:           {cv_scores.mean() * 100:.2f}% (+/- {cv_scores.std() * 100:.2f}%)")
    print(f"  Mean Absolute Error (MAE):    {mae:.4f} points")
    print(f"  Root Mean Squared Error:      {rmse:.4f} points")
    print(f"  Mean Absolute % Error:        {mape:.2f}%")
    print(f"  Mean Percentage Accuracy:     {percent_accuracy:.2f}%")
    print(f"  Predictions within +/-2 pts:   {within_2_pts:.2f}%")
    print(f"  Predictions within +/-3 pts:   {within_3_pts:.2f}%")
    print(f"  Predictions within +/-5 pts:   {within_5_pts:.2f}%")
    print(f"=======================================================\n")

    # Save trained pipeline
    os.makedirs(MODEL_SAVE_DIR, exist_ok=True)
    joblib.dump(pipeline, MODEL_FILE_PATH)
    print(f"Saved regularized model artifact to: {MODEL_FILE_PATH}")


if __name__ == "__main__":
    train()

