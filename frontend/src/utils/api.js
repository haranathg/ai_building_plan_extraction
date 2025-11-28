import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Auth API
export const login = async (username, password) => {
  const response = await api.post('/api/auth/login', { username, password });
  return response.data;
};

export const validateAccessKey = async (accessKey) => {
  const response = await api.post('/api/auth/validate-key', { access_key: accessKey });
  return response.data;
};

export const isAuthenticated = () => {
  return localStorage.getItem('authenticated') === 'true';
};

export const logout = () => {
  localStorage.removeItem('authenticated');
  localStorage.removeItem('accessLevel');
  localStorage.removeItem('authExpiry');
};

// Pre-check API
export const createPreCheck = async () => {
  const response = await api.post('/api/precheck/create');
  return response.data;
};

export const saveBasicInfo = async (precheckId, data) => {
  const response = await api.post(`/api/precheck/${precheckId}/basic-info`, data);
  return response.data;
};

export const uploadFiles = async (precheckId, files) => {
  const formData = new FormData();

  Object.keys(files).forEach(key => {
    if (files[key]) {
      formData.append(key, files[key]);
    }
  });

  const response = await api.post(`/api/precheck/${precheckId}/upload`, formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
  return response.data;
};

export const processPreCheck = async (precheckId) => {
  const response = await api.post(`/api/precheck/${precheckId}/process`);
  return response.data;
};

export const getPreCheckStatus = async (precheckId) => {
  const response = await api.get(`/api/precheck/${precheckId}/status`);
  return response.data;
};

export const getPreCheckData = async (precheckId) => {
  const response = await api.get(`/api/precheck/${precheckId}`);
  return response.data;
};

export const getReportData = async (precheckId, fileType) => {
  const response = await api.get(`/api/precheck/${precheckId}/report/${fileType}`);
  return response.data;
};

export const downloadReport = (precheckId, fileType) => {
  window.open(`${API_BASE_URL}/api/precheck/${precheckId}/download/${fileType}`, '_blank');
};

export default api;
