/**
 * Product Return Intelligence Platform - API Client
 * Centralized API service with automatic credentials handling for session cookies.
 */

const API_BASE = ''; // Proxied via Vite to http://127.0.0.1:8000

async function request(endpoint, options = {}) {
  const defaultHeaders = {
    'Accept': 'application/json',
  };

  if (!(options.body instanceof FormData) && options.body && typeof options.body === 'object') {
    defaultHeaders['Content-Type'] = 'application/json';
    options.body = JSON.stringify(options.body);
  }

  const response = await fetch(`${API_BASE}${endpoint}`, {
    ...options,
    headers: {
      ...defaultHeaders,
      ...options.headers,
    },
    credentials: 'include', // Transmit session cookies
  });

  if (response.status === 401 && !endpoint.includes('/auth/me')) {
    // Unauthenticated request
    const data = await response.json().catch(() => ({}));
    throw new Error(data.detail || 'Authentication required. Please sign in.');
  }

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    const message = errorData.detail || errorData.error || `Request failed with status ${response.status}`;
    throw new Error(message);
  }

  const contentType = response.headers.get('content-type');
  if (contentType && contentType.includes('application/json')) {
    return await response.json();
  }
  return await response.text();
}

export const api = {
  // Authentication
  getAuthMe: () => request('/api/auth/me'),
  login: (email, password) => request('/api/auth/login', { method: 'POST', body: { email, password } }),
  register: (data) => request('/api/auth/register', { method: 'POST', body: data }),
  logout: () => request('/api/auth/logout', { method: 'POST' }),

  // Taxonomy & Metadata
  getCategories: () => request('/api/categories'),
  getPresets: () => request('/api/presets'),
  getMetadata: () => request('/api/metadata'),
  getHealth: () => request('/health'),

  // Predictions
  predict: (payload) => request('/api/predict', { method: 'POST', body: payload }),
  getPredictions: (params = {}) => {
    const qs = new URLSearchParams(params).toString();
    return request(`/api/predictions${qs ? `?${qs}` : ''}`);
  },
  getPredictionDetail: (id) => request(`/api/predictions/${id}`),

  // Dashboard & Analytics
  getDashboard: () => request('/api/dashboard'),
  getAnalytics: (segment = 'product_category', minSamples = 5) =>
    request(`/api/analytics?segment=${encodeURIComponent(segment)}&min_samples=${minSamples}`),
  getPerformance: (windowDays = 30) => request(`/api/performance?window_days=${windowDays}`),

  // Recommendations
  getRecommendations: (statusFilter = 'all') =>
    request(`/api/recommendations?status_filter=${encodeURIComponent(statusFilter)}`),
  updateRecommendationStatus: (id, payload) =>
    request(`/api/recommendations/${id}/status`, { method: 'POST', body: payload }),

  // Ingestion
  uploadCSV: (file) => {
    const formData = new FormData();
    formData.append('file', file);
    return request('/api/import', { method: 'POST', body: formData });
  },
  downloadTemplateUrl: '/api/import/template',
  seedDemoData: () => request('/api/import/demo-seed', { method: 'POST' }),
};
