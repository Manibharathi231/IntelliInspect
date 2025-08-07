
# IntelliInspect: Real-Time Predictive Quality Control

![Banner]([https://user-images.githubusercontent.com/your-org/intelliinspect-banner.png](https://www.uplers.com/wp-content/uploads/2022/05/AngularJs-Frameworks-891x505.jpg))

IntelliInspect is a full-stack AI-powered platform that performs **real-time quality control prediction** using sensor data from the Bosch Production Line. It enables manufacturers to proactively detect failures using live streaming inference and ML models.

---

## Features

| Step | Feature |
|------|---------|
| 1 | Upload CSV dataset with automatic timestamp augmentation |
| 2 | Split data by time (Training / Testing / Simulation) |
| 3 | Train ML model and visualize metrics |
| 4 | Simulate real-time predictions at 1-second granularity |

---

## Tech Stack

| Layer | Technology |
|-------|------------|
| Frontend | Angular 19, SCSS, Chart.js, Bootstrap, Toastr |
| Backend | .NET Core 8 API |
| ML Service | Python 3.13 + FastAPI + XGBoost |
| Deployment | Docker + Docker Compose |

---

##  Directory Structure

```
📁 src/
├── app/
│   ├── core/              # Services & models
│   ├── shared/            # Reusable components & pipes
│   ├── features/          # Step-wise screens
│   │   ├── upload/        # Step 1
│   │   ├── date-range/    # Step 2
│   │   ├── model-training/ # Step 3
│   │   └── simulation/    # Step 4
│   ├── app.routes.ts
│   └── app.config.ts
├── assets/
├── environments/
└── styles.scss
```

---

##  Screenshots

###  Upload Dataset

![Upload]([https://user-images.githubusercontent.com/your-org/upload-ui.png](https://media.brightdata.com/2023/01/What-Is-a-Dataset_large.svg))

### Date Ranges

![Date Ranges]([https://user-images.githubusercontent.com/your-org/date-range-ui.png](https://www.figma.com/community/resource/6560b5e9-92dd-469b-baa0-47b187d0f2f7/thumbnail))

### Model Training

![Training]([https://user-images.githubusercontent.com/your-org/model-training-ui.png](https://media.licdn.com/dms/image/v2/D4D12AQG58MlTDU-0Qw/article-cover_image-shrink_720_1280/article-cover_image-shrink_720_1280/0/1697232630995?e=2147483647&v=beta&t=7-eJOsFJP5ojtNkFr9Sq7mKxPVzJAvYWrUKbgYwJeHA))

### Real-Time Simulation

![Simulation]([https://user-images.githubusercontent.com/your-org/simulation-ui.png](https://www.tecsys.com/hubfs/Imported_Blog_Media/MicrosoftTeams-image-4.jpg))

---

## Docker Deployment

Run the entire platform with:

```bash
docker-compose up --build
```

`docker-compose.yml` launches:

- Angular frontend (`frontend-angular`)
- ASP.NET backend (`backend-dotnet`)
- Python ML service (`ml-service-python`)

---

## API Contracts

### Upload CSV (POST `/api/upload`)

Returns:

```json
{
  "filename": "data.csv",
  "totalRecords": 14704,
  "totalColumns": 5,
  "passRate": 72.5,
  "dateRange": {
    "start": "2021-01-01T00:00:00",
    "end": "2021-01-03T00:00:00"
  }
}
```

### Validate Date Ranges (POST `/api/validate-ranges`)

Returns:

```json
{
  "status": "Valid",
  "training": 10000,
  "testing": 3000,
  "simulation": 1704,
  "monthlyBreakdown": [...]
}
```

### Train Model (POST `/train-model`)

Returns model metrics and charts.

### Simulate (POST `/simulate`)

Returns stream of predictions at 1 row/second.

---

## Setup Instructions

1. Clone the repository:
```bash
git clone https://github.com/your-org/intelliinspect.git
cd intelliinspect
```

2. Install Angular dependencies:
```bash
cd frontend
npm install
ng serve
```

3. Run backend & ML via Docker:
```bash
docker-compose up --build
```

---

## Demo Video

[Watch 3-minute walkthrough](https://youtu.be/demo-link)

---

## Contributors
- Manibharathi
- Varshini
- Tharaneeshwaran
- Sandeep Babu
