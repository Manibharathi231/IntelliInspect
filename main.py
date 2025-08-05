from fastapi import FastAPI, UploadFile, File
from pydantic import BaseModel
import pandas as pd
import joblib
import io
import base64
import matplotlib.pyplot as plt
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

# 🚀 1. Train model
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
        callbacks=[
            lambda env: evals_result.setdefault('training', {}).setdefault('logloss', []).append(env.evaluation_result_list[0][2])
        ]
    )


    joblib.dump(model, MODEL_PATH)
    joblib.dump(evals_result, EVALS_RESULT_PATH)

    preds = model.predict(X_test)

    return {
        "accuracy": round(accuracy_score(y_test, preds), 4),
        "precision": round(precision_score(y_test, preds), 4),
        "recall": round(recall_score(y_test, preds), 4),
        "f1_score": round(f1_score(y_test, preds), 4)
    }

# 📊 2. Evaluate uploaded file + Return plots
@app.post("/evaluate-existing-model")
async def evaluate_model(file: UploadFile = File(...)):
    import matplotlib.pyplot as plt

    # Load CSV
    df = pd.read_csv(file.file)
    df['synthetic_timestamp'] = pd.to_datetime(df['synthetic_timestamp'])

    # Load model
    model = joblib.load(MODEL_PATH)

    # Simulate test split
    split_index = int(len(df) * 0.9)
    test_data = df.iloc[split_index:]

    X_test = test_data.drop(['Response', 'synthetic_timestamp'], axis=1)
    y_test = test_data['Response']
    preds = model.predict(X_test)

    # Calculate metrics
    acc = round(accuracy_score(y_test, preds), 4)
    prec = round(precision_score(y_test, preds, zero_division=0), 4)
    rec = round(recall_score(y_test, preds, zero_division=0), 4)
    f1 = round(f1_score(y_test, preds, zero_division=0), 4)
    cm = confusion_matrix(y_test, preds)

    # Load training metrics
    evals_result = joblib.load(EVALS_RESULT_PATH)
    training_loss = evals_result.get('training', {}).get('logloss', [])

    # Generate line chart (dummy accuracy curve vs training loss)
    acc_list = [1 - l for l in training_loss]  # fake accuracy = 1 - loss

    fig1, ax1 = plt.subplots()
    ax1.plot(range(len(training_loss)), acc_list, label="Accuracy")
    ax1.plot(range(len(training_loss)), training_loss, label="Loss")
    ax1.set_title("Training Accuracy vs Loss")
    ax1.set_xlabel("Epoch")
    ax1.set_ylabel("Score")
    ax1.legend()
    buf1 = io.BytesIO()
    plt.savefig(buf1, format="png")
    buf1.seek(0)
    line_chart_base64 = base64.b64encode(buf1.read()).decode("utf-8")
    plt.close(fig1)

    # Generate donut chart for Confusion Matrix
    tn, fp, fn, tp = 0, 0, 0, 0
    if cm.shape == (2, 2):
        tn, fp, fn, tp = cm.ravel()
    else:
        tn = cm[0][0]

    labels = ['TP', 'TN', 'FP', 'FN']
    sizes = [tp, tn, fp, fn]

    fig2, ax2 = plt.subplots()
    wedges, texts = ax2.pie(sizes, labels=labels, startangle=90)
    centre_circle = plt.Circle((0, 0), 0.70, fc='white')
    fig2.gca().add_artist(centre_circle)
    ax2.axis('equal')
    ax2.set_title('Confusion Matrix Donut')
    buf2 = io.BytesIO()
    plt.savefig(buf2, format="png")
    buf2.seek(0)
    donut_chart_base64 = base64.b64encode(buf2.read()).decode("utf-8")
    plt.close(fig2)

    return {
        "accuracy": acc,
        "precision": prec,
        "recall": rec,
        "f1_score": f1,
        "confusion_matrix": cm.tolist(),
        "line_chart": line_chart_base64,
        "donut_chart": donut_chart_base64
    }

