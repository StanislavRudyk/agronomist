const BASE = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1' 
  ? 'http://localhost:8000/api' 
  : '/api';

async function request(path, opts = {}) {
  const token = localStorage.getItem('access_token');
  const res = await fetch(`${BASE}${path}`, {
    ...opts,
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...(opts.headers || {}),
    },
  });
  if (res.status === 401) {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    window.history.pushState({}, '', '/login');
    window.dispatchEvent(new PopStateEvent('popstate'));
    throw new Error('Сесія завершена. Увійдіть знову.');
  }
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Невідома помилка' }));
    throw new Error(Array.isArray(err.detail) ? err.detail.map(e => e.msg).join('; ') : (err.detail || 'Помилка сервера'));
  }
  const ct = res.headers.get('content-type') || '';
  if (ct.includes('application/json')) return res.json();
  return res.text();
}

export const api = {
  // ── AUTH ──
  profile: () => request('/profile'),

  // ── FIELDS ──
  getFields: () => request('/fields'),
  createField: (data) => request('/fields', { method: 'POST', body: JSON.stringify(data) }),

  // ── WEATHER ──
  getWeatherCurrent: (fieldId) => request(`/weather/current/${fieldId}`),
  getWeatherForecast: (fieldId) => request(`/weather/forecast/${fieldId}`),
  getAirQuality: (fieldId) => request(`/weather/air-quality/current/${fieldId}`),
  getFloodForecast: (fieldId) => request(`/weather/flood/${fieldId}`),

  // ── MACHINERY ──
  getMachinery: () => request('/machinery/'),
  createMachinery: (data) => request('/machinery/', { method: 'POST', body: JSON.stringify(data) }),
  createImplement: (data) => request('/machinery/implements/', { method: 'POST', body: JSON.stringify(data) }),
  logFuel: (data) => request('/machinery/fuel/', { method: 'POST', body: JSON.stringify(data) }),
  createWorkOrder: (data) => request('/machinery/work-orders/', { method: 'POST', body: JSON.stringify(data) }),
  getMaintenanceAlerts: () => request('/machinery/maintenance-alerts/'),

  // ── WAREHOUSE ──
  getWarehouses: () => request('/warehouse/'),
  createWarehouse: (data) => request('/warehouse/', { method: 'POST', body: JSON.stringify(data) }),
  addGrainLot: (data) => request('/warehouse/grain-lot/', { method: 'POST', body: JSON.stringify(data) }),
  addQuality: (data) => request('/warehouse/quality/', { method: 'POST', body: JSON.stringify(data) }),
  logStorageCondition: (data) => request('/warehouse/storage-condition/', { method: 'POST', body: JSON.stringify(data) }),
  getStorageAlerts: () => request('/warehouse/storage-alerts/'),

  // ── YIELD ──
  addSoilAnalysis: (fieldId, data) => request(`/fields/${fieldId}/soil-analysis`, { method: 'POST', body: JSON.stringify(data) }),
  getYieldForecast: (fieldId) => request(`/fields/${fieldId}/yield-forecast`),

  // ── REPORTS ──
  getAnnualReport: (year) => request(`/reports/annual/${year}`),
  getFieldHistory: (fieldId) => request(`/reports/field-history/${fieldId}`),
  exportWorkOrders: () => `${BASE}/reports/export/work-orders`,
  exportFuel: () => `${BASE}/reports/export/fuel`,
};
