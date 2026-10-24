# Product Return Intelligence Platform (Multi-Company)

An enterprise-grade, multi-company machine learning platform engineered to help e-commerce brands predict, analyze, and systematically reduce product returns.

The platform provides a **React.js single-page application** (`frontend/`) and a **FastAPI machine learning & data service** (`backend/`), combining pre-shipment predictive inference, multi-tenant database isolation, historical return rate analytics with Wilson confidence intervals, and automated operational recommendations with before-and-after impact tracking.

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
                       |    Relational Database       |              |   Trained ML Artifact        |
                       |  (SQLite / PostgreSQL)       |              | (ColumnTransformer + LogReg) |
                       |  - companies (Tenant Master) |              |  - 17 pre-shipment features  |
                       |  - products (SKUs & Catalog) |              |  - Tuned threshold: 0.3974   |
                       |  - prediction_records        |              |  - Target Recall: ~90.0%     |
                       |  - actual_return_records     |              +------------------------------+
                       |  - recommendation_records    |
                       +------------------------------+
```

---

## 2. Directory Structure

```
product-return-prediction/
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
│   ├── app/
│   │   ├── main.py               # FastAPI initialization, CORS & error handlers
│   │   ├── config.py             # App settings, thresholds & paths
│   │   ├── database.py           # SQLAlchemy 2.x session & engine
│   │   ├── schemas.py            # Pydantic validation schemas
│   │   ├── models/               # SQLAlchemy ORM models
│   │   │   ├── company.py        # Company tenant model
│   │   │   ├── product.py        # Catalog SKU model
│   │   │   ├── prediction.py     # PredictionRecord audit model
│   │   │   ├── actual_return.py  # ActualReturnRecord historical ledger
│   │   │   └── recommendation.py # Actionable recommendation record
│   │   ├── auth/                 # Authentication & security
│   │   │   ├── security.py       # Argon2id hashing & signed cookies
│   │   │   └── dependencies.py   # Company session resolvers
│   │   ├── services/             # Core business logic
│   │   │   ├── prediction_service.py # Inference & feature alignment
│   │   │   ├── analytics_service.py  # Wilson score intervals & segment metrics
│   │   │   ├── recommendation_service.py # Operational rules & impact tracking
│   │   │   └── import_service.py     # CSV validation & demo seeder
│   │   └── routers/
│   │       ├── api.py            # Full JSON REST API
│   │       └── pages.py          # Legacy server-side rendering fallback
│   ├── alembic/                  # Database migration scripts
│   ├── alembic.ini               # Alembic configuration
│   └── pyproject.toml            # Backend dependencies
│
├── artifacts/
│   └── product_return_prediction.joblib  # Trained model & ColumnTransformer pipeline
├── dataset/
│   ├── cleaned_returns.csv       # Cleaned e-commerce returns dataset
│   └── returns_dataset.csv       # Raw feature dataset
└── tests/
    ├── test_multi_company_platform.py # Multi-tenant isolation & API integration tests
    ├── test_prediction.py        # Inference pipeline, threshold & bounds tests
    └── test_pages.py             # Endpoint & SSR route tests
```

---

## 3. Getting Started

### Prerequisites
- **Python:** 3.10+ (Python 3.11 recommended)
- **Node.js:** v18+ (Node v22 recommended)
- **Package Managers:** `uv` (or `pip`) and `npm`

---

### Step 1: Run the Backend

```bash
# 1. From the project root, install Python dependencies:
uv sync

# 2. Apply database migrations:
uv run alembic upgrade head

# 3. Start the FastAPI backend server:
uv run uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

The backend is now running at `http://127.0.0.1:8000`.
- Interactive API Docs (Swagger UI): `http://127.0.0.1:8000/docs`
- Health check: `http://127.0.0.1:8000/health`

---

### Step 2: Run the React Frontend

Open a new terminal window:

```bash
# 1. Navigate to the frontend directory:
cd frontend

# 2. Install NPM dependencies:
npm install

# 3. Start the Vite development server:
npm run dev
```

The React operations console is now live at:
**`http://localhost:5173`**

The Vite development server automatically proxies all `/api` and `/health` requests to `http://127.0.0.1:8000` with session cookie forwarding (`credentials: include`).

---

### Step 3: Building Frontend for Production

```bash
cd frontend
npm run build
```

