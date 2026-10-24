import React, { useState, useEffect } from 'react';
import { api } from '../api';
import {
  ArrowLeft,
  CheckCircle2,
  AlertTriangle,
  RotateCcw,
  Printer,
  History,
  RefreshCw,
  Cpu,
  ShieldCheck
} from 'lucide-react';

export default function PredictionDetail({ predictionId, onNavigate }) {
  const [record, setRecord] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    async function fetchDetail() {
      if (!predictionId) {
        setError('No prediction ID specified.');
        setLoading(false);
        return;
      }

      try {
        setLoading(true);
        setError(null);
        const data = await api.getPredictionDetail(predictionId);
        setRecord(data);
      } catch (err) {
        setError(err.message || 'Failed to load prediction audit details.');
      } finally {
        setLoading(false);
      }
    }
    fetchDetail();
  }, [predictionId]);

  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: '4rem 1rem' }}>
        <div className="animate-spin" style={{ display: 'inline-block', marginBottom: '0.75rem', color: 'var(--accent-primary)' }}>
          <RefreshCw size={28} />
        </div>
        <p style={{ color: 'var(--text-muted)' }}>Retrieving audit record #{predictionId}...</p>
      </div>
    );
  }

  if (error || !record) {
    return (
      <div className="empty-state">
        <AlertTriangle size={36} color="var(--risk-high-accent)" style={{ marginBottom: '0.75rem' }} />
        <h2 className="empty-title">Audit Record Not Found</h2>
        <p className="empty-desc">{error || 'This record could not be located in your company workspace.'}</p>
        <button className="btn btn-primary" onClick={() => onNavigate('history')}>
          <ArrowLeft size={15} />
          Back to History
        </button>
      </div>
    );
  }

  const isHighRisk = record.predicted_class === 1;
  const comp = record.comparison;

  return (
    <div>
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '1.5rem' }}>
        <button
          className="btn btn-secondary btn-sm"
          onClick={() => onNavigate('history')}
        >
          <ArrowLeft size={14} />
          Back to History
        </button>
        <span style={{ fontSize: '0.82rem', color: 'var(--text-muted)' }}>
          Audit Record <strong>#{record.id}</strong> &bull; Recorded {record.created_at}
        </span>
      </div>

      {/* Hero Banner */}
      <div className={`result-hero ${isHighRisk ? 'risk-high' : 'risk-low'}`} style={{ marginBottom: '2rem' }}>
        <div>
          <span className="result-badge">
            {isHighRisk ? <AlertTriangle size={12} /> : <CheckCircle2 size={12} />}
            {record.risk_level} Risk Tier &bull; Model {record.model_version}
          </span>
          <h2 className="result-title">{record.risk_label}</h2>
          <p className="result-interpretation">
            Evaluated on pre-shipment attributes via source channel: <strong>{record.source || 'interactive'}</strong>.
            {isHighRisk
              ? ' Estimated probability exceeds operational decision threshold, indicating heightened return likelihood.'
              : ' Estimated probability sits below operational decision threshold, indicating standard return likelihood.'}
          </p>
        </div>

        <div className="result-stats-card">
          <div className="stat-label">Estimated Probability</div>
          <div className="prob-metric">{record.prob_pct}%</div>
          <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginTop: '0.35rem' }}>
            Decision Threshold: <strong>{record.threshold_pct}%</strong>
          </div>
        </div>
      </div>

      {/* Historical Context Comparison */}
      {comp && (
        <div className="card" style={{ marginBottom: '2rem', borderLeft: '4px solid var(--accent-primary)' }}>
          <div className="card-header">
            <div>
              <h2 className="card-title" style={{ marginBottom: '0.2rem' }}>Historical Performance Benchmark</h2>
              <p className="card-subtitle">Segment: <strong>{comp.category}</strong></p>
            </div>
            <span className="badge badge-neutral">Empirical Comparison</span>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '1rem', marginBottom: '1.25rem' }}>
            <div style={{ background: 'var(--bg-surface)', border: '1px solid var(--border-light)', padding: '1rem', borderRadius: 'var(--radius-sm)' }}>
              <div style={{ fontSize: '0.74rem', textTransform: 'uppercase', color: 'var(--text-muted)', fontWeight: 600 }}>
                This Order Score
              </div>
              <div style={{ fontSize: '1.5rem', fontWeight: 800, color: isHighRisk ? 'var(--risk-high-accent)' : 'var(--risk-low-accent)' }}>
                {record.prob_pct}%
              </div>
              <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>Pre-shipment prediction</div>
            </div>

            <div style={{ background: 'var(--bg-surface)', border: '1px solid var(--border-light)', padding: '1rem', borderRadius: 'var(--radius-sm)' }}>
              <div style={{ fontSize: '0.74rem', textTransform: 'uppercase', color: 'var(--text-muted)', fontWeight: 600 }}>
                Category Actual Return Rate
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

      {/* Submitted Features Table */}
      <div className="card" style={{ marginBottom: '2rem' }}>
        <div className="card-header">
          <div>
            <h2 className="card-title">Pre-Shipment Input Features</h2>
            <p className="card-subtitle">Exact parameters captured at time of inference</p>
          </div>
          <span className="badge badge-risk-low">Audit Verified</span>
        </div>

        <div className="table-responsive">
          <table className="data-table">
            <thead>
              <tr>
                <th>Feature Name</th>
                <th>Submitted Value</th>
                <th>Feature Name</th>
                <th>Submitted Value</th>
              </tr>
            </thead>
            <tbody>
              {(() => {
                const items = Object.entries(record.features || {});
                const rows = [];
                for (let i = 0; i < items.length; i += 2) {
                  rows.push(
                    <tr key={i}>
                      <td style={{ fontWeight: 600, color: 'var(--text-primary)', width: '25%' }}>{items[i][0]}</td>
                      <td style={{ fontFamily: 'var(--font-mono)', width: '25%' }}>{String(items[i][1])}</td>
                      {items[i + 1] ? (
                        <>
                          <td style={{ fontWeight: 600, color: 'var(--text-primary)', width: '25%' }}>{items[i + 1][0]}</td>
                          <td style={{ fontFamily: 'var(--font-mono)', width: '25%' }}>{String(items[i + 1][1])}</td>
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

      {/* Navigation Actions */}
      <div style={{ display: 'flex', gap: '0.75rem', flexWrap: 'wrap' }}>
        <button className="btn btn-secondary" onClick={() => onNavigate('history')}>
          <ArrowLeft size={15} />
          Back to History
        </button>
        <button className="btn btn-primary" onClick={() => onNavigate('predict')}>
          <Cpu size={15} />
          Evaluate Another Order
        </button>
        <button className="btn btn-secondary" onClick={() => window.print()}>
          <Printer size={15} />
          Print Audit Record
        </button>
      </div>
    </div>
  );
}
