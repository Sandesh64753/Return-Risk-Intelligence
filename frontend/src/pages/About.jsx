import React from 'react';
import { Layers, Shield, Cpu, Database, Terminal, ArrowRight } from 'lucide-react';

export default function About({ onNavigate }) {
  return (
    <div style={{ maxWidth: '880px', margin: '0 auto' }}>
      <div style={{ marginBottom: '2.5rem' }}>
        <span className="badge badge-risk-low" style={{ marginBottom: '0.4rem' }}>Platform Overview</span>
        <h1 className="page-title">About Product Return Intelligence</h1>
        <p className="page-lead">
          An enterprise-grade, multi-company machine learning platform engineered to help e-commerce brands predict, analyze, and systematically reduce product returns.
        </p>
      </div>

      {/* Architecture Cards Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '1.5rem', marginBottom: '2.5rem' }}>
        <div className="card">
          <div style={{ color: 'var(--accent-primary)', marginBottom: '0.75rem' }}>
            <Layers size={26} />
          </div>
          <h2 style={{ fontSize: '1.1rem', fontWeight: 700, marginBottom: '0.4rem' }}>
            Decoupled Architecture
          </h2>
          <p style={{ fontSize: '0.86rem', color: 'var(--text-secondary)', lineHeight: 1.5 }}>
            Clean two-tier repository organization: <code>frontend/</code> runs a modern React 19 single-page application built on Vite, while <code>backend/</code> runs a high-performance Python FastAPI service with SQLAlchemy 2.x ORM and Alembic migrations.
          </p>
        </div>

        <div className="card">
          <div style={{ color: 'var(--accent-primary)', marginBottom: '0.75rem' }}>
            <Shield size={26} />
          </div>
          <h2 style={{ fontSize: '1.1rem', fontWeight: 700, marginBottom: '0.4rem' }}>
            Multi-Tenant Isolation
          </h2>
          <p style={{ fontSize: '0.86rem', color: 'var(--text-secondary)', lineHeight: 1.5 }}>
            Strict company-level data isolation guarantees that one merchant's historical return patterns, catalog SKUs, and recommendations are inaccessible to other companies. Authentication uses state-of-the-art Argon2id password hashing and signed session cookies.
          </p>
        </div>

        <div className="card">
          <div style={{ color: 'var(--accent-primary)', marginBottom: '0.75rem' }}>
            <Cpu size={26} />
          </div>
          <h2 style={{ fontSize: '1.1rem', fontWeight: 700, marginBottom: '0.4rem' }}>
            Calibrated ML Pipeline
          </h2>
          <p style={{ fontSize: '0.86rem', color: 'var(--text-secondary)', lineHeight: 1.5 }}>
            Serializes a production Scikit-Learn Logistic Regression model using strict pre-shipment point-in-time features with a tuned 0.3974 decision threshold that captures ~90% of return events prior to warehouse dispatch.
          </p>
        </div>
      </div>

      {/* Developer API & Integration */}
      <div className="card" style={{ marginBottom: '2.5rem' }}>
        <div className="card-header">
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <Terminal size={18} color="var(--accent-primary)" />
            <h2 className="card-title">Developer & Warehouse Integration API</h2>
          </div>
          <span className="badge badge-neutral">REST / OpenAPI</span>
        </div>

        <p style={{ fontSize: '0.88rem', color: 'var(--text-secondary)', lineHeight: 1.6, marginBottom: '1rem' }}>
          In addition to this visual operations console, the backend exposes comprehensive RESTful JSON endpoints for programmatic warehouse management system (WMS) and ERP integration.
        </p>

        <ul style={{ margin: '0 0 1.25rem 1.25rem', fontSize: '0.84rem', color: 'var(--text-secondary)', lineHeight: 1.6 }}>
          <li><code>POST /api/predict</code> &ndash; Real-time pre-shipment return probability inference</li>
          <li><code>GET /api/dashboard</code> &ndash; Authenticated company KPI summary & recent audits</li>
          <li><code>GET /api/analytics</code> &ndash; Wilson-scored return rates segmented by category, brand, or SKU</li>
          <li><code>GET /api/performance</code> &ndash; Period-over-period return reduction tracking</li>
          <li><code>GET /api/recommendations</code> &ndash; Targeted operational interventions & impact monitoring</li>
          <li><code>POST /api/import</code> &ndash; Bulk historical order outcome CSV ingestion</li>
        </ul>

        <div style={{ display: 'flex', gap: '0.75rem' }}>
          <a
            href="/docs"
            target="_blank"
            rel="noopener noreferrer"
            className="btn btn-secondary btn-sm"
          >
            Explore Interactive Swagger UI &rarr;
          </a>
          <a
            href="/redoc"
            target="_blank"
            rel="noopener noreferrer"
            className="btn btn-secondary btn-sm"
          >
            View ReDoc Specifications &rarr;
          </a>
        </div>
      </div>

      <div style={{ textAlign: 'center' }}>
        <button className="btn btn-primary" onClick={() => onNavigate('home')}>
          Return to Platform Home
        </button>
      </div>
    </div>
  );
}
