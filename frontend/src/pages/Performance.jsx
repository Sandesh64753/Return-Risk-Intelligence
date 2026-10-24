import React, { useState, useEffect } from 'react';
import { api } from '../api';
import { TrendingDown, TrendingUp, Calendar, RefreshCw, AlertCircle, ArrowRight } from 'lucide-react';

const WINDOW_OPTIONS = [
  { days: 14, label: 'Last 14 Days' },
  { days: 30, label: 'Last 30 Days' },
  { days: 60, label: 'Last 60 Days' },
  { days: 90, label: 'Last 90 Days' },
];

export default function Performance({ onNavigate }) {
  const [windowDays, setWindowDays] = useState(30);
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const loadPerformance = async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await api.getPerformance(windowDays);
      setData(res);
    } catch (err) {
      setError(err.message || 'Failed to calculate period-over-period return performance.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadPerformance();
  }, [windowDays]);

  const curr = data?.current_period;
  const prev = data?.previous_period;
  const isImprovement = data?.diff_percentage_points !== null && data?.diff_percentage_points < 0;

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '1rem', marginBottom: '1.75rem' }}>
        <div>
          <span className="badge badge-risk-low" style={{ marginBottom: '0.4rem' }}>Outcome Monitoring</span>
          <h1 className="page-title">Return Rate Performance & Trends</h1>
          <p className="page-lead">
            Evaluate consecutive period-over-period return rate changes to verify if return reduction initiatives are succeeding.
          </p>
        </div>

        {/* Time Window Selector */}
        <div className="segmented-control">
          {WINDOW_OPTIONS.map((w) => (
            <button
              key={w.days}
              className={`segmented-btn ${windowDays === w.days ? 'active' : ''}`}
              onClick={() => setWindowDays(w.days)}
            >
              {w.label}
            </button>
          ))}
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
          <p style={{ color: 'var(--text-muted)' }}>Calculating period-over-period trajectory...</p>
        </div>
      ) : !data?.has_data ? (
        <div className="empty-state">
          <Calendar size={36} color="var(--text-muted)" style={{ marginBottom: '0.75rem' }} />
          <h2 className="empty-title">Insufficient Historical Orders</h2>
          <p className="empty-desc">
            To calculate period comparisons, your workspace needs verified order records with purchase dates. Import historical order outcomes to activate trend intelligence.
          </p>
          <button className="btn btn-primary" onClick={() => onNavigate('import')}>
            Import Historical Outcomes
          </button>
        </div>
      ) : (
        <div>
          {/* Delta Highlights Banner */}
          <div
            className="card"
            style={{
              padding: '1.5rem',
              marginBottom: '2rem',
              borderLeft: `4px solid ${isImprovement ? 'var(--risk-low-accent)' : 'var(--risk-mod-accent)'}`,
              backgroundColor: isImprovement ? 'var(--risk-low-bg)' : 'var(--bg-surface)',
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem' }}>
              <div>
                <span style={{ fontSize: '0.74rem', textTransform: 'uppercase', fontWeight: 700, color: 'var(--text-muted)' }}>
                  Period Comparison Verdict ({windowDays}-Day Window)
                </span>
                <h2 style={{ fontSize: '1.4rem', fontWeight: 800, color: 'var(--text-primary)', marginTop: '0.2rem' }}>
                  {data.diff_percentage_points === null
                    ? 'Baseline Established'
                    : isImprovement
                    ? `Return Rate Reduced by ${Math.abs(data.diff_percentage_points)} ppt`
                    : `Return Rate Increased by ${data.diff_percentage_points} ppt`}
                </h2>
                <p style={{ fontSize: '0.86rem', color: 'var(--text-secondary)', marginTop: '0.35rem' }}>
                  {curr?.start} &ndash; {curr?.end} compared against previous {windowDays}-day baseline ({prev?.start} &ndash; {prev?.end}).
                </p>
              </div>

              {data.diff_percentage_points !== null && (
                <div style={{ textAlign: 'right' }}>
                  <div
                    style={{
                      fontSize: '2rem',
                      fontWeight: 800,
                      display: 'flex',
                      alignItems: 'center',
                      gap: '0.35rem',
                      color: isImprovement ? 'var(--risk-low-accent)' : 'var(--risk-high-accent)',
                    }}
                  >
                    {isImprovement ? <TrendingDown size={28} /> : <TrendingUp size={28} />}
                    {data.diff_percentage_points > 0 ? `+${data.diff_percentage_points}` : data.diff_percentage_points} ppt
                  </div>
                  {data.relative_change_pct !== null && (
                    <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                      Relative change: <strong>{data.relative_change_pct}%</strong>
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>

          {/* Period Detail Side-by-Side Cards */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '1.5rem', marginBottom: '2.5rem' }}>
            {/* Current Window Card */}
            <div className="card">
              <div className="card-header">
                <div>
                  <h3 className="card-title">Recent Window ({windowDays} Days)</h3>
                  <p className="card-subtitle">{curr?.start} &ndash; {curr?.end}</p>
                </div>
                <span className="badge badge-risk-low">Current Active</span>
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', marginTop: '0.5rem' }}>
                <div style={{ backgroundColor: 'var(--bg-subtle)', padding: '0.85rem', borderRadius: 'var(--radius-sm)' }}>
                  <div style={{ fontSize: '0.72rem', textTransform: 'uppercase', color: 'var(--text-muted)' }}>Total Orders</div>
                  <div style={{ fontSize: '1.5rem', fontWeight: 800, color: 'var(--text-primary)' }}>{curr?.orders || 0}</div>
                  <div style={{ fontSize: '0.76rem', color: 'var(--text-muted)' }}>{curr?.returns || 0} returned</div>
                </div>
                <div style={{ backgroundColor: 'var(--bg-subtle)', padding: '0.85rem', borderRadius: 'var(--radius-sm)' }}>
                  <div style={{ fontSize: '0.72rem', textTransform: 'uppercase', color: 'var(--text-muted)' }}>Return Rate</div>
                  <div style={{ fontSize: '1.5rem', fontWeight: 800, color: 'var(--accent-primary)' }}>
                    {curr?.return_rate !== null ? `${curr.return_rate}%` : '--'}
                  </div>
                  <div style={{ fontSize: '0.76rem', color: 'var(--text-muted)' }}>Empirical rate</div>
                </div>
              </div>
            </div>

            {/* Baseline Window Card */}
            <div className="card">
              <div className="card-header">
                <div>
                  <h3 className="card-title">Prior Window ({windowDays} Days)</h3>
                  <p className="card-subtitle">{prev?.start} &ndash; {prev?.end}</p>
                </div>
                <span className="badge badge-neutral">Comparison Baseline</span>
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', marginTop: '0.5rem' }}>
                <div style={{ backgroundColor: 'var(--bg-subtle)', padding: '0.85rem', borderRadius: 'var(--radius-sm)' }}>
                  <div style={{ fontSize: '0.72rem', textTransform: 'uppercase', color: 'var(--text-muted)' }}>Total Orders</div>
                  <div style={{ fontSize: '1.5rem', fontWeight: 800, color: 'var(--text-primary)' }}>{prev?.orders || 0}</div>
                  <div style={{ fontSize: '0.76rem', color: 'var(--text-muted)' }}>{prev?.returns || 0} returned</div>
                </div>
                <div style={{ backgroundColor: 'var(--bg-subtle)', padding: '0.85rem', borderRadius: 'var(--radius-sm)' }}>
                  <div style={{ fontSize: '0.72rem', textTransform: 'uppercase', color: 'var(--text-muted)' }}>Return Rate</div>
                  <div style={{ fontSize: '1.5rem', fontWeight: 800, color: 'var(--text-secondary)' }}>
                    {prev?.return_rate !== null ? `${prev.return_rate}%` : '--'}
                  </div>
                  <div style={{ fontSize: '0.76rem', color: 'var(--text-muted)' }}>Baseline rate</div>
                </div>
              </div>
            </div>
          </div>

          {/* Monthly Cohort Progression Table */}
          {data.monthly_series?.length > 0 && (
            <div className="card">
              <div className="card-header">
                <div>
                  <h2 className="card-title">Monthly Return Cohort Series</h2>
                  <p className="card-subtitle">Aggregated return rates grouped by purchase month</p>
                </div>
                <span className="badge badge-neutral">Chronological Progression</span>
              </div>

              <div className="table-responsive">
                <table className="data-table">
                  <thead>
                    <tr>
                      <th>Month</th>
                      <th className="text-right">Order Volume</th>
                      <th className="text-right">Returns Logged</th>
                      <th className="text-right">Empirical Return Rate</th>
                      <th className="text-center">Trend Indicator</th>
                    </tr>
                  </thead>
                  <tbody>
                    {data.monthly_series.map((m, idx) => (
                      <tr key={idx}>
                        <td><strong>{m.month}</strong></td>
                        <td className="text-right">{m.orders}</td>
                        <td className="text-right">{m.returns}</td>
                        <td className="text-right">
                          <strong style={{ color: m.return_rate >= 25 ? 'var(--risk-high-accent)' : 'var(--text-primary)' }}>
                            {m.return_rate}%
                          </strong>
                        </td>
                        <td className="text-center">
                          {m.return_rate < 20 ? (
                            <span className="badge badge-risk-low">Healthy (&lt;20%)</span>
                          ) : m.return_rate < 30 ? (
                            <span className="badge badge-risk-mod">Moderate (20-30%)</span>
                          ) : (
                            <span className="badge badge-risk-high">Elevated (&gt;30%)</span>
                          )}
                        </td>
                      </tr>
                    ))}
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
