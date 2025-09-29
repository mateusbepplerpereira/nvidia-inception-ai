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

export const jobsService = {
  async getJobs(isActive = null) {
    const params = isActive !== null ? { is_active: isActive } : {};
    const response = await api.get('/jobs', { params });
    return response.data;
  },

  async getJob(id) {
    const response = await api.get(`/jobs/${id}`);
    return response.data;
  },

  async createJob(data) {
    const response = await api.post('/jobs', data);
    return response.data;
  },

  async updateJob(id, data) {
    const response = await api.put(`/jobs/${id}`, data);
    return response.data;
  },

  async deleteJob(id) {
    const response = await api.delete(`/jobs/${id}`);
    return response.data;
  },

  async toggleJob(id) {
    const response = await api.post(`/jobs/${id}/toggle`);
    return response.data;
  },
};

export const notificationsService = {
  async getNotifications(limit = 50, offset = 0) {
    const response = await api.get('/notifications', {
      params: { limit, offset }
    });
    return response.data;
  },

  async getUnreadCount() {
    const response = await api.get('/notifications/unread-count');
    return response.data;
  },

  async markAsRead(id) {
    const response = await api.put(`/notifications/${id}/read`);
    return response.data;
  },

  async markAllAsRead() {
    const response = await api.put('/notifications/mark-all-read');
    return response.data;
  },

  async deleteNotification(id) {
    const response = await api.delete(`/notifications/${id}`);
    return response.data;
  },
};

export const logsService = {
  async getLogs(limit = 50, offset = 0, status = null, taskType = null) {
    const params = { limit, offset };
    if (status) params.status = status;
    if (taskType) params.task_type = taskType;

    const response = await api.get('/logs', { params });
    return response.data;
  },

  async getLogsStats() {
    const response = await api.get('/logs/stats');
    return response.data;
  },

  async getLog(id) {
    const response = await api.get(`/logs/${id}`);
    return response.data;
  },

  async deleteLog(id) {
    const response = await api.delete(`/logs/${id}`);
    return response.data;
  },

  async clearLogs(status = null, olderThanDays = null) {
    const params = {};
    if (status) params.status = status;
    if (olderThanDays) params.older_than_days = olderThanDays;

    const response = await api.delete('/logs', { params });
    return response.data;
  },
};

export const newsletterService = {
  async getEmails() {
    const response = await api.get('/newsletter/emails');
    return response.data;
  },

  async getActiveEmails() {
    const response = await api.get('/newsletter/emails/active');
    return response.data;
  },

  async addEmail(data) {
    const response = await api.post('/newsletter/emails', data);
    return response.data;
  },

  async updateEmail(id, data) {
    const response = await api.put(`/newsletter/emails/${id}`, data);
    return response.data;
  },

  async deleteEmail(id) {
    const response = await api.delete(`/newsletter/emails/${id}`);
    return response.data;
  },

  async toggleEmail(id) {
    const response = await api.post(`/newsletter/emails/${id}/toggle`);
    return response.data;
  }
};

export default api;