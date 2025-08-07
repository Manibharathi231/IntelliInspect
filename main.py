from fastapi import FastAPI, UploadFile, File
from pydantic import BaseModel
import pandas as pd
import joblib
from lightgbm import LGBMClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix

app = FastAPI()

DATASET_PATH = "train_numeric_timestamp.csv"
MODEL_PATH = "model.pkl"
EVALS_RESULT_PATH = "evals_result.pkl"

class TrainRequest(BaseModel):
    trainStart: str
    trainEnd: str
    testStart: str
    testEnd: str

# 1. Train model
@app.post("/train-model")
def train_model(request: TrainRequest):
    df = pd.read_csv(DATASET_PATH)
    df['synthetic_timestamp'] = pd.to_datetime(df['synthetic_timestamp'])

    train_data = df[(df['synthetic_timestamp'] >= request.trainStart) & (df['synthetic_timestamp'] <= request.trainEnd)]
    test_data = df[(df['synthetic_timestamp'] >= request.testStart) & (df['synthetic_timestamp'] <= request.testEnd)]

    X_train = train_data.drop(['Response', 'synthetic_timestamp'], axis=1)
    y_train = train_data['Response']
    X_test = test_data.drop(['Response', 'synthetic_timestamp'], axis=1)
    y_test = test_data['Response']

    model = LGBMClassifier()
    evals_result = {}
    model.fit(
        X_train, y_train,
        eval_set=[(X_train, y_train)],
        eval_metric='logloss',
        callbacks=[lambda env: evals_result.setdefault('training', {}).setdefault('logloss', []).append(env.evaluation_result_list[0][2])]
    )

    joblib.dump(model, MODEL_PATH)
    joblib.dump(evals_result, EVALS_RESULT_PATH)

    preds = model.predict(X_test)

    return {
        "accuracy": round(accuracy_score(y_test, preds), 4),
        "precision": round(precision_score(y_test, preds, zero_division=0), 4),
        "recall": round(recall_score(y_test, preds, zero_division=0), 4),
        "f1_score": round(f1_score(y_test, preds, zero_division=0), 4)
    }

# 2. Evaluate uploaded file and return metrics & training logs
@app.post("/evaluate-existing-model")
async def evaluate_model(file: UploadFile = File(...)):
    df = pd.read_csv(file.file)
    df['synthetic_timestamp'] = pd.to_datetime(df['synthetic_timestamp'])

    model = joblib.load(MODEL_PATH)
    evals_result = joblib.load(EVALS_RESULT_PATH)

    training_loss = evals_result.get('training', {}).get('logloss', [])
    acc_list = [round(1 - l, 4) for l in training_loss]
    loss_list = [round(l, 4) for l in training_loss]

    split_index = int(len(df) * 0.9)
    test_data = df.iloc[split_index:]

    X_test = test_data.drop(['Response', 'synthetic_timestamp'], axis=1)
    y_test = test_data['Response']
    preds = model.predict(X_test)

    acc = round(accuracy_score(y_test, preds), 4)
    prec = round(precision_score(y_test, preds, zero_division=0), 4)
    rec = round(recall_score(y_test, preds, zero_division=0), 4)
    f1 = round(f1_score(y_test, preds, zero_division=0), 4)
    cm = confusion_matrix(y_test, preds)

    cm_values = {
        "tp": int(cm[1][1]) if cm.shape == (2, 2) else 0,
        "tn": int(cm[0][0]) if cm.shape == (2, 2) else int(cm[0][0]),
        "fp": int(cm[0][1]) if cm.shape == (2, 2) else 0,
        "fn": int(cm[1][0]) if cm.shape == (2, 2) else 0
    }

    return {
        "accuracy": acc,
        "precision": prec,
        "recall": rec,
        "f1_score": f1,
        "confusion_matrix": cm.tolist(),
        "training_accuracy": acc_list,
        "training_loss": loss_list,
        "confusion_counts": cm_values
    }

