# Product Return Intelligence Platform (Multi-Company)

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat&logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688?style=flat&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-19.0-61DAFB?style=flat&logo=react&logoColor=black)](https://react.dev/)
[![Vite](https://img.shields.io/badge/Vite-6.0-646CFF?style=flat&logo=vite&logoColor=white)](https://vitejs.dev/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Neon_Serverless-4169E1?style=flat&logo=postgresql&logoColor=white)](https://neon.tech/)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?style=flat&logo=docker&logoColor=white)](https://www.docker.com/)
[![Tests](https://img.shields.io/badge/Pytest-25_Passed-brightgreen?style=flat&logo=pytest&logoColor=white)](https://pytest.org/)

An enterprise-grade, multi-tenant machine learning platform engineered to help e-commerce brands predict, analyze, and systematically reduce product returns before fulfillment.

The platform combines a **React 19 single-page application** (`frontend/`) and a **FastAPI data & inference service** (`backend/`), featuring pre-shipment predictive inference, multi-tenant database isolation, historical return rate analytics with Wilson confidence intervals, automated operational action plans with before-and-after impact tracking, containerized deployment, and cloud database integration via Neon PostgreSQL.

---

## 1. Architecture Overview

```
                                      +---------------------------------------------+
                                      |         React 19 + Vite Frontend            |
                                      |             (frontend/ directory)           |
                                      |  - React SPA with custom warm slate CSS     |
                                      |  - Operations Dashboard & Analytics Console |
                                      |  - Interactive Pre-Shipment Prediction Form |
                                      |  - Return Reduction Action Plans & Tracking |
                                      |  - Historical CSV Ingestion & 1-Click Seed  |
                                      +----------------------+----------------------+
                                                             |
                                               HTTP / JSON   | Credentials (Cookies)
                                               Proxied: :5173 -> :8000
                                                             v
                                      +---------------------------------------------+
                                      |           FastAPI Backend Service           |
                                      |              (backend/ directory)           |
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
product-return-prediction/
├── Dockerfile                    # Production multi-stage Docker build for backend
├── docker-compose.yml            # Docker Compose orchestration
├── .dockerignore                 # Docker build exclusions
├── requirements.txt              # Standard pip dependencies
├── pyproject.toml                # UV / PEP-518 package configuration
├── .env.example                  # Environment configuration template
│
├── CapStone_Solutions.ipynb      # End-to-end ML notebook (EDA, training, evaluation)
├── artifacts/
│   ├── model.joblib              # Serialized Capstone trained model bundle
│   └── product_return_prediction.joblib # Backup model artifact
├── dataset/
│   ├── cleaned_returns.csv       # Cleaned e-commerce returns dataset
│   └── returns_dataset.csv       # Raw feature dataset
│
├── frontend/                     # React.js Single Page Application
│   ├── package.json              # React 19, Lucide React, Vite
│   ├── vite.config.js            # Vite config with backend proxy (:8000)
│   ├── src/
│   │   ├── main.jsx              # React DOM mounting
│   │   ├── App.jsx               # Router & session state management
│   │   ├── api.js                # Central API client (cookie credentials)
│   │   ├── index.css             # Enterprise design system (770+ lines of custom CSS)
│   │   ├── components/
│   │   │   ├── Navbar.jsx        # Company workspace badge & navigation
│   │   │   └── Footer.jsx        # Operational notes & quick links
│   │   └── pages/
│   │       ├── Home.jsx          # Public landing with live inspection demo
│   │       ├── Dashboard.jsx     # Company KPIs, top return categories & recent stream
│   │       ├── Predict.jsx       # 4-section order assessment form & presets
│   │       ├── Result.jsx        # Calibrated risk verdict & historical benchmark
│   │       ├── History.jsx       # Paginated prediction audit logs with filtering
│   │       ├── PredictionDetail.jsx # Deep inspection of captured input features
│   │       ├── Analytics.jsx     # Empirical segmentation & Wilson 95% CIs
│   │       ├── Performance.jsx   # Period-over-period return reduction trends
│   │       ├── Recommendations.jsx # Rule-based action plans & outcome impact
│   │       ├── Import.jsx        # Historical CSV upload & 1-click 150-order seeder
│   │       ├── Login.jsx         # Company workspace sign-in
│   │       ├── Register.jsx      # Multi-tenant organization creation
│   │       ├── Methodology.jsx   # Point-in-time constraints & threshold math
│   │       └── About.jsx         # Architecture & developer REST endpoints
│   └── dist/                     # Optimized production bundle
│
├── backend/                      # Python FastAPI Application Service
│   ├── Dockerfile                # Backend containerization file
│   ├── docker-compose.yml        # Backend standalone Compose config
│   ├── requirements.txt          # Backend dependencies
│   ├── alembic/                  # Database migration scripts
│   ├── alembic.ini               # Alembic configuration
│   └── app/
│       ├── main.py               # FastAPI initialization, CORS & error handlers
│       ├── config.py             # Settings, Neon/Postgres pool & threshold config
│       ├── database.py           # SQLAlchemy 2.x session & connection pooling
│       ├── schemas.py            # Pydantic validation schemas
│       ├── models/               # SQLAlchemy ORM models
│       │   ├── company.py        # Company tenant model
│       │   ├── product.py        # Catalog SKU model
│       │   ├── prediction.py     # PredictionRecord audit model
│       │   ├── actual_return.py  # ActualReturnRecord historical ledger
│       │   └── recommendation.py # Actionable recommendation record
│       ├── auth/                 # Authentication & security
│       │   ├── security.py       # Argon2id hashing & signed cookies
│       │   └── dependencies.py   # Company session resolvers
│       ├── services/             # Core business logic
│       │   ├── prediction_service.py # Inference & Capstone feature pipeline
│       │   ├── analytics_service.py  # Wilson score intervals & segment metrics
│       │   ├── recommendation_service.py # Operational rules & impact tracking
│       │   └── import_service.py     # CSV validation & demo seeder
│       └── routers/
│           ├── api.py            # Full JSON REST API
│           └── pages.py          # Legacy server-side rendering fallback
│
└── tests/
    ├── test_multi_company_platform.py # Multi-tenant isolation & API integration tests
    ├── test_prediction.py        # Inference pipeline, threshold & bounds tests
    └── test_pages.py             # Endpoint & SSR route tests
```

---

## 3. Machine Learning Pipeline (Capstone Model)

The machine learning core is built on the empirical findings and modeling developed in [`CapStone_Solutions.ipynb`](file:///d:/Prduct%20Return%20Prediction/CapStone_Solutions.ipynb).

### Pipeline Characteristics
- **Estimator**: Scikit-Learn Balanced Logistic Regression with tuned regularization.
- **Preprocessor (`CapstoneFeatureTransformer`)**:
  - Imputes numerical missing values using training-set medians.
  - Generates engineered interaction and categorical design matrices.
  - Normalizes numerical predictors using training-set feature scaling parameters.
- **Unified Scikit-Learn Pipeline**: The inference engine dynamically constructs a complete `Pipeline([("preprocessor", transformer), ("classifier", raw_model)])` guaranteeing zero train-serve feature skew.
- **Validation Metrics**:
  - **ROC-AUC**: `0.9366`
  - **F1 Score**: `0.7933`
  - **Calibrated Decision Threshold**: `0.3974` (tuned from the default 0.50 to achieve ~90% recall on true returns, protecting merchant margins from high reverse-logistics costs).
- **Grounded Operational Factors**: Derived from empirical distributions:
  - **Payment Method**: Cash on Delivery (COD) orders display an empirical ~50.5% return rate vs. ~15.7% for UPI.
  - **Transit Distance & Delays**: Long-distance fulfillment and shipping delays multiply cancellation and return probability.
  - **Customer Touchpoints**: Orders with multiple pre-dispatch support calls or chat inquiries exhibit significantly higher return propensity.
  - **Defect Rates & Fragility**: Manufacturer defect rates above 8% or unreinforced fragile items trigger specialized quality flags.

---

## 4. Key Platform Features

### A. Multi-Tenant Company Isolation
- Every company creates and administers an isolated workspace.
- Passwords are securely hashed with **Argon2id**.
- Authentication uses **signed HTTP-only session cookies** (`itsdangerous`).
- All queries for predictions, products, actual return records, and recommendations are strictly filtered by the authenticated `company_id`. Cross-tenant queries return 404.

### B. Empirical Historical Returns & Wilson Confidence Intervals
- Small-sample cohorts (e.g. 1 return out of 1 order) distort simple percentages.
- The platform computes **Wilson score 95% confidence intervals** (`ci_low`, `ci_high`) across all segmentations: Category, Sub-Category, Brand, SKU, Fulfillment Type, and Payment Method.
- Strictly decouples **Predicted Probability** (pre-shipment risk estimate) from **Actual Return Rate** (empirical outcome logged post-delivery).

### C. Automated Return Reduction Action Plans
- Scans tenant history for statistically elevated return factors and generates actionable intervention plans:
  - *High-defect items*: Enforce supplier QA certification and reinforced packaging.
  - *High-discount COD apparel*: Automated pre-dispatch SMS verification and sizing guidance.
  - *Fragile home goods*: Upgrade to double-wall corrugated packaging and specialized handling.
- Full lifecycle management: `open`, `in_progress`, `implemented`, `dismissed`.
- When marked as `implemented`, the system automatically tracks **Before vs After Outcome Impact** to measure net return rate reduction in percentage points.

### D. Data Ingestion & 1-Click Seeder
- **CSV Ingestion**: Bulk ingest historical order batches with idempotency (skips duplicate order reference IDs).
- **Downloadable CSV Template**: Standard format ready for client spreadsheet exports.
- **1-Click 150-Order Demo Seeder**: Instantly populates any new workspace with 150 verified sample orders to explore analytics and reports immediately.

---

## 5. Environment Configuration

Copy `.env.example` to `.env` in the project root:

```bash
cp .env.example .env
```

### Key Configuration Variables

| Variable | Description | Default / Example |
|---|---|---|
| `ENVIRONMENT` | Environment name | `development` / `production` |
| `DEBUG` | Enable debug logs | `false` |
| `HOST` | Backend bind host | `0.0.0.0` |
| `PORT` | Backend port | `8000` |
| `SECRET_KEY` | Key for signing session cookies | Change to random 32+ char secret |
| `POSTGRESS_DATABASE` | Neon Serverless PostgreSQL connection string | `postgresql://user:pass@ep-xyz.aws.neon.tech/dbname?sslmode=require` |
| `DATABASE_URL` | Alternative standard database connection URL | (Falls back to SQLite if unset) |
| `DB_POOL_SIZE` | Database connection pool size | `10` |
| `DB_MAX_OVERFLOW` | Maximum database connection overflow | `20` |
| `DB_POOL_RECYCLE` | Connection recycle period in seconds | `300` |
| `ARTIFACT_PATH` | Path to the trained ML model artifact | `artifacts/model.joblib` |
| `PREDICTION_THRESHOLD` | Operational decision threshold override | `0.397378` |

> [!NOTE]
> If neither `POSTGRESS_DATABASE` nor `DATABASE_URL` is set, the application automatically defaults to a local SQLite database (`return_intelligence.db`), allowing zero-configuration local evaluation.

---

## 6. Installation & Deployment

### Method 1: Running with Docker & Docker Compose (Recommended)

To build and run the backend service using Docker:

```bash
# Build and start the container
docker compose up --build

# Run in detached mode
docker compose up -d
```

The containerized backend will be available at `http://localhost:8000`.

---

### Method 2: Local Development Setup

#### Prerequisites
- **Python**: 3.10+ (Python 3.11 recommended)
- **Node.js**: v18+ (Node v20/v22 recommended)
- **Package Managers**: `pip` / `uv` and `npm`

#### 1. Setup Backend

```bash
# Create and activate a virtual environment
python -m venv .venv
# On Windows:
.venv\Scripts\activate
# On Linux/macOS:
# source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
# (or if using uv: uv sync)

# Run database migrations
alembic upgrade head

# Start FastAPI server
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

- API Documentation: `http://localhost:8000/docs`
- Health Check: `http://localhost:8000/health`

#### 2. Setup Frontend

```bash
# In a separate terminal
cd frontend

# Install Node dependencies
npm install

# Start Vite development server
npm run dev
```

- Operations Console: **`http://localhost:5173`**
- The Vite dev server proxies `/api` and `/health` to `http://localhost:8000` with credential forwarding.

#### 3. Production Frontend Build

```bash
cd frontend
npm run build
```
Generates optimized static assets in `frontend/dist/`.

---

## 7. Running Automated Tests

The test suite covers multi-tenant isolation, authorization boundaries, API contracts, and ML inference validation:

```bash
# Run full test suite with pytest
pytest -v

# Or using virtual environment path directly
.venv\Scripts\python.exe -m pytest -v
```

### Test Coverage Highlights:
- **`tests/test_multi_company_platform.py`**:
  - Tenant registration, authentication, and session cookie lifecycle.
  - Multi-tenant data isolation: ensures Company B cannot view or mutate Company A's predictions, catalog, or reports.
  - Direct object access horizontal privilege escalation tests.
  - CSV ingestion idempotency, duplicate detection, and demo seeder.
  - Wilson confidence intervals and period comparisons.
  - Action plan status lifecycles and before/after outcome tracking.
- **`tests/test_prediction.py`**:
  - Model artifact loading and schema validation.
  - Pre-shipment boundary assertions (rating, discount, transit distance).
  - Agreement with trained notebook baseline test cases.
- **`tests/test_pages.py`**:
  - Unauthenticated redirect protection and CSRF/error handling.

---

## 8. REST API Reference

| Method | Endpoint | Description | Auth Required |
|---|---|---|---|
| `GET` | `/health` | System health and model readiness | No |
| `GET` | `/api/categories` | Valid categories, brands, and product taxonomy | No |
| `GET` | `/api/presets` | Standard demonstration order presets | No |
| `POST` | `/api/auth/register` | Register new company workspace | No |
| `POST` | `/api/auth/login` | Sign in to company workspace | No |
| `GET` | `/api/auth/me` | Current authenticated company profile | No |
| `POST` | `/api/auth/logout` | Sign out and clear session cookie | Yes |
| `POST` | `/api/predict` | Pre-shipment return probability prediction | Optional (associates with tenant if authenticated) |
| `GET` | `/api/predictions` | Paginated prediction audit history | Yes |
| `GET` | `/api/predictions/{id}` | Single prediction audit record with inputs | Yes |
| `GET` | `/api/dashboard` | Workspace KPIs, top categories & recent stream | Yes |
| `GET` | `/api/analytics` | Return rates segmented with Wilson 95% CIs | Yes |
| `GET` | `/api/performance` | Period-over-period return rate comparisons | Yes |
| `GET` | `/api/recommendations`| Return reduction action plans & impact tracking| Yes |
| `POST` | `/api/recommendations/{id}/status` | Update action plan status & notes | Yes |
| `POST` | `/api/import` | Upload bulk historical order CSV | Yes |
| `GET` | `/api/import/template` | Download standard CSV import template | No |
| `POST` | `/api/import/demo-seed`| 1-Click seed 150 verified sample orders | Yes |

---

## 9. License

Proprietary enterprise operations software and machine learning system.
