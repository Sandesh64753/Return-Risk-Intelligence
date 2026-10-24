import React from 'react';
import {
  CheckCircle2,
  AlertTriangle,
  RotateCcw,
  Printer,
  LayoutDashboard,
  History,
  Info
} from 'lucide-react';

export default function Result({ result, onNavigate }) {
  if (!result) {
    return (
      <div className="empty-state">
        <h2 className="empty-title">No Evaluation Results</h2>
        <p className="empty-desc">Please evaluate an order first to view probability and historical comparison metrics.</p>
        <button className="btn btn-primary" onClick={() => onNavigate('predict')}>
          Go to Predict
        </button>
      </div>
    );
  }

  const isHighRisk = result.predicted_class === 1;
  const comp = result.comparison;

  return (
    <div>
      <div style={{ marginBottom: '2rem' }}>
        <span className="badge badge-risk-low" style={{ marginBottom: '0.4rem' }}>Inference Report</span>
        <h1 className="page-title">Return Risk Assessment</h1>
        <p className="page-lead">
          Statistical return propensity evaluated strictly from pre-shipment order and catalog attributes.
        </p>
      </div>

      {/* Primary Result Hero Box */}
      <div className={`result-hero ${isHighRisk ? 'risk-high' : 'risk-low'}`}>
        <div>
          <span className="result-badge">
            {isHighRisk ? <AlertTriangle size={12} /> : <CheckCircle2 size={12} />}
            {result.risk_level} Risk Tier &bull; Operational Decision
          </span>
          <h2 className="result-title">{result.risk_label}</h2>
          <p className="result-interpretation">{result.interpretation}</p>
        </div>

        <div className="result-stats-card">
          <div className="stat-label">Estimated Probability</div>
          <div className="prob-metric">{result.probability_percent}%</div>
          <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginTop: '0.35rem' }}>
            Decision Threshold: <strong>{(result.threshold * 100).toFixed(1)}%</strong>
          </div>
        </div>
      </div>

      {/* Historical Company Context Comparison Block */}
      {comp && (
        <div className="card" style={{ marginBottom: '2rem', borderLeft: '4px solid var(--accent-primary)' }}>
          <div className="card-header">
            <div>
              <h2 className="card-title" style={{ marginBottom: '0.2rem' }}>Company Historical Performance Benchmark</h2>
              <p className="card-subtitle">Segment: <strong>{comp.category}</strong></p>
            </div>
            <span className="badge badge-neutral">Empirical Comparison</span>
          </div>

          <div style={{ backgroundColor: 'var(--bg-subtle)', padding: '0.85rem 1rem', borderRadius: 'var(--radius-sm)', marginBottom: '1.25rem', fontSize: '0.84rem', color: 'var(--text-secondary)' }}>
            <strong>Methodological Note:</strong> A predicted return probability is an estimated pre-shipment risk based on catalog attributes. It has a different meaning from the <em>actual return rate</em>, which is calculated strictly from completed orders with known post-delivery outcomes.
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '1rem', marginBottom: '1.25rem' }}>
            <div style={{ background: 'var(--bg-surface)', border: '1px solid var(--border-light)', padding: '1rem', borderRadius: 'var(--radius-sm)' }}>
              <div style={{ fontSize: '0.74rem', textTransform: 'uppercase', color: 'var(--text-muted)', fontWeight: 600 }}>
                Current Order Risk
              </div>
              <div style={{ fontSize: '1.5rem', fontWeight: 800, color: isHighRisk ? 'var(--risk-high-accent)' : 'var(--risk-low-accent)' }}>
                {result.probability_percent}%
              </div>
              <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>Pre-shipment model estimate</div>
            </div>

            <div style={{ background: 'var(--bg-surface)', border: '1px solid var(--border-light)', padding: '1rem', borderRadius: 'var(--radius-sm)' }}>
              <div style={{ fontSize: '0.74rem', textTransform: 'uppercase', color: 'var(--text-muted)', fontWeight: 600 }}>
                Category Historical Return Rate
              </div>
              <div style={{ fontSize: '1.5rem', fontWeight: 800, color: 'var(--text-primary)' }}>
                {comp.has_category_history ? `${comp.historical_actual_return_rate}%` : 'Pending'}
              </div>
              <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>
                {comp.has_category_history
                  ? `${comp.historical_return_count} returns / ${comp.historical_order_count} orders`
                  : 'Insufficient history (< 5 orders)'}
              </div>
            </div>

            {comp.has_product_history && (
              <div style={{ background: 'var(--bg-surface)', border: '1px solid var(--border-light)', padding: '1rem', borderRadius: 'var(--radius-sm)' }}>
                <div style={{ fontSize: '0.74rem', textTransform: 'uppercase', color: 'var(--text-muted)', fontWeight: 600 }}>
                  Product SKU Actual Rate
                </div>
                <div style={{ fontSize: '1.5rem', fontWeight: 800, color: 'var(--text-primary)' }}>
                  {comp.product_actual_return_rate}%
                </div>
                <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>
                  {comp.product_order_count} verified orders
                </div>
              </div>
            )}

            <div style={{ background: 'var(--bg-surface)', border: '1px solid var(--border-light)', padding: '1rem', borderRadius: 'var(--radius-sm)' }}>
              <div style={{ fontSize: '0.74rem', textTransform: 'uppercase', color: 'var(--text-muted)', fontWeight: 600 }}>
                Historical Avg Predicted Prob
              </div>
              <div style={{ fontSize: '1.5rem', fontWeight: 800, color: 'var(--text-primary)' }}>
                {comp.historical_avg_predicted_prob !== null ? `${comp.historical_avg_predicted_prob}%` : '--'}
              </div>
              <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>Prior model evaluations</div>
            </div>
          </div>

          {comp.comparison_notes?.length > 0 && (
            <ul style={{ listStyle: 'none', padding: 0, margin: 0 }}>
              {comp.comparison_notes.map((note, idx) => (
                <li key={idx} style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.84rem', color: 'var(--text-secondary)', marginBottom: '0.35rem' }}>
                  <CheckCircle2 size={14} color="var(--accent-primary)" />
                  <span>{note}</span>
                </li>
              ))}
            </ul>
          )}
        </div>
      )}

      {/* Key Factors */}
      {result.key_factors?.length > 0 && (
        <div className="card" style={{ marginBottom: '2rem' }}>
          <div className="card-header">
            <h2 className="card-title">Submitted Attributes of Operational Note</h2>
          </div>
          <ul style={{ listStyle: 'none', padding: 0, margin: 0 }}>
            {result.key_factors.map((factor, idx) => (
              <li
                key={idx}
                style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', padding: '0.5rem 0', borderBottom: idx < result.key_factors.length - 1 ? '1px solid var(--border-light)' : 'none', fontSize: '0.88rem', color: 'var(--text-secondary)' }}
              >
                <AlertTriangle size={15} color="var(--risk-mod-accent)" />
                <span>{factor}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Complete Submitted Parameter Summary Table */}
      {result.submitted_inputs && (
        <div className="card" style={{ marginBottom: '2rem' }}>
          <div className="card-header">
            <h2 className="card-title">Complete Submitted Parameters</h2>
            <span style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>
              {result.record_id ? `Audit Record #${result.record_id}` : 'Transmitted Inputs'}
            </span>
          </div>

          <div className="table-responsive">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Parameter</th>
                  <th>Submitted Value</th>
                  <th>Parameter</th>
                  <th>Submitted Value</th>
                </tr>
              </thead>
              <tbody>
                {(() => {
                  const items = Object.entries(result.submitted_inputs);
                  const rows = [];
                  for (let i = 0; i < items.length; i += 2) {
                    rows.push(
                      <tr key={i}>
                        <td style={{ fontWeight: 600, color: 'var(--text-primary)', width: '25%' }}>{items[i][0]}</td>
                        <td style={{ fontFamily: 'var(--font-mono)', width: '25%' }}>{items[i][1]}</td>
                        {items[i + 1] ? (
                          <>
                            <td style={{ fontWeight: 600, color: 'var(--text-primary)', width: '25%' }}>{items[i + 1][0]}</td>
                            <td style={{ fontFamily: 'var(--font-mono)', width: '25%' }}>{items[i + 1][1]}</td>
                          </>
                        ) : (
                          <><td></td><td></td></>
                        )}
                      </tr>
                    );
                  }
                  return rows;
                })()}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Navigation Toolbar */}
      <div style={{ display: 'flex', gap: '0.75rem', flexWrap: 'wrap', alignItems: 'center' }}>
        <button className="btn btn-primary" onClick={() => onNavigate('predict')}>
          <RotateCcw size={15} />
          Evaluate Another Order
        </button>
        {result.record_id && (
          <button
            className="btn btn-secondary"
            onClick={() => onNavigate('prediction_detail', { id: result.record_id })}
          >
            Audit Record #{result.record_id}
          </button>
        )}
        <button className="btn btn-secondary" onClick={() => onNavigate('dashboard')}>
          <LayoutDashboard size={15} />
          Dashboard
        </button>
        <button className="btn btn-secondary" onClick={() => window.print()}>
          <Printer size={15} />
          Print Assessment
        </button>
      </div>
    </div>
  );
}
