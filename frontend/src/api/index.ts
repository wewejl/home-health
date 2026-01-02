import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// 请求拦截器
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('admin_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// 响应拦截器
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('admin_token');
      localStorage.removeItem('admin_user');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// Auth API
export const authApi = {
  login: (username: string, password: string) =>
    api.post('/admin/auth/login', { username, password }),
  getMe: () => api.get('/admin/auth/me'),
  logout: () => api.post('/admin/auth/logout'),
};

// Stats API
export const statsApi = {
  getOverview: () => api.get('/admin/stats/overview'),
  getTrends: (days: number = 30) => api.get(`/admin/stats/trends?days=${days}`),
  getDoctorStats: (id: number) => api.get(`/admin/stats/doctors/${id}`),
  getDepartmentStats: (id: number) => api.get(`/admin/stats/departments/${id}`),
  getLogs: (params?: any) => api.get('/admin/stats/logs', { params }),
};

// Departments API
export const departmentsApi = {
  list: () => api.get('/admin/departments'),
  get: (id: number) => api.get(`/admin/departments/${id}`),
  create: (data: any) => api.post('/admin/departments', data),
  update: (id: number, data: any) => api.put(`/admin/departments/${id}`, data),
  delete: (id: number) => api.delete(`/admin/departments/${id}`),
};

// Doctors API
export const doctorsApi = {
  list: (params?: any) => api.get('/admin/doctors', { params }),
  get: (id: number) => api.get(`/admin/doctors/${id}`),
  create: (data: any) => api.post('/admin/doctors', data),
  update: (id: number, data: any) => api.put(`/admin/doctors/${id}`, data),
  delete: (id: number) => api.delete(`/admin/doctors/${id}`),
  activate: (id: number, isActive: boolean) =>
    api.put(`/admin/doctors/${id}/activate?is_active=${isActive}`),
  test: (id: number, message: string) =>
    api.post(`/admin/doctors/${id}/test?message=${encodeURIComponent(message)}`),
};

// Knowledge Bases API
export const knowledgeBasesApi = {
  list: (params?: any) => api.get('/admin/knowledge-bases', { params }),
  get: (id: string) => api.get(`/admin/knowledge-bases/${id}`),
  create: (data: any) => api.post('/admin/knowledge-bases', data),
  update: (id: string, data: any) => api.put(`/admin/knowledge-bases/${id}`, data),
  delete: (id: string) => api.delete(`/admin/knowledge-bases/${id}`),
  reindex: (id: string) => api.post(`/admin/knowledge-bases/${id}/reindex`),
  listDocuments: (kbId: string, params?: any) =>
    api.get(`/admin/knowledge-bases/${kbId}/documents`, { params }),
  createDocument: (kbId: string, data: any) =>
    api.post(`/admin/knowledge-bases/${kbId}/documents`, data),
};

// Documents API
export const documentsApi = {
  get: (id: number) => api.get(`/admin/documents/${id}`),
  update: (id: number, data: any) => api.put(`/admin/documents/${id}`, data),
  delete: (id: number) => api.delete(`/admin/documents/${id}`),
  approve: (id: number, data: { approved: boolean; review_notes?: string }) =>
    api.post(`/admin/documents/${id}/approve`, data),
};

// Feedbacks API
export const feedbacksApi = {
  list: (params?: any) => api.get('/admin/feedbacks', { params }),
  get: (id: number) => api.get(`/admin/feedbacks/${id}`),
  handle: (id: number, data: { status: string; resolution_notes?: string }) =>
    api.put(`/admin/feedbacks/${id}/handle`, data),
  getStats: () => api.get('/admin/feedbacks/stats/summary'),
};

// Diseases API
export const diseasesApi = {
  list: (params?: any) => api.get('/admin/diseases', { params }),
  get: (id: number) => api.get(`/admin/diseases/${id}`),
  create: (data: any) => api.post('/admin/diseases', data),
  update: (id: number, data: any) => api.put(`/admin/diseases/${id}`, data),
  delete: (id: number) => api.delete(`/admin/diseases/${id}`),
  toggleHot: (id: number, isHot: boolean) =>
    api.put(`/admin/diseases/${id}/toggle-hot?is_hot=${isHot}`),
  toggleActive: (id: number, isActive: boolean) =>
    api.put(`/admin/diseases/${id}/toggle-active?is_active=${isActive}`),
};

// Drug Categories API
export const drugCategoriesApi = {
  list: (includeInactive?: boolean) => 
    api.get('/admin/drug-categories', { params: { include_inactive: includeInactive } }),
  create: (data: any) => api.post('/admin/drug-categories', data),
  update: (id: number, data: any) => api.put(`/admin/drug-categories/${id}`, data),
  delete: (id: number) => api.delete(`/admin/drug-categories/${id}`),
};

// Drugs API
export const drugsApi = {
  list: (params?: any) => api.get('/admin/drugs', { params }),
  get: (id: number) => api.get(`/admin/drugs/${id}`),
  create: (data: any) => api.post('/admin/drugs', data),
  update: (id: number, data: any) => api.put(`/admin/drugs/${id}`, data),
  delete: (id: number) => api.delete(`/admin/drugs/${id}`),
  toggleHot: (id: number) => api.post(`/admin/drugs/${id}/toggle-hot`),
  toggleActive: (id: number) => api.post(`/admin/drugs/${id}/toggle-active`),
};

export default api;
