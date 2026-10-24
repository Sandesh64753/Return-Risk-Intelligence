import React, { useState, useEffect } from 'react';
import { api } from '../api';
import {
  Package,
  TrendingDown,
  AlertTriangle,
  Lightbulb,
  UploadCloud,
  Cpu,
  BarChart2,
  RefreshCw,
  CheckCircle2
} from 'lucide-react';

export default function Dashboard({ currentCompany, onNavigate }) {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [seeding, setSeeding] = useState(false);
  const [seedMessage, setSeedMessage] = useState(null);
  const [error, setError] = useState(null);

  const loadData = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await api.getDashboard();
      setStats(data);
    } catch (err) {
      setError(err.message || 'Failed to load dashboard metrics.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleSeedDemo = async () => {
    try {
      setSeeding(true);
      await api.seedDemoData();
      setSeedMessage('Successfully loaded 150 verified sample orders into your company workspace!');
      await loadData();
    } catch (err) {
      setError(err.message || 'Failed to seed sample orders.');
    } finally {
      setSeeding(false);
    }
  };

  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: '4rem 1rem' }}>
        <div className="animate-spin" style={{ display: 'inline-block', marginBottom: '1rem', color: 'var(--accent-primary)' }}>
          <RefreshCw size={28} />
        </div>
        <p style={{ color: 'var(--text-muted)' }}>Loading operations dashboard...</p>
      </div>
    );
  }

  return (
    <div>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '1rem', marginBottom: '2rem' }}>
        <div>
          <h1 className="page-title">{currentCompany.name} Operations Dashboard</h1>
          <p className="page-lead">
            Company workspace &bull; Vertical: <strong>{currentCompany.industry || 'General Merchandise'}</strong>
          </p>
        </div>
        <div style={{ display: 'flex', gap: '0.75rem', flexWrap: 'wrap' }}>
          <button className="btn btn-primary" onClick={() => onNavigate('predict')}>
            <Cpu size={15} />
            Evaluate New Order
          </button>
          <button className="btn btn-secondary" onClick={() => onNavigate('import')}>
            <UploadCloud size={15} />
            Import Outcomes
          </button>
        </div>
      </div>

      {seedMessage && (
        <div className="callout" style={{ backgroundColor: 'var(--accent-subtle)', borderLeft: '3px solid var(--accent-primary)', marginBottom: '1.5rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <CheckCircle2 size={16} color="var(--accent-primary)" />
          <span>{seedMessage}</span>
        </div>
      )}

      {error && (
        <div className="callout callout-danger" style={{ marginBottom: '1.5rem' }}>
          <strong>Error:</strong> {error}
        </div>
      )}

      {/* Operational Governance Principle Callout */}
      <div className="callout" style={{ backgroundColor: 'var(--bg-surface)', borderLeft: '3px solid var(--accent-primary)', marginBottom: '1.75rem' }}>
        <strong>Data Governance Principle:</strong> This console strictly separates <em>Pre-Shipment Predictions</em> (calibrated probability calculated from catalog attributes) from <em>Verified Return Outcomes</em> (empirical returns logged after fulfillment). Predictions never fabricate or distort actual return metrics.
      </div>

      {/* KPI Stats Grid */}
      <div className="stat-grid">
        <div className="stat-card">
          <div className="stat-label">Predictions Executed</div>
          <div className="stat-value">{stats?.total_predictions || 0}</div>
          <div className="stat-subtext">
            {stats?.total_predictions > 0 ? (
              <span><strong>{stats.high_risk_predictions}</strong> flagged high risk ({stats.high_risk_pct}%)</span>
            ) : (
              'No predictions performed yet'
            )}
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-label">Orders with Known Outcomes</div>
          <div className="stat-value">{stats?.total_known_orders || 0}</div>
          <div className="stat-subtext">Completed orders in company ledger</div>
        </div>

        <div className="stat-card">
          <div className="stat-label">Actual Return Rate</div>
          <div className="stat-value">
            {stats?.total_known_orders > 0 ? `${stats.actual_return_rate}%` : '--'}
          </div>
          <div className="stat-subtext">
            {stats?.total_known_orders > 0
              ? `${stats.actual_returns} returns / ${stats.total_known_orders} orders`
              : 'Awaiting verified outcomes'}
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-label">Active Recommendations</div>
          <div className="stat-value">{stats?.active_recs_count || 0}</div>
          <div className="stat-subtext">
            <button
              onClick={() => onNavigate('recommendations')}
              style={{ background: 'none', border: 'none', color: 'var(--accent-primary)', fontWeight: 600, padding: 0, cursor: 'pointer', fontSize: '0.82rem' }}
            >
              Review action plans &rarr;
            </button>
          </div>
        </div>
      </div>

      {/* Empty State vs Content */}
      {!stats?.has_data ? (
        <div className="empty-state">
          <div style={{ fontSize: '2.5rem', marginBottom: '0.75rem' }}>📊</div>
          <h2 className="empty-title">Your Company Workspace is Ready</h2>
          <p className="empty-desc">
            To generate returns intelligence, evaluate individual pre-shipment orders using our trained machine learning pipeline, or import historical actual order outcomes via CSV.
          </p>
          <div style={{ display: 'flex', justifyContent: 'center', gap: '0.75rem', flexWrap: 'wrap' }}>
            <button className="btn btn-primary" onClick={() => onNavigate('predict')}>
              <Cpu size={15} />
              Evaluate an Order
            </button>
            <button className="btn btn-secondary" onClick={() => onNavigate('import')}>
              <UploadCloud size={15} />
              Import Historical CSV
            </button>
            <button
              className="btn btn-secondary"
              onClick={handleSeedDemo}
              disabled={seeding}
              title="Load 150 verified sample orders from dataset"
            >
              {seeding ? (
                <>
                  <RefreshCw size={14} className="animate-spin" />
                  Loading...
                </>
              ) : (
                'Load Sample Dataset (1-Click)'
              )}
            </button>
          </div>
        </div>
      ) : (
        <div style={{ display: 'grid', gridTemplateColumns: '1fr', gap: '2rem' }}>
          {/* Top Return Categories Table */}
          <div className="card">
            <div className="card-header">
              <div>
                <h2 className="card-title" style={{ marginBottom: '0.2rem' }}>Highest Return Categories (Empirical Outcomes)</h2>
                <p className="card-subtitle">
                  Ranked by verified return rate &bull; Minimum sample size: <strong>{stats.min_sample_size} orders</strong>
                </p>
              </div>
              <button
                className="btn btn-secondary btn-sm"
                onClick={() => onNavigate('analytics')}
              >
                Full Analytics &rarr;
              </button>
            </div>

            {stats?.top_categories?.length > 0 ? (
              <div className="table-responsive">
                <table className="data-table">
                  <thead>
                    <tr>
                      <th>Category</th>
                      <th className="text-right">Completed Orders</th>
                      <th className="text-right">Actual Returns</th>
                      <th className="text-right">Actual Return Rate</th>
                      <th className="text-center">95% Confidence Interval</th>
                      <th className="text-center">Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {stats.top_categories.map((cat, idx) => (
                      <tr key={idx}>
                        <td><strong>{cat.category}</strong></td>
                        <td className="text-right">{cat.orders}</td>
                        <td className="text-right">{cat.returns}</td>
                        <td className="text-right">
                          <strong style={{ color: cat.return_rate >= 25 ? 'var(--risk-high-accent)' : 'var(--text-primary)' }}>
                            {cat.return_rate}%
                          </strong>
                        </td>
                        <td className="text-center" style={{ fontFamily: 'var(--font-mono)', fontSize: '0.78rem', color: 'var(--text-muted)' }}>
                          [{cat.ci_low}% &ndash; {cat.ci_high}%]
                        </td>
                        <td className="text-center">
                          {cat.return_rate >= 25 ? (
                            <span className="badge badge-risk-high">High Return</span>
                          ) : (
                            <span className="badge badge-risk-low">Standard</span>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <p style={{ color: 'var(--text-muted)', fontSize: '0.88rem', padding: '1rem 0' }}>
                No categories have reached the minimum sample size ({stats.min_sample_size} orders) yet.
              </p>
            )}
          </div>

          {/* Recent Predictions Stream */}
          <div className="card">
            <div className="card-header">
              <div>
                <h2 className="card-title" style={{ marginBottom: '0.2rem' }}>Recent Order Risk Assessments</h2>
                <p className="card-subtitle">Persisted model evaluation records for this company</p>
              </div>
              <button
                className="btn btn-secondary btn-sm"
                onClick={() => onNavigate('history')}
              >
                View History &rarr;
              </button>
            </div>

            {stats?.recent_predictions?.length > 0 ? (
              <div className="table-responsive">
                <table className="data-table">
                  <thead>
                    <tr>
                      <th>Audit ID</th>
                      <th>Timestamp</th>
                      <th>Category / SKU</th>
                      <th className="text-right">Return Probability</th>
                      <th className="text-center">Classification</th>
                      <th className="text-right">Action</th>
                    </tr>
                  </thead>
                  <tbody>
                    {stats.recent_predictions.map((p) => (
                      <tr key={p.id}>
                        <td><code>#{p.id}</code></td>
                        <td style={{ color: 'var(--text-muted)', fontSize: '0.82rem' }}>{p.created_at}</td>
                        <td>
                          <strong>{p.category}</strong> &bull; {p.sub_category}
                          {p.sku && p.sku !== '-' && (
                            <div style={{ fontSize: '0.76rem', color: 'var(--text-muted)' }}>{p.sku}</div>
                          )}
                        </td>
                        <td className="text-right">
                          <strong>{p.prob_pct}%</strong>
                        </td>
                        <td className="text-center">
                          <span className={`badge ${p.predicted_class === 1 ? 'badge-risk-high' : 'badge-risk-low'}`}>
                            {p.risk_label}
                          </span>
                        </td>
                        <td className="text-right">
                          <button
                            onClick={() => onNavigate('prediction_detail', { id: p.id })}
                            style={{ background: 'none', border: 'none', color: 'var(--accent-primary)', fontWeight: 600, fontSize: '0.82rem', cursor: 'pointer' }}
                          >
                            View Detail &rarr;
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <p style={{ color: 'var(--text-muted)', fontSize: '0.88rem', padding: '1rem 0' }}>
                No predictions recorded yet. Click "Evaluate New Order" above to run an inference.
              </p>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
