import React, { useState, useEffect } from 'react';
import { api } from '../api';
import { Cpu, Zap, RefreshCw, AlertCircle, ArrowLeft } from 'lucide-react';

const DEFAULT_FORM = {
  product_category: 'Fashion',
  sub_category: 'Women',
  brand: 'Brand_10',
  product_identifier: 'SKU-FASH-100',
  product_price: 599.0,
  discount_percent: 25.0,
  product_rating: 4.2,
  review_count: 65,
  fragile_item: 0,
  warranty_available: 1,
  defect_rate: 0.03,
  seller_rating: 4.5,
  fulfillment_type: 'Marketplace Fulfilled',
  payment_method: 'Credit Card',
  quantity: 1,
  shipping_distance_km: 350.0,
  wishlist_before_purchase: 1,
  product_page_views: 15,
};

export default function Predict({ onResult, onNavigate }) {
  const [formData, setFormData] = useState(DEFAULT_FORM);
  const [taxonomy, setTaxonomy] = useState(null);
  const [presets, setPresets] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    async function init() {
      try {
        const [taxData, presetsData] = await Promise.all([
          api.getCategories(),
          api.getPresets(),
        ]);
        setTaxonomy(taxData);
        setPresets(presetsData);
      } catch (err) {
        console.warn('Could not load categories or presets', err);
      }
    }
    init();
  }, []);

  const handleChange = (e) => {
    const { name, value, type } = e.target;
    let parsedVal = value;
    if (type === 'number') {
      parsedVal = value === '' ? '' : parseFloat(value);
    } else if (name === 'fragile_item' || name === 'warranty_available' || name === 'wishlist_before_purchase') {
      parsedVal = parseInt(value, 10);
    }

    setFormData((prev) => {
      const next = { ...prev, [name]: parsedVal };
      // If category changed, update sub_category to first valid option
      if (name === 'product_category' && taxonomy?.categories?.[value]) {
        const validSubs = taxonomy.categories[value];
        if (!validSubs.includes(next.sub_category)) {
          next.sub_category = validSubs[0] || '';
        }
      }
      return next;
    });
  };

  const handleApplyPreset = (presetKey) => {
    if (!presets?.[presetKey]) return;
    setFormData((prev) => ({
      ...prev,
      ...presets[presetKey].data,
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      const result = await api.predict(formData);
      onResult(result);
    } catch (err) {
      setError(err.message || 'Prediction failed. Please verify your inputs.');
      setLoading(false);
    }
  };

  const availableCategories = taxonomy?.categories ? Object.keys(taxonomy.categories).sort() : ['Fashion', 'Electronics', 'Home', 'Beauty', 'Sports', 'Toys', 'Books'];
  const availableSubCategories = taxonomy?.categories?.[formData.product_category] || [formData.sub_category];
  const availableBrands = taxonomy?.brands || Array.from({ length: 30 }, (_, i) => `Brand_${i + 1}`);
  const availableFulfillments = taxonomy?.fulfillment_types || ['Marketplace Fulfilled', 'Seller Fulfilled'];
  const availablePayments = taxonomy?.payment_methods || ['COD', 'Credit Card', 'Debit Card', 'UPI', 'Wallet'];

  return (
    <div>
      <div style={{ marginBottom: '2rem' }}>
        <span className="badge badge-risk-low" style={{ marginBottom: '0.4rem' }}>Inference Engine</span>
        <h1 className="page-title">Order Return Risk Evaluation</h1>
        <p className="page-lead">
          Submit verified order, catalog, and logistics parameters to estimate customer return propensity prior to shipment.
        </p>
      </div>

      {/* Quick Test Presets Bar */}
      <div className="card" style={{ backgroundColor: 'var(--bg-subtle)', marginBottom: '1.75rem', padding: '1rem 1.25rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.86rem', fontWeight: 600, color: 'var(--text-primary)', marginBottom: '0.75rem' }}>
          <Zap size={15} color="var(--accent-primary)" />
          Quick Test Presets (Click to autofill validated scenarios)
        </div>
        <div style={{ display: 'flex', gap: '0.75rem', flexWrap: 'wrap' }}>
          <button
            type="button"
            className="btn-preset"
            onClick={() => handleApplyPreset('preset_1')}
          >
            <strong>Sample 1:</strong> Standard Verified Electronics (Lower Risk)
          </button>
          <button
            type="button"
            className="btn-preset"
            onClick={() => handleApplyPreset('preset_2')}
          >
            <strong>Sample 2:</strong> High-Discount Apparel with COD (Higher Risk)
          </button>
          <button
            type="button"
            className="btn-preset"
            onClick={() => handleApplyPreset('preset_3')}
          >
            <strong>Sample 3:</strong> Fragile Home Goods with Defect Alert (Higher Risk)
          </button>
        </div>
      </div>

      {error && (
        <div className="callout callout-danger" style={{ marginBottom: '1.5rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <AlertCircle size={16} />
          <span>{error}</span>
        </div>
      )}

      <form onSubmit={handleSubmit}>
        {/* Section 1: Product Information */}
        <fieldset className="form-fieldset">
          <legend className="fieldset-legend">1. Merchandise & Catalog Attributes</legend>
          <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: '1rem' }}>
            Core merchandise specifications recorded in catalog.
          </p>

          <div className="form-grid">
            <div className="form-group">
              <label className="form-label">Product SKU / Identifier (Optional)</label>
              <input
                type="text"
                name="product_identifier"
                className="form-control"
                value={formData.product_identifier || ''}
                onChange={handleChange}
                placeholder="e.g. SKU-FASH-100"
              />
              <span className="field-hint">Links prediction to company SKU history</span>
            </div>

            <div className="form-group">
              <label className="form-label">Product Category <span style={{ color: 'red' }}>*</span></label>
              <select
                name="product_category"
                className="form-control"
                value={formData.product_category}
                onChange={handleChange}
                required
              >
                {availableCategories.map((c) => (
                  <option key={c} value={c}>{c}</option>
                ))}
              </select>
            </div>

            <div className="form-group">
              <label className="form-label">Sub-Category <span style={{ color: 'red' }}>*</span></label>
              <select
                name="sub_category"
                className="form-control"
                value={formData.sub_category}
                onChange={handleChange}
                required
              >
                {availableSubCategories.map((s) => (
                  <option key={s} value={s}>{s}</option>
                ))}
              </select>
            </div>

            <div className="form-group">
              <label className="form-label">Brand Identifier <span style={{ color: 'red' }}>*</span></label>
              <select
                name="brand"
                className="form-control"
                value={formData.brand}
                onChange={handleChange}
                required
              >
                {availableBrands.map((b) => (
                  <option key={b} value={b}>{b}</option>
                ))}
              </select>
            </div>

            <div className="form-group">
              <label className="form-label">Fragile Item Status</label>
              <select
                name="fragile_item"
                className="form-control"
                value={formData.fragile_item}
                onChange={handleChange}
              >
                <option value={0}>No (Standard Handling)</option>
                <option value={1}>Yes (Fragile / Breakage-Prone)</option>
              </select>
            </div>

            <div className="form-group">
              <label className="form-label">Manufacturer Warranty</label>
              <select
                name="warranty_available"
                className="form-control"
                value={formData.warranty_available}
                onChange={handleChange}
              >
                <option value={1}>Yes (Warranty Included)</option>
                <option value={0}>No Warranty</option>
              </select>
            </div>
          </div>
        </fieldset>

        {/* Section 2: Pricing & Commercials */}
        <fieldset className="form-fieldset">
          <legend className="fieldset-legend">2. Pricing & Commercial Parameters</legend>
          <div className="form-grid">
            <div className="form-group">
              <label className="form-label">Product Unit Price ($) <span style={{ color: 'red' }}>*</span></label>
              <input
                type="number"
                step="0.01"
                min="0.01"
                name="product_price"
                className="form-control"
                value={formData.product_price}
                onChange={handleChange}
                required
              />
            </div>

            <div className="form-group">
              <label className="form-label">Promotional Discount (%)</label>
              <input
                type="number"
                step="0.1"
                min="0"
                max="100"
                name="discount_percent"
                className="form-control"
                value={formData.discount_percent}
                onChange={handleChange}
                required
              />
            </div>

            <div className="form-group">
              <label className="form-label">Order Quantity</label>
              <input
                type="number"
                min="1"
                max="100"
                name="quantity"
                className="form-control"
                value={formData.quantity}
                onChange={handleChange}
                required
              />
            </div>
          </div>
        </fieldset>

        {/* Section 3: Quality & Merchant */}
        <fieldset className="form-fieldset">
          <legend className="fieldset-legend">3. Quality & Merchant Metrics</legend>
          <div className="form-grid">
            <div className="form-group">
              <label className="form-label">Product Rating (1.0 - 5.0)</label>
              <input
                type="number"
                step="0.1"
                min="1.0"
                max="5.0"
                name="product_rating"
                className="form-control"
                value={formData.product_rating}
                onChange={handleChange}
                required
              />
            </div>

            <div className="form-group">
              <label className="form-label">Verified Review Count</label>
              <input
                type="number"
                min="0"
                name="review_count"
                className="form-control"
                value={formData.review_count}
                onChange={handleChange}
                required
              />
            </div>

            <div className="form-group">
              <label className="form-label">Manufacturer Defect Rate (0.00 - 1.00)</label>
              <input
                type="number"
                step="0.001"
                min="0.0"
                max="1.0"
                name="defect_rate"
                className="form-control"
                value={formData.defect_rate}
                onChange={handleChange}
                required
              />
            </div>

            <div className="form-group">
              <label className="form-label">Seller Quality Rating (1.0 - 5.0)</label>
              <input
                type="number"
                step="0.1"
                min="1.0"
                max="5.0"
                name="seller_rating"
                className="form-control"
                value={formData.seller_rating}
                onChange={handleChange}
                required
              />
            </div>
          </div>
        </fieldset>

        {/* Section 4: Logistics & Buyer Context */}
        <fieldset className="form-fieldset">
          <legend className="fieldset-legend">4. Logistics & Buyer Pre-Commitment</legend>
          <div className="form-grid">
            <div className="form-group">
              <label className="form-label">Fulfillment Channel</label>
              <select
                name="fulfillment_type"
                className="form-control"
                value={formData.fulfillment_type}
                onChange={handleChange}
              >
                {availableFulfillments.map((f) => (
                  <option key={f} value={f}>{f}</option>
                ))}
              </select>
            </div>

            <div className="form-group">
              <label className="form-label">Payment Method</label>
              <select
                name="payment_method"
                className="form-control"
                value={formData.payment_method}
                onChange={handleChange}
              >
                {availablePayments.map((p) => (
                  <option key={p} value={p}>{p}</option>
                ))}
              </select>
            </div>

            <div className="form-group">
              <label className="form-label">Shipping Distance (km)</label>
              <input
                type="number"
                step="1"
                min="1"
                max="15000"
                name="shipping_distance_km"
                className="form-control"
                value={formData.shipping_distance_km}
                onChange={handleChange}
                required
              />
            </div>

            <div className="form-group">
              <label className="form-label">Wishlist Pre-Commitment</label>
              <select
                name="wishlist_before_purchase"
                className="form-control"
                value={formData.wishlist_before_purchase}
                onChange={handleChange}
              >
                <option value={1}>Yes (Saved to wishlist prior to ordering)</option>
                <option value={0}>No Pre-Save</option>
              </select>
            </div>

            <div className="form-group">
              <label className="form-label">Product Page Views</label>
              <input
                type="number"
                min="1"
                max="10000"
                name="product_page_views"
                className="form-control"
                value={formData.product_page_views}
                onChange={handleChange}
                required
              />
            </div>
          </div>
        </fieldset>

        <div style={{ display: 'flex', gap: '0.85rem', alignItems: 'center', marginTop: '1.75rem' }}>
          <button
            type="submit"
            className="btn btn-primary btn-lg"
            disabled={loading}
          >
            {loading ? (
              <>
                <RefreshCw size={16} className="animate-spin" />
                Running Inference Pipeline...
              </>
            ) : (
              <>
                <Cpu size={16} />
                Assess Return Risk
              </>
            )}
          </button>
          <button
            type="button"
            className="btn btn-secondary"
            onClick={() => onNavigate('dashboard')}
          >
            Cancel
          </button>
        </div>
      </form>
    </div>
  );
}
