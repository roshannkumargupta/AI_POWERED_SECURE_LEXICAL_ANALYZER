import os
import sys
import joblib
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import classification_report, confusion_matrix

# Ensure project root is in the Python path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)

def train_model(data_dir=None, model_dir=None):
    if data_dir is None:
        data_dir = os.path.join(PROJECT_ROOT, 'data/processed')
    if model_dir is None:
        model_dir = os.path.join(PROJECT_ROOT, 'data/models')

    print("--- Loading Preprocessed Data ---")
    try:
        X = joblib.load(os.path.join(data_dir, 'X.joblib'))
        y = joblib.load(os.path.join(data_dir, 'y.joblib'))
        le = joblib.load(os.path.join(data_dir, 'label_encoder.joblib'))
        tfidf = joblib.load(os.path.join(data_dir, 'tfidf_vectorizer.joblib'))
        feature_keys = joblib.load(os.path.join(data_dir, 'feature_keys.joblib'))
    except Exception as e:
        print(f"Error loading processed data: {e}")
        return

    # Split into Training and Testing sets (80/20)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    print(f"Training set size: {X_train.shape[0]}")
    print(f"Testing set size: {X_test.shape[0]}")

    print("\n--- Training Random Forest Classifier ---")
    rf = RandomForestClassifier(
        n_estimators=100, 
        max_depth=20, 
        random_state=42, 
        n_jobs=-1,
        class_weight='balanced'
    )
    
    rf.fit(X_train, y_train)

    print("\n--- Evaluating Model Performance ---")
    y_pred = rf.predict(X_test)
    
    print("\nClassification Report:")
    print(classification_report(y_test, y_pred, target_names=le.classes_))

    print("\n--- Feature Importance Analysis ---")
    tfidf_feature_names = tfidf.get_feature_names_out()
    all_feature_names = list(feature_keys) + list(tfidf_feature_names)
    
    importances = rf.feature_importances_
    indices = np.argsort(importances)[::-1]

    print("\nTop 10 Most Important Features:")
    for i in range(10):
        idx = indices[i]
        importance = importances[idx]
        name = all_feature_names[idx]
        print(f"{i+1:2d}. {name:30s} : {importance:.4f}")

    # Save the Model
    if not os.path.exists(model_dir):
        os.makedirs(model_dir)
        
    print(f"\n--- Saving Model to {model_dir} ---")
    model_path = os.path.join(model_dir, 'random_forest_model.joblib')
    joblib.dump(rf, model_path)
    print(f"Model saved successfully at {model_path}")

if __name__ == "__main__":
    train_model()
