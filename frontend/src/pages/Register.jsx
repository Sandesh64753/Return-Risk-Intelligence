import React, { useState } from 'react';
import { api } from '../api';
import { UserPlus, Building2, Lock, Mail, Tag, AlertCircle } from 'lucide-react';

const INDUSTRIES = [
  'E-commerce & Marketplace',
  'Fashion & Apparel',
  'Consumer Electronics & Tech',
  'Home, Furniture & Living',
  'Health & Beauty',
  'Sports & Activewear',
  'Books & Stationery',
  'Other Merchandise',
];

export default function Register({ onRegisterSuccess, onNavigate }) {
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    industry: 'E-commerce & Marketplace',
    password: '',
    confirm_password: '',
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (formData.password !== formData.confirm_password) {
      setError('Passwords do not match. Please verify your entries.');
      return;
    }
    if (formData.password.length < 8) {
      setError('Password must be at least 8 characters long.');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const data = await api.register(formData);
      if (data.company) {
        onRegisterSuccess(data.company);
        onNavigate('dashboard');
      }
    } catch (err) {
      setError(err.message || 'Registration failed. Company email may already be registered.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ maxWidth: '520px', margin: '2.5rem auto' }}>
      <div className="card" style={{ padding: '2rem 2.25rem', boxShadow: 'var(--shadow-lg)' }}>
        <div style={{ textAlign: 'center', marginBottom: '1.75rem' }}>
          <div
            style={{
              width: 44,
              height: 44,
              borderRadius: 'var(--radius-md)',
              backgroundColor: 'var(--accent-subtle)',
              color: 'var(--accent-primary)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              margin: '0 auto 1rem',
            }}
          >
            <UserPlus size={24} />
          </div>
          <h1 style={{ fontSize: '1.45rem', fontWeight: 800, color: 'var(--text-primary)', marginBottom: '0.35rem' }}>
            Register Company Workspace
          </h1>
          <p style={{ fontSize: '0.86rem', color: 'var(--text-muted)' }}>
            Create an isolated tenant account for your organization with dedicated database scoping.
          </p>
        </div>

        {error && (
          <div
            className="callout callout-danger"
            style={{ marginBottom: '1.25rem', display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.84rem' }}
          >
            <AlertCircle size={16} />
            <span>{error}</span>
          </div>
        )}

        <form onSubmit={handleSubmit}>
          <div className="form-group" style={{ marginBottom: '1.15rem' }}>
            <label className="form-label" style={{ display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
              <Building2 size={14} color="var(--text-muted)" />
              Company Legal / Trading Name <span style={{ color: 'red' }}>*</span>
            </label>
            <input
              type="text"
              name="name"
              className="form-control"
              value={formData.name}
              onChange={handleChange}
              placeholder="e.g. Apex Retail Inc"
              required
              autoFocus
            />
          </div>

          <div className="form-group" style={{ marginBottom: '1.15rem' }}>
            <label className="form-label" style={{ display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
              <Mail size={14} color="var(--text-muted)" />
              Company Admin Email <span style={{ color: 'red' }}>*</span>
            </label>
            <input
              type="email"
              name="email"
              className="form-control"
              value={formData.email}
              onChange={handleChange}
              placeholder="e.g. ops@apexretail.com"
              required
            />
            <span className="field-hint">Used as your company login username</span>
          </div>

          <div className="form-group" style={{ marginBottom: '1.15rem' }}>
            <label className="form-label" style={{ display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
              <Tag size={14} color="var(--text-muted)" />
              Industry Vertical
            </label>
            <select
              name="industry"
              className="form-control"
              value={formData.industry}
              onChange={handleChange}
            >
              {INDUSTRIES.map((ind) => (
                <option key={ind} value={ind}>{ind}</option>
              ))}
            </select>
          </div>

          <div className="form-group" style={{ marginBottom: '1.15rem' }}>
            <label className="form-label" style={{ display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
              <Lock size={14} color="var(--text-muted)" />
              Workspace Password <span style={{ color: 'red' }}>*</span>
            </label>
            <input
              type="password"
              name="password"
              className="form-control"
              value={formData.password}
              onChange={handleChange}
              placeholder="Minimum 8 characters"
              required
            />
          </div>

          <div className="form-group" style={{ marginBottom: '1.5rem' }}>
            <label className="form-label" style={{ display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
              <Lock size={14} color="var(--text-muted)" />
              Confirm Password <span style={{ color: 'red' }}>*</span>
            </label>
            <input
              type="password"
              name="confirm_password"
              className="form-control"
              value={formData.confirm_password}
              onChange={handleChange}
              placeholder="Re-enter password"
              required
            />
          </div>

          <button
            type="submit"
            className="btn btn-primary btn-lg"
            disabled={loading}
            style={{ width: '100%', justifyContent: 'center' }}
          >
            {loading ? (
              'Creating Workspace...'
            ) : (
              <>
                <UserPlus size={16} />
                Create Company Workspace
              </>
            )}
          </button>
        </form>

        <div style={{ marginTop: '1.75rem', paddingTop: '1.25rem', borderTop: '1px solid var(--border-light)', textAlign: 'center', fontSize: '0.86rem', color: 'var(--text-muted)' }}>
          Already registered?{' '}
          <button
            type="button"
            onClick={() => onNavigate('login')}
            style={{ background: 'none', border: 'none', color: 'var(--accent-primary)', fontWeight: 600, cursor: 'pointer', padding: 0 }}
          >
            Sign In
          </button>
        </div>
      </div>
    </div>
  );
}
