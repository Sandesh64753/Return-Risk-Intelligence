# Product Return Intelligence Platform (Backend Service)

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat&logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688?style=flat&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Neon_Serverless-4169E1?style=flat&logo=postgresql&logoColor=white)](https://neon.tech/)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?style=flat&logo=docker&logoColor=white)](https://www.docker.com/)
[![Tests](https://img.shields.io/badge/Pytest-25_Passed-brightgreen?style=flat&logo=pytest&logoColor=white)](https://pytest.org/)

FastAPI backend service powering the Product Return Intelligence Platform. Provides high-throughput pre-shipment ML risk inference, multi-tenant workspace isolation, historical return analytics with Wilson confidence intervals, and automated operational recommendation workflows.

---

## 1. Architecture & Service Overview

```
                          +---------------------------------------------+
                          |         Client / React Application          |
                          +----------------------+----------------------+
                                                 |
                                   HTTP / JSON   | Credentials (Cookies)
                                   Proxied / Direct -> :8000
                                                 v
                          +---------------------------------------------+
                          |           FastAPI Backend Service           |
                          |  - RESTful JSON API Router (/api/*)         |
                          |  - Signed Session Auth (Argon2id + itsdang) |
                          |  - Strict Multi-Tenant Scoping by company_id|
                          |  - ML Inference Engine (Scikit-Learn Joblib)|
                          +----------------------+----------------------+
                                                 |
                          +----------------------+----------------------+
                          |                                             |
                          v                                             v
           +------------------------------+              +------------------------------+
           |    Relational Database       |              |     Trained ML Pipeline      |
           | (Neon PostgreSQL or SQLite)  |              | (CapstoneFeatureTransformer  |
           |  - companies (Tenant Master) |              |  + Balanced Logistic Reg)    |
           |  - products (SKUs & Catalog) |              |  - 17 pre-shipment features  |
           |  - prediction_records        |              |  - Calibrated thresh: 0.3974 |
           |  - actual_return_records     |              |  - ROC-AUC: 0.9366, F1: 0.79 |
           |  - recommendation_records    |              +------------------------------+
           +------------------------------+
```

---

## 2. Directory Structure

```
backend/
├── Dockerfile                    # Containerization configuration
├── docker-compose.yml            # Standalone container orchestration
├── requirements.txt              # Production pip requirements
├── pyproject.toml                # UV package specification
├── alembic.ini                   # Alembic database migration config
├── alembic/                      # Alembic version migrations
│   └── versions/                 # Version scripts
├── app/
│   ├── main.py                   # FastAPI app instance, CORS & exception handlers
│   ├── config.py                 # Settings, Neon/PostgreSQL pool & threshold config
│   ├── database.py               # SQLAlchemy 2.x session & connection pooling
│   ├── schemas.py                # Pydantic validation schemas
│   ├── models/                   # SQLAlchemy ORM models
│   │   ├── company.py            # Company tenant model
│   │   ├── product.py            # Catalog SKU model
│   │   ├── prediction.py         # PredictionRecord audit model
│   │   ├── actual_return.py      # ActualReturnRecord historical ledger
│   │   └── recommendation.py     # Actionable recommendation record
│   ├── auth/                     # Authentication & security
│   │   ├── security.py           # Argon2id hashing & signed cookies
│   │   └── dependencies.py       # Company session resolvers
│   ├── services/                 # Core business logic
│   │   ├── prediction_service.py # Inference & Capstone feature pipeline
│   │   ├── analytics_service.py  # Wilson score intervals & segment metrics
│   │   ├── recommendation_service.py # Operational rules & impact tracking
│   │   └── import_service.py     # CSV validation & demo seeder
│   └── routers/
│       ├── api.py                # Full JSON REST API
│       └── pages.py              # Server-side rendering fallback
└── artifacts/
    ├── model.joblib              # Serialized Capstone trained model bundle
    └── product_return_prediction.joblib # Backup model artifact
```

---

## 3. Machine Learning Inference Pipeline

Built on the CapStone modeling solution (`artifacts/model.joblib`):
- **Model**: Scikit-Learn Balanced Logistic Regression.
- **Preprocessor (`CapstoneFeatureTransformer`)**: Preprocesses raw inputs using median imputation, feature engineering, and standard scaling.
- **Metrics**: ROC-AUC: `0.9366`, F1: `0.7933`.
- **Tuned Operational Threshold**: `0.3974` (calibrated to prioritize ~90% recall of return events).
- **Grounded Key Factors**:
  - Payment method risk differentiation (Cash on Delivery ~50.5% return rate vs ~15.7% for UPI).
  - Transit distance and delivery delay impact.
  - Defect rate (>8%) and fragility alerts.
  - Pre-dispatch customer support touchpoint volume.

---

## 4. Environment Variables

Create `.env` inside `backend/` or project root:

```ini
ENVIRONMENT=development
DEBUG=false
HOST=0.0.0.0
PORT=8000

SECRET_KEY=dev-secure-session-signing-key-change-for-production-min32bytes

# Database Configuration (Neon PostgreSQL or SQLite)
POSTGRESS_DATABASE=postgresql://neondb_owner:password@ep-morning-dew-b500nhyb-pooler.c-7.us-east-2.aws.neon.tech/Data%20Storage%20of%20product%20details?sslmode=require&channel_binding=require

# Database pool tuning
DB_POOL_SIZE=10
DB_MAX_OVERFLOW=20
DB_POOL_RECYCLE=300

# Path to serialized model bundle
ARTIFACT_PATH=artifacts/model.joblib

# Optional threshold override
# PREDICTION_THRESHOLD=0.397378
```

---

## 5. Deployment & Execution

### Docker Deployment

```bash
# Build and run with Docker Compose
docker compose up --build

# Run container directly
docker build -t return-risk-backend .
docker run -p 8000:8000 --env-file .env return-risk-backend
```

### Local Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Run migrations
alembic upgrade head

# Run server
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

- Swagger API Documentation: `http://localhost:8000/docs`
- Health Endpoint: `http://localhost:8000/health`

---

## 6. Running Tests

```bash
# Run pytest from project root
pytest -v
```
All 25 automated unit and integration tests validate tenant scoping, privilege security, and inference correctness.
