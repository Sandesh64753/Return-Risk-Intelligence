import React from 'react';
import { ShieldCheck, Sliders, CheckCircle2, AlertTriangle, Cpu, Database } from 'lucide-react';

export default function Methodology({ onNavigate }) {
  return (
    <div style={{ maxWidth: '880px', margin: '0 auto' }}>
      <div style={{ marginBottom: '2.5rem' }}>
        <span className="badge badge-risk-low" style={{ marginBottom: '0.4rem' }}>Technical Governance</span>
        <h1 className="page-title">Statistical & Machine Learning Methodology</h1>
        <p className="page-lead">
          Technical specifications covering point-in-time feature constraints, decision threshold calibration, and multi-tenant data governance.
        </p>
      </div>

      {/* Principle 1: Point-in-Time Integrity */}
      <div className="card" style={{ marginBottom: '2rem' }}>
        <div className="card-header">
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <ShieldCheck size={20} color="var(--accent-primary)" />
            <h2 className="card-title">1. Pre-Shipment Point-in-Time Data Integrity</h2>
          </div>
          <span className="badge badge-risk-low">Zero Leakage</span>
        </div>

        <p style={{ fontSize: '0.92rem', color: 'var(--text-secondary)', lineHeight: 1.6, marginBottom: '1rem' }}>
          A machine learning model intended for pre-dispatch intervention is fundamentally flawed if it depends on data generated after an order has shipped. In retail logistics, post-purchase signals (such as delivery tracking delays, customer support chat tickets, or refund requests) cannot exist when the warehouse is packing an order.
        </p>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '1rem', marginBottom: '1.25rem' }}>
          <div style={{ backgroundColor: 'var(--risk-low-bg)', border: '1px solid var(--risk-low-border)', padding: '1rem', borderRadius: 'var(--radius-sm)' }}>
            <div style={{ fontWeight: 700, color: 'var(--risk-low-text)', fontSize: '0.86rem', marginBottom: '0.5rem', display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
              <CheckCircle2 size={15} /> 17 Validated Pre-Shipment Features
            </div>
            <ul style={{ margin: '0 0 0 1.25rem', fontSize: '0.8rem', color: 'var(--risk-low-text)', lineHeight: 1.5 }}>
              <li>Merchandise: Category, Sub-Category, Brand, Fragile, Warranty</li>
              <li>Pricing: Product Price, Promotional Discount %, Quantity</li>
              <li>Merchant Quality: Defect Rate, Seller Rating, Product Rating, Review Count</li>
              <li>Logistics & Buyer: Fulfillment Channel, Payment Method, Distance (km), Wishlist Pre-Save, Page Views</li>
            </ul>
          </div>

          <div style={{ backgroundColor: 'var(--risk-high-bg)', border: '1px solid var(--risk-high-border)', padding: '1rem', borderRadius: 'var(--radius-sm)' }}>
            <div style={{ fontWeight: 700, color: 'var(--risk-high-text)', fontSize: '0.86rem', marginBottom: '0.5rem', display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
              <AlertTriangle size={15} /> Excluded Post-Purchase Features (Leakage)
            </div>
            <ul style={{ margin: '0 0 0 1.25rem', fontSize: '0.8rem', color: 'var(--risk-high-text)', lineHeight: 1.5 }}>
              <li>Transit & Carrier Delays (unknown until carrier completes transit)</li>
              <li>Customer Support Interactions (only logged post-delivery)</li>
              <li>Customer Return Reasons & Complaints (generated only when return is filed)</li>
              <li>Post-Delivery Satisfaction Ratings</li>
            </ul>
          </div>
        </div>
      </div>

      {/* Principle 2: Threshold Calibration */}
      <div className="card" style={{ marginBottom: '2rem' }}>
        <div className="card-header">
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <Sliders size={20} color="var(--accent-primary)" />
            <h2 className="card-title">2. Cost-Sensitive Threshold Calibration (0.3974)</h2>
          </div>
          <span className="badge badge-risk-low">Tuned Recall: ~90%</span>
        </div>

        <p style={{ fontSize: '0.92rem', color: 'var(--text-secondary)', lineHeight: 1.6, marginBottom: '1rem' }}>
          Conventional classification systems default to a naive 0.50 probability cutoff. However, in reverse logistics, the cost of a <strong>False Negative</strong> (failing to identify an order that will be returned, incurring double shipping and restocking costs) far exceeds the cost of a <strong>False Positive</strong> (applying low-cost preventive measures like an SMS verification or extra box padding to a non-returned order).
        </p>

        <div style={{ backgroundColor: 'var(--bg-subtle)', padding: '1rem 1.25rem', borderRadius: 'var(--radius-sm)', marginBottom: '1rem' }}>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '1rem', textAlign: 'center' }}>
            <div>
              <div style={{ fontSize: '0.74rem', textTransform: 'uppercase', color: 'var(--text-muted)' }}>Calibrated Threshold</div>
              <div style={{ fontSize: '1.5rem', fontWeight: 800, color: 'var(--accent-primary)', fontFamily: 'var(--font-mono)' }}>0.3974</div>
            </div>
            <div>
              <div style={{ fontSize: '0.74rem', textTransform: 'uppercase', color: 'var(--text-muted)' }}>Validation Target Recall</div>
              <div style={{ fontSize: '1.5rem', fontWeight: 800, color: 'var(--text-primary)' }}>&ge; 90.0%</div>
            </div>
            <div>
              <div style={{ fontSize: '0.74rem', textTransform: 'uppercase', color: 'var(--text-muted)' }}>Test Set ROC-AUC</div>
              <div style={{ fontSize: '1.5rem', fontWeight: 800, color: 'var(--text-primary)', fontFamily: 'var(--font-mono)' }}>0.8939</div>
            </div>
          </div>
        </div>

        <p style={{ fontSize: '0.86rem', color: 'var(--text-muted)', lineHeight: 1.5 }}>
          The underlying model is a regularized Scikit-Learn Logistic Regression pipeline with standard feature scaling and categorical one-hot encoding, serialized in <code>artifacts/product_return_prediction.joblib</code>.
        </p>
      </div>

      {/* Principle 3: Wilson Score Confidence Intervals */}
      <div className="card" style={{ marginBottom: '2rem' }}>
        <div className="card-header">
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <Database size={20} color="var(--accent-primary)" />
            <h2 className="card-title">3. Small-Sample Defense with Wilson Confidence Intervals</h2>
          </div>
          <span className="badge badge-neutral">Statistical Rigor</span>
        </div>

        <p style={{ fontSize: '0.92rem', color: 'var(--text-secondary)', lineHeight: 1.6, marginBottom: '1rem' }}>
          In e-commerce reporting, calculating return rates on small cohorts can lead to gross misinterpretations (e.g., 1 return out of 1 order reported as a "100% return rate"). This platform calculates <strong>Wilson Score 95% Confidence Intervals</strong> for every empirical segment proportion.
        </p>

        <p style={{ fontSize: '0.88rem', color: 'var(--text-secondary)', lineHeight: 1.5 }}>
          For an observed return proportion <em>p̂</em> across <em>n</em> orders with standard normal quantile <em>z = 1.96</em>, the Wilson score interval ensures that categories with low sample counts correctly report wider uncertainty bands rather than misleading definitive percentages.
        </p>
      </div>

      <div style={{ textAlign: 'center', marginTop: '2rem' }}>
        <button className="btn btn-primary" onClick={() => onNavigate('predict')}>
          <Cpu size={15} />
          Test Inference Pipeline
        </button>
      </div>
    </div>
  );
}