This compiles optimized client assets into `frontend/dist/`.

---

## 4. Key Platform Features

### A. Multi-Tenant Company Isolation
- Every company registers an independent workspace.
- Passwords are securely hashed with **Argon2id**.
- Authentication uses **signed HTTP-only session cookies** (`itsdangerous`).
- All queries for predictions, products, actual return ledger records, and recommendations are strictly filtered by the authenticated `company_id`. Cross-tenant access is blocked with 404 responses.

### B. Machine Learning Pipeline & Calibrated Threshold
- **Serialized Model:** Scikit-Learn balanced Logistic Regression with standard feature scaling and one-hot encoding.
- **Pre-Shipment Point-in-Time Constraint:** 17 validated pre-shipment features. All post-purchase signals (delayed transit, customer support tickets, refund claims) are strictly excluded from the inference pipeline.
- **Tuned Threshold (`0.3974`):** Lowered from 0.50 to prioritize ~90% recall of return events on validation data, protecting merchant margins from costly reverse logistics.

### C. Empirical Historical Returns & Wilson Confidence Intervals
- When calculating return rates on small cohorts, naive division (e.g. 1/1 = 100%) distorts reality.
- The platform calculates **Wilson score 95% confidence intervals** (`ci_low`, `ci_high`) for all segmentations across Category, Sub-Category, Brand, SKU, Fulfillment Type, and Payment Method.
- Distinguishes **Predicted Probability** (pre-shipment risk estimate) from **Actual Return Rate** (empirical outcome logged post-delivery).

### D. Automated Return Reduction Action Plans
- The recommendation engine scans company catalog history for statistically significant return drivers.
- Generates targeted interventions:
  - High-defect items: Require supplier QA certification and packaging reinforcement.
  - High-discount apparel with COD: Implement SMS pre-dispatch address verification and sizing chart prompt.
  - Fragile home goods: Upgrade cushioning to double-wall corrugated packaging.
- Supports operational statuses (`open`, `in_progress`, `implemented`, `dismissed`).
- When marked as `implemented` with an implementation date, the system measures **Before vs After Outcome Impact** to calculate real return rate reduction in percentage points.

### E. Data Ingestion & 1-Click Seeder
- **CSV Ingestion:** Ingest historical orders with idempotency (skips duplicate order reference IDs per company).
- **Downloadable CSV Template:** Pre-formatted with exact column headers and sample data.
- **1-Click 150-Order Demo Seeder:** Seed 150 realistic orders with verified return outcomes directly into any new company workspace to explore analytics instantly.

---

## 5. Running Automated Tests

All tests are implemented using `pytest` and `fastapi.testclient`:

```bash
# Run all tests across backend, ML pipeline, and multi-tenant security:
.venv\Scripts\python.exe -m pytest -v
```

### Test Coverage Highlights:
- `tests/test_multi_company_platform.py`:
  - Company A and Company B registration, login, and logout.
  - Multi-company data isolation: Company B cannot see Company A's predictions, historical orders, or recommendations.
  - Direct access horizontal privilege escalation tests.
  - CSV import validation, duplicate avoidance, and template download.
  - Analytics with Wilson confidence intervals and period comparisons.
  - Recommendation status lifecycle and before/after impact calculations.
- `tests/test_prediction.py`:
  - Model artifact loading and schema validation.
  - Pre-shipment boundary checks (rating, price, distance).
  - Agreement with trained notebook baseline test cases.
- `tests/test_pages.py`:
  - Unauthenticated redirect protection.
  - Form rendering and error handling.

---

## 6. API Reference Summary

| Method | Endpoint | Description | Auth Required |
|---|---|---|---|
| `GET` | `/health` | System health and model readiness | No |
| `GET` | `/api/categories` | Valid categories, brands, and taxonomy | No |
| `GET` | `/api/presets` | Demonstration order presets for testing | No |
| `POST` | `/api/auth/register` | Register new company workspace | No |
| `POST` | `/api/auth/login` | Sign in to company workspace | No |
| `GET` | `/api/auth/me` | Current authenticated company profile | No |
| `POST` | `/api/auth/logout` | Sign out and clear session cookie | Yes |
| `POST` | `/api/predict` | Run pre-shipment return probability prediction | Optional (links to company if logged in) |
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

## 7. License

Internal Enterprise Operations Software & Machine Learning Pipeline.
