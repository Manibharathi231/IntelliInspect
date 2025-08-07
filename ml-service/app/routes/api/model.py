from fastapi import FastAPI,APIRouter, File, UploadFile, Form, HTTPException, Request
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from imblearn.under_sampling import RandomUnderSampler
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from xgboost import XGBClassifier
from xgboost.callback import EarlyStopping
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
from typing import List
import io
import json
import joblib
import os

router = APIRouter()



MODEL_PATH = os.path.join(os.getcwd(), "data")
os.makedirs(MODEL_PATH, exist_ok=True)
MODEL_FILE = os.path.join(MODEL_PATH, "trained_model.pkl")

@router.post("/train-model")
async def train_model(
    file: UploadFile = File(...),
    ranges: str    = Form(...)
):
    # 1) Load full CSV
    contents = await file.read()
    try:
        df = pd.read_csv(io.BytesIO(contents), parse_dates=['synthetic_timestamp'])
    except Exception as e:
        raise HTTPException(400, f"CSV parse error: {e}")

    # 2) Parse date ranges
    rd = json.loads(ranges)
    ts, te = pd.to_datetime(rd['TrainStart']), pd.to_datetime(rd['TrainEnd'])
    vs, ve = pd.to_datetime(rd['TestStart']),  pd.to_datetime(rd['TestEnd'])

    # 3) Slice train & test windows
    df_train = df[(df.synthetic_timestamp >= ts) & (df.synthetic_timestamp <= te)]
    df_test  = df[(df.synthetic_timestamp >= vs) & (df.synthetic_timestamp <= ve)]

    # 4) Separate features & target
    X_train = df_train.drop(['response','synthetic_timestamp'], axis=1)
    y_train = df_train['response']
    X_test  = df_test.drop( ['response','synthetic_timestamp'], axis=1)
    y_test  = df_test['response']

    # 5) Balance classes (undersample majority to 1:1)
    rus = RandomUnderSampler(sampling_strategy=1.0, random_state=42)
    X_bal, y_bal = rus.fit_resample(X_train, y_train)

    # 6) Split off 20% for early stopping
    X_tr, X_val, y_tr, y_val = train_test_split(
        X_bal, y_bal,
        test_size=0.2,
        random_state=42,
        stratify=y_bal
    )

    # 7) Train with regularization & early stopping
    model = XGBClassifier(
    use_label_encoder=False,
    eval_metric="logloss",
    tree_method="hist",
    max_depth=4,
    min_child_weight=5,
    subsample=0.8,
    colsample_bytree=0.8,
    reg_alpha=1.0,
    reg_lambda=1.0
)
    model.set_params(eval_metric=["logloss", "error"])
    
    model.fit(
        X_tr, y_tr,
        eval_set=[(X_tr, y_tr)], 
        verbose=False
    )
    
    evals_result = model.evals_result()
    logloss = evals_result["validation_0"]["logloss"]
    error = evals_result["validation_0"]["error"]
    epochs = range(len(logloss))

    
    fig, ax1 = plt.subplots(figsize=(10, 5))


    ax1.plot(epochs, logloss, label="Logloss", color='tab:blue')
    ax1.set_xlabel("Epoch")
    ax1.set_ylabel("Logloss", color='tab:blue')
    ax1.tick_params(axis='y', labelcolor='tab:blue')

    
    ax2 = ax1.twinx()
    accuracy = [1 - e for e in error]
    ax2.plot(epochs, accuracy, label="Accuracy", color='tab:green')
    ax2.set_ylabel("Accuracy", color='tab:green')
    ax2.tick_params(axis='y', labelcolor='tab:green')

    
    plt.title("Training Logloss and Accuracy")
    fig.tight_layout()

    
    PLOT_PATH = os.path.join(MODEL_PATH, "training_metrics.png")
    plt.savefig(PLOT_PATH)
    plt.close()

    
    joblib.dump(model, MODEL_FILE)

    
    preds = model.predict(X_test)
    return {
        'status':    'Model trained successfully',
        'accuracy':  accuracy_score(y_test, preds),
        'precision': precision_score(y_test, preds),
        'recall':    recall_score(y_test, preds),
        'f1_score':  f1_score(y_test, preds),

    }
model = joblib.load("data/trained_model.pkl")

class PredictionResult(BaseModel):
    Id: str
    Prediction: str
    Confidence: float

@router.post("/predict", response_model=PredictionResult)
async def predict(request: Request):
    # Receive full dynamic row
    data = await request.json()

    # Extract metadata
    sample_id = data.get("id", "unknown")
    data.pop("id", None)
    data.pop("synthetic_timestamp", None)

    # Convert all remaining values to float
    try:
        features = []
        for k, v in data.items():
            try:
                features.append(float(v))
            except (ValueError, TypeError):
                features.append(0.0)  # or np.nan if your model can handle it
        features = np.array(features).reshape(1, -1)
    except Exception:
        print("always exception")
        return PredictionResult(
            sample_id=sample_id,
            prediction="Fail",
            confidence=0.0
        )

    # Make prediction
    pred_proba = model.predict_proba(features)[0]
    pred_class = model.predict(features)[0]

    label = "Pass" if pred_class == 1 else "Fail"
    confidence = round(100 * max(pred_proba), 2)
    print(sample_id, label, confidence)
    print(PredictionResult)

    return PredictionResult(
        Id=sample_id,
        Prediction=label,
        Confidence=confidence
    )

