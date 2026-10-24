# Product Return Risk Intelligence Platform - Frontend Console

Modern, responsive React SPA for multi-company retail logistics intelligence, return propensity prediction, batch ingestion, and operational analytics.

---

## Architecture Overview

- **Framework**: React 19 + Vite 8
- **Icons**: Lucide React
- **Styling**: Tailored glassmorphism UI with smooth CSS transitions and dark/light contrast
- **Production Server**: Alpine Nginx with reverse proxy for API, health, and docs
- **Authentication**: Session cookie credentials (`credentials: 'include'`)

---

## Containerization & Docker

The frontend is containerized using a multi-stage Docker build:
1. **Stage 1 (Node 20 Alpine)**: Installs dependencies (`npm ci`) and builds optimized static assets (`npm run build`).
2. **Stage 2 (Nginx Alpine)**: Serves static assets, configures gzip compression, handles client-side SPA routing (`try_files $uri $uri/ /index.html`), and reverse-proxies `/api`, `/health`, and `/docs` to the FastAPI backend.

### Running with Docker Compose (Full-Stack)
From the repository root:
```bash
docker compose up --build
```
- Frontend Operations Console: `http://localhost:3000`
- Backend API & Swagger: `http://localhost:8000/docs`

---

## Local Development (Without Docker)

### 1. Install Dependencies
```bash
npm install
```

### 2. Start Vite Dev Server
```bash
npm run dev
```
The Vite development server runs at `http://localhost:5173` and automatically proxies `/api` and `/health` requests to `http://127.0.0.1:8000`.

### 3. Production Build
```bash
npm run build
```
Generates production-ready distribution files in `dist/`.
