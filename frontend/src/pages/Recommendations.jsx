import React, { useState, useEffect } from 'react';
import { api } from '../api';
import {
  Lightbulb,
  CheckCircle2,
  Clock,
  XCircle,
  AlertTriangle,
  RefreshCw,
  TrendingDown,
  Calendar,
  Save,
  Tag
} from 'lucide-react';

export default function Recommendations({ onNavigate }) {
  const [recommendations, setRecommendations] = useState([]);
  const [statusFilter, setStatusFilter] = useState('all');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [updatingId, setUpdatingId] = useState(null);
  const [successMessage, setSuccessMessage] = useState(null);

  // Edit state for status modals/cards
  const [editingCard, setEditingCard] = useState({});

  const loadRecommendations = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await api.getRecommendations(statusFilter);
      setRecommendations(data || []);
    } catch (err) {
      setError(err.message || 'Failed to load recommendations.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadRecommendations();
  }, [statusFilter]);

  const handleStatusChange = async (recId, newStatus, reviewNotes, implDate) => {
    try {
      setUpdatingId(recId);
      setError(null);
      await api.updateRecommendationStatus(recId, {
        status: newStatus,
        review_notes: reviewNotes || undefined,
        implementation_date: implDate || undefined,
      });
      setSuccessMessage(`Recommendation #${recId} status updated to ${newStatus}.`);
      setTimeout(() => setSuccessMessage(null), 4000);
      await loadRecommendations();
    } catch (err) {
      setError(err.message || 'Failed to update recommendation.');
    } finally {
      setUpdatingId(null);
    }
  };

  const getStatusBadge = (status) => {
    switch (status) {
      case 'implemented':
        return <span className="badge badge-risk-low"><CheckCircle2 size={12} /> Implemented</span>;
      case 'in_progress':
        return <span className="badge badge-risk-mod"><Clock size={12} /> In Progress</span>;
      case 'dismissed':
        return <span className="badge badge-neutral"><XCircle size={12} /> Dismissed</span>;
      default:
        return <span className="badge badge-risk-high"><Lightbulb size={12} /> Open Action</span>;
    }
  };

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '1rem', marginBottom: '1.75rem' }}>
        <div>
          <span className="badge badge-risk-low" style={{ marginBottom: '0.4rem' }}>Operational Guidance</span>
          <h1 className="page-title">Return Reduction Action Plans</h1>
          <p className="page-lead">
            Rule-driven interventions derived from empirical return patterns in your company's order history.
          </p>
        </div>

        {/* Filter Toolbar */}
        <div className="segmented-control">
          {['all', 'open', 'in_progress', 'implemented', 'dismissed'].map((st) => (
            <button
              key={st}
              className={`segmented-btn ${statusFilter === st ? 'active' : ''}`}
              onClick={() => setStatusFilter(st)}
              style={{ textTransform: 'capitalize' }}
            >
              {st.replace('_', ' ')}
            </button>
          ))}
        </div>
      </div>

      {successMessage && (
        <div className="callout" style={{ backgroundColor: 'var(--accent-subtle)', borderLeft: '3px solid var(--accent-primary)', marginBottom: '1.5rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <CheckCircle2 size={16} color="var(--accent-primary)" />
          <span>{successMessage}</span>
        </div>
      )}

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
          <p style={{ color: 'var(--text-muted)' }}>Scanning catalog for return reduction opportunities...</p>
        </div>
      ) : recommendations.length === 0 ? (
        <div className="empty-state">
          <Lightbulb size={36} color="var(--text-muted)" style={{ marginBottom: '0.75rem' }} />
          <h2 className="empty-title">No Recommendations in this Filter</h2>
          <p className="empty-desc">
            {statusFilter !== 'all'
              ? `No action plans currently marked as "${statusFilter.replace('_', ' ')}".`
              : 'Recommendations are automatically generated when specific categories, brands, or SKUs exceed empirical return thresholds with sufficient order history.'}
          </p>
          {statusFilter !== 'all' && (
            <button className="btn btn-secondary" onClick={() => setStatusFilter('all')}>
              View All Recommendations
            </button>
          )}
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
          {recommendations.map((rec) => {
            const cardState = editingCard[rec.id] || {
              status: rec.status,
              implementation_date: rec.implementation_date || new Date().toISOString().split('T')[0],
              review_notes: rec.review_notes || '',
            };

            const impact = rec.impact;

            return (
              <div key={rec.id} className="card" style={{ borderLeft: '4px solid var(--accent-primary)' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '0.75rem', marginBottom: '0.75rem' }}>
                  <div>
                    <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center', marginBottom: '0.35rem' }}>
                      {getStatusBadge(rec.status)}
                      <span className="badge badge-neutral">
                        <Tag size={10} style={{ marginRight: '0.25rem' }} />
                        {rec.segment_type.replace('_', ' ').toUpperCase()}: {rec.segment_identifier}
                      </span>
                    </div>
                    <h2 style={{ fontSize: '1.2rem', fontWeight: 700, color: 'var(--text-primary)' }}>
                      {rec.title}
                    </h2>
                  </div>
                  <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>
                    Generated: {rec.created_at}
                  </div>
                </div>

                <p style={{ fontSize: '0.9rem', color: 'var(--text-secondary)', marginBottom: '1rem', lineHeight: 1.5 }}>
                  {rec.text}
                </p>

                {/* Suggested Action Box */}
                <div
                  style={{
                    backgroundColor: 'var(--bg-subtle)',
                    border: '1px solid var(--border-light)',
                    borderRadius: 'var(--radius-sm)',
                    padding: '0.85rem 1rem',
                    marginBottom: '1rem',
                  }}
                >
                  <div style={{ fontSize: '0.74rem', textTransform: 'uppercase', fontWeight: 700, color: 'var(--text-muted)', marginBottom: '0.25rem' }}>
                    Recommended Operational Action
                  </div>
                  <div style={{ fontSize: '0.88rem', color: 'var(--text-primary)', fontWeight: 600 }}>
                    {rec.suggested_action}
                  </div>
                </div>

                {/* Evidence Metrics */}
                {rec.evidence && Object.keys(rec.evidence).length > 0 && (
                  <div style={{ display: 'flex', gap: '1.5rem', flexWrap: 'wrap', marginBottom: '1rem', padding: '0.5rem 0', borderTop: '1px solid var(--border-light)', borderBottom: '1px solid var(--border-light)', fontSize: '0.82rem' }}>
                    {Object.entries(rec.evidence).map(([k, v]) => (
                      <div key={k}>
                        <span style={{ color: 'var(--text-muted)' }}>{k.replace(/_/g, ' ')}: </span>
                        <strong style={{ color: 'var(--text-primary)' }}>{String(v)}</strong>
                      </div>
                    ))}
                  </div>
                )}

                {/* Before vs After Outcome Impact Tracking (if implemented) */}
                {impact && impact.has_data && (
                  <div
                    style={{
                      backgroundColor: 'var(--risk-low-bg)',
                      border: '1px solid var(--risk-low-border)',
                      borderRadius: 'var(--radius-sm)',
                      padding: '0.85rem 1rem',
                      marginBottom: '1.25rem',
                    }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.4rem' }}>
                      <TrendingDown size={16} color="var(--risk-low-accent)" />
                      <strong style={{ fontSize: '0.84rem', color: 'var(--risk-low-text)' }}>
                        Before vs After Outcome Impact Tracking
                      </strong>
                    </div>
                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))', gap: '0.75rem', fontSize: '0.82rem' }}>
                      <div>
                        <div style={{ color: 'var(--text-muted)' }}>Pre-Implementation Rate</div>
                        <div style={{ fontSize: '1.1rem', fontWeight: 800, color: 'var(--text-secondary)' }}>
                          {impact.before_rate !== null ? `${impact.before_rate}%` : '--'}
                        </div>
                        <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>{impact.before_orders} orders</div>
                      </div>
                      <div>
                        <div style={{ color: 'var(--text-muted)' }}>Post-Implementation Rate</div>
                        <div style={{ fontSize: '1.1rem', fontWeight: 800, color: 'var(--risk-low-accent)' }}>
                          {impact.after_rate !== null ? `${impact.after_rate}%` : '--'}
                        </div>
                        <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>{impact.after_orders} orders</div>
                      </div>
                      <div>
                        <div style={{ color: 'var(--text-muted)' }}>Empirical Difference</div>
                        <div style={{ fontSize: '1.1rem', fontWeight: 800, color: impact.diff_percentage_points <= 0 ? 'var(--risk-low-accent)' : 'var(--risk-high-accent)' }}>
                          {impact.diff_percentage_points <= 0 ? `${impact.diff_percentage_points} ppt` : `+${impact.diff_percentage_points} ppt`}
                        </div>
                        <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>Absolute delta</div>
                      </div>
                    </div>
                  </div>
                )}

                {/* Status Update Inline Controls */}
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', flexWrap: 'wrap', paddingTop: '0.5rem' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
                    <label style={{ fontSize: '0.78rem', fontWeight: 600, color: 'var(--text-muted)' }}>Status:</label>
                    <select
                      className="form-control"
                      style={{ width: 'auto', padding: '0.3rem 0.65rem', fontSize: '0.82rem' }}
                      value={cardState.status}
                      onChange={(e) =>
                        setEditingCard((prev) => ({
                          ...prev,
                          [rec.id]: { ...cardState, status: e.target.value },
                        }))
                      }
                    >
                      <option value="open">Open</option>
                      <option value="in_progress">In Progress</option>
                      <option value="implemented">Implemented</option>
                      <option value="dismissed">Dismissed</option>
                    </select>
                  </div>

                  {cardState.status === 'implemented' && (
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
                      <label style={{ fontSize: '0.78rem', fontWeight: 600, color: 'var(--text-muted)' }}>Date:</label>
                      <input
                        type="date"
                        className="form-control"
                        style={{ width: 'auto', padding: '0.25rem 0.5rem', fontSize: '0.8rem' }}
                        value={cardState.implementation_date}
                        onChange={(e) =>
                          setEditingCard((prev) => ({
                            ...prev,
                            [rec.id]: { ...cardState, implementation_date: e.target.value },
                          }))
                        }
                      />
                    </div>
                  )}

                  <input
                    type="text"
                    className="form-control"
                    style={{ flex: 1, minWidth: '180px', padding: '0.3rem 0.65rem', fontSize: '0.82rem' }}
                    placeholder="Add operational notes or team comments..."
                    value={cardState.review_notes}
                    onChange={(e) =>
                      setEditingCard((prev) => ({
                        ...prev,
                        [rec.id]: { ...cardState, review_notes: e.target.value },
                      }))
                    }
                  />

                  <button
                    className="btn btn-secondary btn-sm"
                    disabled={updatingId === rec.id}
                    onClick={() =>
                      handleStatusChange(
                        rec.id,
                        cardState.status,
                        cardState.review_notes,
                        cardState.status === 'implemented' ? cardState.implementation_date : null
                      )
                    }
                  >
                    {updatingId === rec.id ? (
                      <RefreshCw size={13} className="animate-spin" />
                    ) : (
                      <Save size={13} />
                    )}
                    Save Status
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
