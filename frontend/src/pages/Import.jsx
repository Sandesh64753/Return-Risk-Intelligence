import React, { useState } from 'react';
import { api } from '../api';
import {
  UploadCloud,
  Download,
  Database,
  CheckCircle2,
  AlertCircle,
  FileText,
  RefreshCw,
  ArrowRight
} from 'lucide-react';

export default function Import({ onNavigate }) {
  const [file, setFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [uploadResult, setUploadResult] = useState(null);
  const [seeding, setSeeding] = useState(false);
  const [seedResult, setSeedResult] = useState(null);
  const [error, setError] = useState(null);

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
      setUploadResult(null);
      setError(null);
    }
  };

  const handleUpload = async (e) => {
    e.preventDefault();
    if (!file) {
      setError('Please select a valid CSV file to upload.');
      return;
    }

    setUploading(true);
    setError(null);
    setUploadResult(null);

    try {
      const res = await api.uploadCSV(file);
      setUploadResult(res);
    } catch (err) {
      setError(err.message || 'File upload failed. Ensure the CSV conforms to the template schema.');
    } finally {
      setUploading(false);
    }
  };

  const handleDemoSeed = async () => {
    setSeeding(true);
    setError(null);
    setSeedResult(null);

    try {
      const res = await api.seedDemoData();
      setSeedResult(res);
    } catch (err) {
      setError(err.message || 'Failed to seed sample order dataset.');
    } finally {
      setSeeding(false);
    }
  };

  return (
    <div>
      <div style={{ marginBottom: '1.75rem' }}>
        <span className="badge badge-risk-low" style={{ marginBottom: '0.4rem' }}>Data Ingestion</span>
        <h1 className="page-title">Historical Order Outcomes Ingestion</h1>
        <p className="page-lead">
          Ingest post-fulfillment order outcomes into your isolated company database to populate historical benchmarks, segment return rates, and automated action plans.
        </p>
      </div>

      {/* 1-Click Fast Seeder Card */}
      <div
        className="card"
        style={{
          backgroundColor: 'var(--accent-light)',
          border: '1px solid var(--accent-border)',
          marginBottom: '2rem',
          padding: '1.25rem 1.5rem',
        }}
      >
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.25rem' }}>
              <Database size={18} color="var(--accent-primary)" />
              <h2 style={{ fontSize: '1.05rem', fontWeight: 700, color: 'var(--accent-hover)' }}>
                Demo Environment: Load Verified Sample Dataset (1-Click)
              </h2>
            </div>
            <p style={{ fontSize: '0.86rem', color: 'var(--text-secondary)', maxWidth: '620px' }}>
              Instantly seed 150 realistic orders with verified return outcomes into your current company workspace to test analytics, Wilson confidence intervals, and recommendations without preparing a CSV file.
            </p>
          </div>
          <button
            className="btn btn-primary"
            onClick={handleDemoSeed}
            disabled={seeding}
            style={{ padding: '0.65rem 1.25rem', fontSize: '0.9rem' }}
          >
            {seeding ? (
              <>
                <RefreshCw size={15} className="animate-spin" />
                Seeding 150 Orders...
              </>
            ) : (
              <>
                <Database size={15} />
                Load 150 Sample Orders
              </>
            )}
          </button>
        </div>

        {seedResult && (
          <div style={{ marginTop: '1rem', paddingTop: '0.75rem', borderTop: '1px solid var(--accent-border)', fontSize: '0.84rem', color: 'var(--accent-hover)', display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '0.5rem' }}>
            <span>
              <strong>Success:</strong> {seedResult.message || `Loaded ${seedResult.inserted_count} sample records into your workspace.`}
            </span>
            <button
              className="btn btn-secondary btn-sm"
              onClick={() => onNavigate('dashboard')}
            >
              View Dashboard &rarr;
            </button>
          </div>
        )}
      </div>

      {error && (
        <div className="callout callout-danger" style={{ marginBottom: '1.5rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <AlertCircle size={16} />
          <span>{error}</span>
        </div>
      )}

      {/* CSV Upload Form Card */}
      <div className="card" style={{ marginBottom: '2rem' }}>
        <div className="card-header">
          <div>
            <h2 className="card-title">Upload Historical Orders CSV</h2>
            <p className="card-subtitle">File size limit: 10 MB &bull; UTF-8 or Latin-1 encoded</p>
          </div>
          <a
            href={api.downloadTemplateUrl}
            download
            className="btn btn-secondary btn-sm"
            style={{ display: 'inline-flex', alignItems: 'center', gap: '0.35rem' }}
          >
            <Download size={14} />
            Download Standard Template
          </a>
        </div>

        <form onSubmit={handleUpload}>
          <div
            style={{
              border: '2px dashed var(--border-medium)',
              borderRadius: 'var(--radius-md)',
              padding: '2.5rem 1.5rem',
              textAlign: 'center',
              backgroundColor: 'var(--bg-subtle)',
              marginBottom: '1.25rem',
              cursor: 'pointer',
            }}
            onClick={() => document.getElementById('csv-file-input').click()}
          >
            <UploadCloud size={36} color="var(--accent-primary)" style={{ marginBottom: '0.5rem' }} />
            <div style={{ fontSize: '0.95rem', fontWeight: 600, color: 'var(--text-primary)', marginBottom: '0.25rem' }}>
              {file ? file.name : 'Choose a CSV file or drag and drop here'}
            </div>
            <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>
              {file ? `${(file.size / 1024).toFixed(1)} KB` : 'Click to select .csv file from your computer'}
            </div>
            <input
              id="csv-file-input"
              type="file"
              accept=".csv,text/csv"
              style={{ display: 'none' }}
              onChange={handleFileChange}
            />
          </div>

          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem' }}>
            <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
              Order reference IDs are scoped to your company; duplicate references will be skipped safely.
            </span>
            <button
              type="submit"
              className="btn btn-primary"
              disabled={uploading || !file}
            >
              {uploading ? (
                <>
                  <RefreshCw size={15} className="animate-spin" />
                  Ingesting Records...
                </>
              ) : (
                <>
                  <UploadCloud size={15} />
                  Upload & Ingest CSV
                </>
              )}
            </button>
          </div>
        </form>

        {/* Upload Outcome Report */}
        {uploadResult && (
          <div
            style={{
              marginTop: '1.5rem',
              paddingTop: '1.25rem',
              borderTop: '1px solid var(--border-light)',
            }}
          >
            <h3 style={{ fontSize: '1rem', fontWeight: 700, marginBottom: '0.75rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <CheckCircle2 size={16} color="var(--risk-low-accent)" />
              Ingestion Results
            </h3>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))', gap: '1rem', marginBottom: '1rem' }}>
              <div style={{ backgroundColor: 'var(--bg-subtle)', padding: '0.75rem', borderRadius: 'var(--radius-xs)' }}>
                <div style={{ fontSize: '0.72rem', textTransform: 'uppercase', color: 'var(--text-muted)' }}>Inserted</div>
                <div style={{ fontSize: '1.35rem', fontWeight: 800, color: 'var(--risk-low-accent)' }}>
                  {uploadResult.inserted ?? uploadResult.inserted_count ?? 0}
                </div>
              </div>
              <div style={{ backgroundColor: 'var(--bg-subtle)', padding: '0.75rem', borderRadius: 'var(--radius-xs)' }}>
                <div style={{ fontSize: '0.72rem', textTransform: 'uppercase', color: 'var(--text-muted)' }}>Duplicates Skipped</div>
                <div style={{ fontSize: '1.35rem', fontWeight: 800, color: 'var(--text-secondary)' }}>
                  {uploadResult.duplicates ?? uploadResult.duplicate_count ?? 0}
                </div>
              </div>
              <div style={{ backgroundColor: 'var(--bg-subtle)', padding: '0.75rem', borderRadius: 'var(--radius-xs)' }}>
                <div style={{ fontSize: '0.72rem', textTransform: 'uppercase', color: 'var(--text-muted)' }}>Validation Errors</div>
                <div style={{ fontSize: '1.35rem', fontWeight: 800, color: (uploadResult.total_errors ?? uploadResult.error_count ?? 0) > 0 ? 'var(--risk-high-accent)' : 'var(--text-muted)' }}>
                  {uploadResult.total_errors ?? uploadResult.error_count ?? 0}
                </div>
              </div>
            </div>

            {uploadResult.errors?.length > 0 && (
              <div style={{ marginTop: '0.75rem', backgroundColor: 'var(--risk-high-bg)', border: '1px solid var(--risk-high-border)', padding: '0.75rem 1rem', borderRadius: 'var(--radius-xs)' }}>
                <strong style={{ fontSize: '0.8rem', color: 'var(--risk-high-text)' }}>Row Validation Issues (first {uploadResult.errors.length}):</strong>
                <ul style={{ margin: '0.35rem 0 0 1.25rem', fontSize: '0.78rem', color: 'var(--risk-high-text)' }}>
                  {uploadResult.errors.map((err, idx) => (
                    <li key={idx}>{err}</li>
                  ))}
                </ul>
              </div>
            )}

            <div style={{ marginTop: '1rem', display: 'flex', gap: '0.75rem' }}>
              <button className="btn btn-secondary btn-sm" onClick={() => onNavigate('dashboard')}>
                Go to Dashboard &rarr;
              </button>
              <button className="btn btn-secondary btn-sm" onClick={() => onNavigate('analytics')}>
                View Analytics &rarr;
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Schema Documentation Table */}
      <div className="card">
        <div className="card-header">
          <div>
            <h2 className="card-title">Expected CSV Column Specifications</h2>
            <p className="card-subtitle">Required headers and data formats</p>
          </div>
        </div>
        <div className="table-responsive">
          <table className="data-table">
            <thead>
              <tr>
                <th>Column Header</th>
                <th>Type</th>
                <th>Required</th>
                <th>Description / Example</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td><code>order_reference_id</code></td>
                <td>String</td>
                <td><strong>Yes</strong></td>
                <td>Unique order identifier (e.g. <code>ORD-2026-9001</code>)</td>
              </tr>
              <tr>
                <td><code>product_category</code></td>
                <td>String</td>
                <td><strong>Yes</strong></td>
                <td>Fashion, Electronics, Home, Beauty, Sports, etc.</td>
              </tr>
              <tr>
                <td><code>sub_category</code></td>
                <td>String</td>
                <td><strong>Yes</strong></td>
                <td>Category-specific sub-tier (e.g. Women, Men, Laptops)</td>
              </tr>
              <tr>
                <td><code>returned</code></td>
                <td>Integer</td>
                <td><strong>Yes</strong></td>
                <td><code>1</code> if returned, <code>0</code> if completed without return</td>
              </tr>
              <tr>
                <td><code>product_price</code></td>
                <td>Float</td>
                <td><strong>Yes</strong></td>
                <td>Unit price (e.g. <code>140.00</code>)</td>
              </tr>
              <tr>
                <td><code>discount_percent</code></td>
                <td>Float</td>
                <td>No</td>
                <td>Promotional discount percentage (0-100)</td>
              </tr>
              <tr>
                <td><code>defect_rate</code></td>
                <td>Float</td>
                <td>No</td>
                <td>Manufacturer defect rate (0.00 - 1.00)</td>
              </tr>
              <tr>
                <td><code>fulfillment_type</code></td>
                <td>String</td>
                <td>No</td>
                <td><code>Marketplace Fulfilled</code> or <code>Seller Fulfilled</code></td>
              </tr>
              <tr>
                <td><code>payment_method</code></td>
                <td>String</td>
                <td>No</td>
                <td><code>COD</code>, <code>Credit Card</code>, <code>UPI</code>, <code>Wallet</code>, <code>Debit Card</code></td>
              </tr>
              <tr>
                <td><code>purchase_date</code></td>
                <td>Date (YYYY-MM-DD)</td>
                <td>No</td>
                <td>Purchase date for period-over-period tracking</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
