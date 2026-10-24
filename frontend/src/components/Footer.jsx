import React from 'react';

export default function Footer({ onNavigate }) {
  return (
    <footer className="site-footer">
      <div className="container footer-inner">
        <div>
          <p>
            <strong>Product Return Intelligence Platform</strong> &bull; Multi-Company e-commerce operations & logistics risk engine.
          </p>
          <p style={{ marginTop: '0.25rem', color: 'var(--text-muted)' }}>
            Validation-tuned decision threshold: <strong>0.3974</strong> &bull; Zero point-in-time data leakage.
          </p>
        </div>
        <div className="footer-links">
          <button className="nav-link" onClick={() => onNavigate('home')} style={{ padding: 0 }}>
            Home
          </button>
          <button className="nav-link" onClick={() => onNavigate('methodology')} style={{ padding: 0 }}>
            Methodology
          </button>
          <button className="nav-link" onClick={() => onNavigate('about')} style={{ padding: 0 }}>
            About
          </button>
          <a href="/docs" target="_blank" rel="noopener noreferrer">
            FastAPI Docs
          </a>
        </div>
      </div>
    </footer>
  );
}
