import React, { useState, useEffect } from 'react';
import { api } from '../api';
import { BarChart3, Filter, RefreshCw, AlertCircle, TrendingUp, Info } from 'lucide-react';

const SEGMENTS = [
  { id: 'product_category', label: 'Product Category' },
  { id: 'sub_category', label: 'Sub-Category' },
  { id: 'brand', label: 'Brand Identifier' },
  { id: 'product_identifier', label: 'Product SKU' },
  { id: 'fulfillment_type', label: 'Fulfillment Channel' },
  { id: 'payment_method', label: 'Payment Method' },
  { id: 'return_reason', label: 'Empirical Return Reason' },
];

export default function Analytics({ onNavigate }) {
  const [segment, setSegment] = useState('product_category');
  const [minSamples, setMinSamples] = useState(5);
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const loadAnalytics = async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await api.getAnalytics(segment, minSamples);
      setData(res);
    } catch (err) {
      setError(err.message || 'Failed to load return analytics.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadAnalytics();
  }, [segment, minSamples]);

  const currentSegmentLabel = SEGMENTS.find((s) => s.id === segment)?.label || segment;

  return (
    <div>
      <div style={{ marginBottom: '1.75rem' }}>
        <span className="badge badge-risk-low" style={{ marginBottom: '0.4rem' }}>Empirical Intelligence</span>
        <h1 className="page-title">Historical Return Analytics & Segmentation</h1>
        <p className="page-lead">
          Slice verified actual order outcomes across merchandising, fulfillment, and payment dimensions with statistical confidence intervals.
        </p>
      </div>

      {/* Control Bar */}
      <div className="card" style={{ padding: '1rem 1.25rem', marginBottom: '2rem', backgroundColor: 'var(--bg-surface)' }}>
        <div style={{ display: 'flex', gap: '1.5rem', flexWrap: 'wrap', alignItems: 'center' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <Filter size={15} color="var(--accent-primary)" />
            <strong style={{ fontSize: '0.86rem', color: 'var(--text-primary)' }}>Dimension:</strong>
            <select
              className="form-control"
              style={{ width: 'auto', padding: '0.4rem 0.75rem', fontSize: '0.84rem' }}
              value={segment}
              onChange={(e) => setSegment(e.target.value)}
            >
              {SEGMENTS.map((s) => (
                <option key={s.id} value={s.id}>{s.label}</option>
              ))}
            </select>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <strong style={{ fontSize: '0.86rem', color: 'var(--text-primary)' }}>Min Verified Orders:</strong>
            <select
              className="form-control"
              style={{ width: 'auto', padding: '0.4rem 0.75rem', fontSize: '0.84rem' }}
              value={minSamples}
              onChange={(e) => setMinSamples(parseInt(e.target.value, 10))}
            >
              <option value={1}>1 order (unfiltered)</option>
              <option value={3}>3 orders</option>
              <option value={5}>5 orders (recommended)</option>
              <option value={10}>10 orders (high confidence)</option>
              <option value={20}>20 orders</option>
            </select>
          </div>

          <div style={{ marginLeft: 'auto', fontSize: '0.8rem', color: 'var(--text-muted)' }}>
            Confidence Level: <strong>95% Wilson Score Interval</strong>
          </div>
        </div>
      </div>

      {error && (
        <div className="callout callout-danger" style={{ marginBottom: '1.5rem' }}>
          <strong>Error:</strong> {error}
        </div>
      )}

      {loading ? (
        <div style={{ textAlign: 'center', padding: '4rem 1rem' }}>
          <div className="animate-spin" style={{ display: 'inline-block', marginBottom: '0.75rem', color: 'var(--accent-primary)' }}>
            <RefreshCw size={28} />
          </div>
          <p style={{ color: 'var(--text-muted)' }}>Calculating empirical segment distributions...</p>
        </div>
      ) : (
        <div style={{ display: 'grid', gridTemplateColumns: '1fr', gap: '2rem' }}>
          {/* Main Segment Table */}
          <div className="card">
            <div className="card-header">
              <div>
                <h2 className="card-title">{currentSegmentLabel} Return Rate Breakdown</h2>
                <p className="card-subtitle">
                  Ranked by empirical actual return rate &bull; Minimum sample size: {minSamples} orders
                </p>
              </div>
              <span className="badge badge-neutral">
                {data?.segment_data?.length || 0} segments qualified
              </span>
            </div>

            {data?.segment_data?.length > 0 ? (
              <div className="table-responsive">
                <table className="data-table">
                  <thead>
                    <tr>
                      <th>{currentSegmentLabel}</th>
                      <th className="text-right">Completed Orders</th>
                      <th className="text-right">Verified Returns</th>
                      <th className="text-right">Actual Return Rate</th>
                      <th className="text-center">95% Confidence Interval</th>
                      <th className="text-center">Risk Assessment</th>
                    </tr>
                  </thead>
                  <tbody>
                    {data.segment_data.map((row, idx) => {
                      const isHigh = row.return_rate >= 25.0;
                      const segmentName = row.segment || row.segment_value || '(Unassigned)';
                      const ordersCount = row.orders ?? row.total_orders ?? 0;
                      const returnsCount = row.returns ?? row.returns_count ?? 0;
                      const ciLow = row.ci_low ?? row.ci_lower ?? 0;
                      const ciHigh = row.ci_high ?? row.ci_upper ?? 0;

                      return (
                        <tr key={idx}>
                          <td>
                            <strong>{segmentName}</strong>
                          </td>
                          <td className="text-right">{ordersCount}</td>
                          <td className="text-right">{returnsCount}</td>
                          <td className="text-right">
                            <strong style={{ color: isHigh ? 'var(--risk-high-accent)' : 'var(--text-primary)' }}>
                              {row.return_rate}%
                            </strong>
                          </td>
                          <td className="text-center" style={{ fontFamily: 'var(--font-mono)', fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                            {ciLow !== null && ciHigh !== null ? `[${ciLow}% – ${ciHigh}%]` : '–'}
                          </td>
                          <td className="text-center">
                            {isHigh ? (
                              <span className="badge badge-risk-high">High Return</span>
                            ) : (
                              <span className="badge badge-risk-low">Standard</span>
                            )}
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            ) : (
              <div style={{ textAlign: 'center', padding: '2.5rem 1rem' }}>
                <p style={{ color: 'var(--text-muted)', marginBottom: '1rem' }}>
                  No segments satisfy the minimum order requirement ({minSamples} orders).
                </p>
                <button className="btn btn-secondary btn-sm" onClick={() => setMinSamples(1)}>
                  Lower Threshold to 1 Order
                </button>
              </div>
            )}
          </div>

          {/* Factor Associations Card */}
          {data?.feature_correlations?.length > 0 && (
            <div className="card">
              <div className="card-header">
                <div>
                  <h2 className="card-title">Empirical Factor Associations with Return Outcomes</h2>
                  <p className="card-subtitle">
                    Comparing mean attribute values between returned orders and kept orders in your company dataset
                  </p>
                </div>
                <span className="badge badge-neutral">Observational Evidence</span>
              </div>

              <div className="table-responsive">
                <table className="data-table">
                  <thead>
                    <tr>
                      <th>Continuous Attribute</th>
                      <th className="text-right">Mean in Returned Orders</th>
                      <th className="text-right">Mean in Kept Orders</th>
                      <th className="text-right">Difference (&Delta;)</th>
                      <th>Operational Interpretation</th>
                    </tr>
                  </thead>
                  <tbody>
                    {data.feature_correlations.map((f, idx) => {
                      const diff = f.diff;
                      return (
                        <tr key={idx}>
                          <td><strong>{f.feature_label}</strong></td>
                          <td className="text-right" style={{ fontFamily: 'var(--font-mono)' }}>
                            {f.returned_mean}
                          </td>
                          <td className="text-right" style={{ fontFamily: 'var(--font-mono)' }}>
                            {f.kept_mean}
                          </td>
                          <td className="text-right" style={{ fontFamily: 'var(--font-mono)', fontWeight: 600 }}>
                            <span style={{ color: diff > 0 ? 'var(--risk-high-accent)' : 'var(--risk-low-accent)' }}>
                              {diff > 0 ? `+${diff}` : diff}
                            </span>
                          </td>
                          <td style={{ fontSize: '0.82rem', color: 'var(--text-secondary)' }}>
                            {f.interpretation}
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
