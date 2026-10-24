import React from 'react';
import { ArrowRight, ShieldCheck, Database, Sliders, CheckCircle2 } from 'lucide-react';

export default function Home({ currentCompany, onNavigate }) {
  return (
    <div>
      {/* Hero Section */}
      <section style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '3rem', alignItems: 'center', marginBottom: '4rem' }}>
        <div>
          <span className="badge badge-risk-low" style={{ marginBottom: '0.75rem' }}>
            Enterprise Logistics Intelligence
          </span>
          <h1 style={{ fontSize: '2.5rem', fontWeight: 800, lineHeight: 1.15, letterSpacing: '-0.025em', color: 'var(--text-primary)', marginBottom: '1rem' }}>
            Pre-Shipment Product Return Risk Analysis
          </h1>
          <p style={{ fontSize: '1.05rem', color: 'var(--text-secondary)', lineHeight: 1.6, marginBottom: '1.75rem', maxWidth: '580px' }}>
            Evaluate customer return propensity before fulfilling and dispatching orders. Designed for e-commerce operations teams to identify return drivers using clean, pre-shipment order and catalog data.
          </p>

          <div style={{ display: 'flex', gap: '0.75rem', flexWrap: 'wrap', marginBottom: '2rem' }}>
            {currentCompany ? (
              <>
                <button
                  className="btn btn-primary btn-lg"
                  onClick={() => onNavigate('dashboard')}
                >
                  Open Company Console
                  <ArrowRight size={16} />
                </button>
                <button
                  className="btn btn-secondary btn-lg"
                  onClick={() => onNavigate('predict')}
                >
                  Evaluate an Order
                </button>
              </>
            ) : (
              <>
                <button
                  className="btn btn-primary btn-lg"
                  onClick={() => onNavigate('register')}
                >
                  Register Company Workspace
                  <ArrowRight size={16} />
                </button>
                <button
                  className="btn btn-secondary btn-lg"
                  onClick={() => onNavigate('login')}
                >
                  Sign In
                </button>
                <button
                  className="btn btn-secondary btn-lg"
                  onClick={() => onNavigate('predict')}
                >
                  Evaluate an Order
                </button>
              </>
            )}
          </div>

          <div style={{ display: 'flex', gap: '1.75rem', fontSize: '0.82rem', color: 'var(--text-muted)', flexWrap: 'wrap', borderTop: '1px solid var(--border-light)', paddingTop: '1.25rem' }}>
            <div>
              <strong style={{ color: 'var(--text-primary)', fontFamily: 'var(--font-mono)' }}>0.3974</strong> Decision Threshold
            </div>
            <div>
              <strong style={{ color: 'var(--text-primary)', fontFamily: 'var(--font-mono)' }}>88.8%</strong> Test Recall
            </div>
            <div>
              <strong style={{ color: 'var(--text-primary)', fontFamily: 'var(--font-mono)' }}>0.8939</strong> Test ROC-AUC
            </div>
            <div>
              <strong style={{ color: 'var(--text-primary)' }}>Multi-Company</strong> Data Isolation
            </div>
          </div>
        </div>

        {/* Live CSS Order Inspection Preview */}
        <div>
          <div className="card" style={{ padding: 0, overflow: 'hidden', boxShadow: 'var(--shadow-lg)', border: '1px solid var(--border-medium)' }}>
            <div style={{ backgroundColor: 'var(--bg-subtle)', padding: '0.65rem 1rem', borderBottom: '1px solid var(--border-light)', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <div style={{ display: 'flex', gap: '0.35rem' }}>
                <span style={{ width: 10, height: 10, borderRadius: '50%', backgroundColor: '#ef4444' }}></span>
                <span style={{ width: 10, height: 10, borderRadius: '50%', backgroundColor: '#f59e0b' }}></span>
                <span style={{ width: 10, height: 10, borderRadius: '50%', backgroundColor: '#10b981' }}></span>
              </div>
              <span style={{ fontSize: '0.72rem', fontFamily: 'var(--font-mono)', color: 'var(--text-muted)' }}>
                INSPECTION_CONSOLE // ORDER-84920
              </span>
            </div>

            <div style={{ padding: '1.25rem' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '1rem', paddingBottom: '0.75rem', borderBottom: '1px solid var(--border-light)' }}>
                <div>
                  <div style={{ fontSize: '0.72rem', textTransform: 'uppercase', color: 'var(--text-muted)', fontWeight: 600 }}>
                    Merchandise SKU
                  </div>
                  <div style={{ fontWeight: 700, fontSize: '0.98rem', color: 'var(--text-primary)' }}>
                    Women's Outerwear (Fashion)
                  </div>
                  <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                    Brand_5 &bull; Catalog Price: $140.00
                  </div>
                </div>
                <span className="badge badge-risk-high">
                  HIGHER RETURN RISK
                </span>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.75rem', marginBottom: '1rem' }}>
                <div style={{ backgroundColor: 'var(--bg-subtle)', padding: '0.65rem 0.85rem', borderRadius: 'var(--radius-xs)' }}>
                  <div style={{ color: 'var(--text-muted)', fontSize: '0.72rem', textTransform: 'uppercase' }}>Estimated Probability</div>
                  <div style={{ fontSize: '1.45rem', fontWeight: 800, color: 'var(--risk-high-accent)' }}>78.4%</div>
                </div>
                <div style={{ backgroundColor: 'var(--bg-subtle)', padding: '0.65rem 0.85rem', borderRadius: 'var(--radius-xs)' }}>
                  <div style={{ color: 'var(--text-muted)', fontSize: '0.72rem', textTransform: 'uppercase' }}>Operational Threshold</div>
                  <div style={{ fontSize: '1.45rem', fontWeight: 800, color: 'var(--text-primary)' }}>39.7%</div>
                </div>
              </div>

              <div style={{ fontSize: '0.82rem', color: 'var(--text-secondary)', backgroundColor: '#fff', border: '1px solid var(--border-light)', padding: '0.65rem 0.85rem', borderRadius: 'var(--radius-xs)' }}>
                <strong>Operational Signal:</strong> Cash on Delivery (COD) payment combined with deep promotional discount (55%) and high defect rate profile (9.0%). Protective packaging and pre-dispatch SMS verification recommended.
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Feature Pillars Grid */}
      <section style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '1.5rem', marginBottom: '3.5rem' }}>
        <div className="card">
          <div style={{ color: 'var(--accent-primary)', marginBottom: '0.75rem' }}>
            <ShieldCheck size={28} />
          </div>
          <h3 style={{ fontSize: '1.05rem', fontWeight: 700, marginBottom: '0.4rem' }}>
            Zero Point-in-Time Data Leakage
          </h3>
          <p style={{ fontSize: '0.86rem', color: 'var(--text-secondary)', lineHeight: 1.5 }}>
            Strictly excludes post-purchase attributes like delayed delivery, customer support calls, and chat interactions so predictions can genuinely execute prior to dispatch.
          </p>
        </div>

        <div className="card">
          <div style={{ color: 'var(--accent-primary)', marginBottom: '0.75rem' }}>
            <Database size={28} />
          </div>
          <h3 style={{ fontSize: '1.05rem', fontWeight: 700, marginBottom: '0.4rem' }}>
            Multi-Company Data Isolation
          </h3>
          <p style={{ fontSize: '0.86rem', color: 'var(--text-secondary)', lineHeight: 1.5 }}>
            Each registered company workspace operates with strict data isolation. Historical return outcomes, catalog records, and recommendation audits are query-scoped on the server.
          </p>
        </div>

        <div className="card">
          <div style={{ color: 'var(--accent-primary)', marginBottom: '0.75rem' }}>
            <Sliders size={28} />
          </div>
          <h3 style={{ fontSize: '1.05rem', fontWeight: 700, marginBottom: '0.4rem' }}>
            Tuned Recall Threshold (0.3974)
          </h3>
          <p style={{ fontSize: '0.86rem', color: 'var(--text-secondary)', lineHeight: 1.5 }}>
            Calibrated on validation data to achieve ~90% return recall, safeguarding logistics teams from unexpected return freight and reverse logistics overhead.
          </p>
        </div>
      </section>
    </div>
  );
}
