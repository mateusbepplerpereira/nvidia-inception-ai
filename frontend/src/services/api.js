import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const startupService = {
  async getStartups(params = {}) {
    const response = await api.get('/startups', { params });
    return response.data;
  },

  async getStartup(id) {
    const response = await api.get(`/startups/${id}`);
    return response.data;
  },

  async createStartup(data) {
    const response = await api.post('/startups', data);
    return response.data;
  },

  async updateStartup(id, data) {
    const response = await api.put(`/startups/${id}`, data);
    return response.data;
  },

  async deleteStartup(id) {
    const response = await api.delete(`/startups/${id}`);
    return response.data;
  },
};

export const analysisService = {
  async getDashboard() {
    const response = await api.get('/analysis/dashboard');
    return response.data;
  },

  async getOpportunities() {
    const response = await api.get('/analysis/opportunities');
    return response.data;
  },
};

export const agentService = {
  async discoverStartups(params = {}) {
    const response = await api.post('/agents/discover', params);
    return response.data;
  },

  async getMetricsRanking() {
    const response = await api.get('/agents/metrics/ranking');
    return response.data;
  },
};

export const reportService = {
  async generateReport(filters) {
    const response = await api.post('/startups/report', filters, {
      responseType: 'blob'
    });
    return response.data;
  },
};

export default api;