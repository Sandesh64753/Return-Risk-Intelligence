import React, { useState, useEffect } from 'react';
import { api } from '../api';
import { History as HistoryIcon, Search, Filter, ChevronLeft, ChevronRight, RefreshCw, Cpu, ExternalLink } from 'lucide-react';

export default function History({ onNavigate }) {
  const [records, setRecords] = useState([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [pageSize] = useState(15);
  const [riskFilter, setRiskFilter] = useState('all');
  const [categoryFilter, setCategoryFilter] = useState('all');
  const [categories, setCategories] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    async function loadMeta() {
      try {
        const catData = await api.getCategories();
        if (catData?.categories) {
          setCategories(Object.keys(catData.categories).sort());
        }
      } catch (e) {
        console.warn('Could not load categories list', e);
      }
    }
    loadMeta();
  }, []);

  const loadPredictions = async () => {
    try {
      setLoading(true);
      setError(null);
      const params = {
        page,
        page_size: pageSize,
      };
      if (riskFilter !== 'all') params.risk_level = riskFilter;
      if (categoryFilter !== 'all') params.category = categoryFilter;

      const data = await api.getPredictions(params);
      setRecords(data.records || []);
      setTotal(data.total || 0);
      setTotalPages(data.total_pages || 1);
    } catch (err) {
      setError(err.message || 'Failed to load historical predictions.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadPredictions();
  }, [page, riskFilter, categoryFilter]);

  const handleFilterChange = (setter) => (e) => {
    setter(e.target.value);
    setPage(1); // Reset to page 1 on filter change
  };

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '1rem', marginBottom: '1.75rem' }}>
        <div>
          <span className="badge badge-risk-low" style={{ marginBottom: '0.4rem' }}>Audit Log</span>
          <h1 className="page-title">Prediction History & Logs</h1>
          <p className="page-lead">
            Review past pre-shipment order assessments with stored input features and risk scores.
          </p>
        </div>
        <button className="btn btn-primary" onClick={() => onNavigate('predict')}>
          <Cpu size={15} />
          Evaluate New Order
        </button>
      </div>

      {/* Filter Toolbar */}
      <div className="card" style={{ padding: '1rem 1.25rem', marginBottom: '1.5rem', backgroundColor: 'var(--bg-surface)' }}>
        <div style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap', alignItems: 'center', justifyContent: 'space-between' }}>
          <div style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap', alignItems: 'center' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <Filter size={15} color="var(--text-muted)" />
              <span style={{ fontSize: '0.85rem', fontWeight: 600, color: 'var(--text-secondary)' }}>Filters:</span>
            </div>

            <div style={{ display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
              <label style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Risk Tier:</label>
              <select
                className="form-control"
                style={{ width: 'auto', padding: '0.35rem 0.65rem', fontSize: '0.84rem' }}
                value={riskFilter}
                onChange={handleFilterChange(setRiskFilter)}
              >
                <option value="all">All Risk Levels</option>
                <option value="High">High Risk Only</option>
                <option value="Low">Low Risk Only</option>
              </select>
            </div>

            <div style={{ display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
              <label style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Category:</label>
              <select
                className="form-control"
                style={{ width: 'auto', padding: '0.35rem 0.65rem', fontSize: '0.84rem' }}
                value={categoryFilter}
                onChange={handleFilterChange(setCategoryFilter)}
              >
                <option value="all">All Categories</option>
                {categories.map((c) => (
                  <option key={c} value={c}>{c}</option>
                ))}
              </select>
            </div>
          </div>

          <div style={{ fontSize: '0.82rem', color: 'var(--text-muted)' }}>
            Showing <strong>{records.length}</strong> of <strong>{total}</strong> records
          </div>
        </div>
      </div>

      {error && (
        <div className="callout callout-danger" style={{ marginBottom: '1.5rem' }}>
          <strong>Error:</strong> {error}
        </div>
      )}

      {loading ? (
        <div style={{ textAlign: 'center', padding: '3.5rem 1rem' }}>
          <div className="animate-spin" style={{ display: 'inline-block', marginBottom: '0.75rem', color: 'var(--accent-primary)' }}>
            <RefreshCw size={24} />
          </div>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.88rem' }}>Loading prediction records...</p>
        </div>
      ) : records.length === 0 ? (
        <div className="empty-state">
          <HistoryIcon size={36} color="var(--text-muted)" style={{ marginBottom: '0.75rem' }} />
          <h2 className="empty-title">No Prediction Records Found</h2>
          <p className="empty-desc">
            {riskFilter !== 'all' || categoryFilter !== 'all'
              ? 'No evaluations match your selected filter criteria. Try resetting filters.'
              : 'You have not evaluated any orders in this company workspace yet.'}
          </p>
          <div style={{ display: 'flex', gap: '0.75rem', justifyContent: 'center' }}>
            {(riskFilter !== 'all' || categoryFilter !== 'all') && (
              <button
                className="btn btn-secondary"
                onClick={() => {
                  setRiskFilter('all');
                  setCategoryFilter('all');
                  setPage(1);
                }}
              >
                Reset Filters
              </button>
            )}
            <button className="btn btn-primary" onClick={() => onNavigate('predict')}>
              <Cpu size={15} />
              Evaluate First Order
            </button>
          </div>
        </div>
      ) : (
        <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
          <div className="table-responsive">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Audit ID</th>
                  <th>Evaluation Date</th>
                  <th>Merchandise SKU / Category</th>
                  <th>Brand</th>
                  <th className="text-right">Estimated Probability</th>
                  <th className="text-center">Operational Verdict</th>
                  <th className="text-right">Action</th>
                </tr>
              </thead>
              <tbody>
                {records.map((r) => (
                  <tr key={r.id}>
                    <td>
                      <code style={{ fontSize: '0.82rem', fontWeight: 600 }}>#{r.id}</code>
                    </td>
                    <td style={{ color: 'var(--text-muted)', fontSize: '0.82rem' }}>
                      {r.created_at}
                    </td>
                    <td>
                      <div>
                        <strong>{r.category}</strong> &bull; {r.sub_category}
                      </div>
                      {r.sku && r.sku !== '-' && (
                        <span style={{ fontSize: '0.76rem', fontFamily: 'var(--font-mono)', color: 'var(--text-muted)' }}>
                          {r.sku}
                        </span>
                      )}
                    </td>
                    <td style={{ fontSize: '0.84rem' }}>{r.brand}</td>
                    <td className="text-right">
                      <strong
                        style={{
                          fontSize: '1rem',
                          color: r.predicted_class === 1 ? 'var(--risk-high-accent)' : 'var(--risk-low-accent)',
                        }}
                      >
                        {r.prob_pct}%
                      </strong>
                    </td>
                    <td className="text-center">
                      <span className={`badge ${r.predicted_class === 1 ? 'badge-risk-high' : 'badge-risk-low'}`}>
                        {r.risk_label}
                      </span>
                    </td>
                    <td className="text-right">
                      <button
                        className="btn btn-secondary btn-sm"
                        onClick={() => onNavigate('prediction_detail', { id: r.id })}
                        style={{ padding: '0.3rem 0.65rem', fontSize: '0.78rem' }}
                      >
                        <ExternalLink size={13} />
                        Audit Detail
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Pagination Footer */}
          {totalPages > 1 && (
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                padding: '0.85rem 1.25rem',
                borderTop: '1px solid var(--border-light)',
                backgroundColor: 'var(--bg-subtle)',
              }}
            >
              <div style={{ fontSize: '0.82rem', color: 'var(--text-muted)' }}>
                Page <strong>{page}</strong> of <strong>{totalPages}</strong>
              </div>
              <div style={{ display: 'flex', gap: '0.5rem' }}>
                <button
                  className="btn btn-secondary btn-sm"
                  disabled={page <= 1}
                  onClick={() => setPage((p) => Math.max(1, p - 1))}
                >
                  <ChevronLeft size={14} />
                  Previous
                </button>
                <button
                  className="btn btn-secondary btn-sm"
                  disabled={page >= totalPages}
                  onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                >
                  Next
                  <ChevronRight size={14} />
                </button>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
