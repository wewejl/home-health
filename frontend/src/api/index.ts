import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

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
  // 病历分析
  analyzeRecords: (id: number, formData: FormData) => {
    const apiWithFormData = axios.create({
      baseURL: API_BASE_URL,
      timeout: 60000, // 病历分析可能需要更长时间
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    const token = localStorage.getItem('admin_token');
    if (token) {
      apiWithFormData.defaults.headers['Authorization'] = `Bearer ${token}`;
    }
    return apiWithFormData.post(`/admin/doctors/${id}/analyze-records`, formData);
  },
  saveAnalysisResult: (id: number, aiPersonaPrompt: string) =>
    api.post(`/admin/doctors/${id}/save-analysis`, new URLSearchParams({
      ai_persona_prompt: aiPersonaPrompt
    }), {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
    }),
  getAnalysisStatus: (id: number) => api.get(`/admin/doctors/${id}/analysis-status`),
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
  uploadDocument: (kbId: string, file: File, options?: { title?: string; doc_type?: string; source?: string }) => {
    const apiWithFormData = axios.create({
      baseURL: API_BASE_URL,
      timeout: 60000,
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    const token = localStorage.getItem('admin_token');
    if (token) {
      apiWithFormData.defaults.headers['Authorization'] = `Bearer ${token}`;
    }
    const formData = new FormData();
    formData.append('file', file);
    if (options?.title) formData.append('title', options.title);
    if (options?.doc_type) formData.append('doc_type', options.doc_type);
    if (options?.source) formData.append('source', options.source);
    return apiWithFormData.post(`/admin/knowledge-bases/${kbId}/documents/upload`, formData);
  },
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

// Persona Chat API (医生分身对话式采集)
export const personaChatApi = {
  start: (doctorId: number) => api.post(`/admin/doctors/${doctorId}/persona-chat/start`),
  sendMessage: (doctorId: number, message: string, state: string) =>
    api.post(`/admin/doctors/${doctorId}/persona-chat`, { message, state }),
  getStatus: (doctorId: number) => api.get(`/admin/doctors/${doctorId}/persona-status`),
  reset: (doctorId: number) => api.post(`/admin/doctors/${doctorId}/persona-chat/reset`),
};

// Dermatology Agent API
export const dermaAgentApi = {
  // 创建新会话
  createSession: (chiefComplaint?: string) =>
    api.post('/derma/start', {
      chief_complaint: chiefComplaint || ''
    }),

  // 发送消息（继续对话）
  sendMessage: (sessionId: string, message: string, history: any[] = []) =>
    api.post(`/derma/${sessionId}/continue`, {
      history: history,
      current_input: {
        message: message
      },
      task_type: 'conversation'
    }),

  // 创建新会话（SSE 流式）
  createSessionStream: (chiefComplaint?: string, callbacks?: {
    onMeta?: (data: any) => void;
    onChunk?: (text: string) => void;
    onStep?: (step: { type: string; content: string }) => void;
    onComplete?: (data: any) => void;
    onError?: (error: string) => void;
  }) => {
    const token = localStorage.getItem('admin_token');
    const eventSource = new EventSource(
      `${API_BASE_URL}/derma/start?chief_complaint=${encodeURIComponent(chiefComplaint || '')}`,
      {
        headers: token ? { 'Authorization': `Bearer ${token}` } : undefined,
      } as any
    );

    eventSource.addEventListener('meta', (e: MessageEvent) => {
      const data = JSON.parse(e.data);
      callbacks?.onMeta?.(data);
    });

    eventSource.addEventListener('chunk', (e: MessageEvent) => {
      const data = JSON.parse(e.data);
      callbacks?.onChunk?.(data.text);
    });

    eventSource.addEventListener('step', (e: MessageEvent) => {
      const data = JSON.parse(e.data);
      callbacks?.onStep?.(data);
    });

    eventSource.addEventListener('complete', (e: MessageEvent) => {
      const data = JSON.parse(e.data);
      callbacks?.onComplete?.(data);
      eventSource.close();
    });

    eventSource.addEventListener('error', (e: MessageEvent) => {
      if (e.data) {
        const data = JSON.parse(e.data);
        callbacks?.onError?.(data.error);
      }
      eventSource.close();
    });

    eventSource.onerror = () => {
      callbacks?.onError?.('连接错误');
      eventSource.close();
    };

    return eventSource;
  },

  // 发送消息（SSE 流式）
  sendMessageStream: (
    sessionId: string,
    message: string,
    history: any[] = [],
    callbacks?: {
      onMeta?: (data: any) => void;
      onChunk?: (text: string) => void;
      onStep?: (step: { type: string; content: string }) => void;
      onComplete?: (data: any) => void;
      onError?: (error: string) => void;
    }
  ) => {
    const token = localStorage.getItem('admin_token');

    console.log('[SSE] Starting stream request to:', `${API_BASE_URL}/derma/${sessionId}/continue`);

    fetch(`${API_BASE_URL}/derma/${sessionId}/continue`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'text/event-stream',
        ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
      },
      body: JSON.stringify({
        history: history,
        current_input: { message: message },
        task_type: 'conversation',
      }),
    }).then(async (response) => {
      console.log('[SSE] Response status:', response.status);
      console.log('[SSE] Response headers:', Object.fromEntries(response.headers.entries()));

      if (!response.ok) {
        const errorText = await response.text();
        console.error('[SSE] HTTP error response:', errorText);
        throw new Error(`HTTP error! status: ${response.status}, body: ${errorText}`);
      }

      const reader = response.body?.getReader();
      const decoder = new TextDecoder();

      if (!reader) {
        throw new Error('No reader available');
      }

      let buffer = '';
      let eventCount = 0;

      while (true) {
        const { done, value } = await reader.read();
        if (done) {
          console.log('[SSE] Stream ended, total events:', eventCount);
          break;
        }

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          if (!line.trim()) continue;

          console.log('[SSE] Raw line:', line);

          // 改进的解析逻辑
          const eventMatch = line.match(/event:\s*(.+)/);
          const dataMatch = line.match(/data:\s*(.+)/s);

          if (eventMatch && dataMatch) {
            const eventType = eventMatch[1].trim();
            const dataStr = dataMatch[1].trim();

            console.log('[SSE] Event type:', eventType);
            console.log('[SSE] Data string:', dataStr);

            try {
              const data = JSON.parse(dataStr);
              eventCount++;

              switch (eventType) {
                case 'meta':
                  console.log('[SSE] Meta event:', data);
                  callbacks?.onMeta?.(data);
                  break;
                case 'chunk':
                  console.log('[SSE] Chunk event:', data.text);
                  callbacks?.onChunk?.(data.text);
                  break;
                case 'step':
                  console.log('[SSE] Step event:', data);
                  callbacks?.onStep?.(data);
                  break;
                case 'complete':
                  console.log('[SSE] Complete event:', data);
                  callbacks?.onComplete?.(data);
                  break;
                case 'error':
                  console.error('[SSE] Error event:', data.error);
                  callbacks?.onError?.(data.error);
                  break;
                default:
                  console.warn('[SSE] Unknown event type:', eventType);
              }
            } catch (parseError) {
              console.error('[SSE] JSON parse error:', parseError, 'Data:', dataStr);
            }
          } else {
            console.warn('[SSE] Failed to parse line:', line);
          }
        }
      }
    }).catch((error) => {
      console.error('[SSE] Fetch error:', error);
      callbacks?.onError?.(error.message);
    });
  },

  // 获取会话详情
  getSession: (sessionId: string) =>
    api.get(`/derma/${sessionId}`),
};

// Medical Orders API (医嘱执行监督)
export const medicalOrdersApi = {
  // 医嘱 CRUD
  list: (status?: string) =>
    api.get('/medical-orders', { params: { status } }),
  get: (id: number) => api.get(`/medical-orders/${id}`),
  create: (data: {
    order_type: string;
    title: string;
    description?: string;
    schedule_type: string;
    start_date: string;
    end_date?: string;
    frequency?: string;
    reminder_times?: string[];
    ai_generated?: boolean;
    ai_session_id?: string;
  }) => api.post('/medical-orders', data),
  update: (id: number, data: {
    title?: string;
    description?: string;
    end_date?: string;
    frequency?: string;
    reminder_times?: string[];
  }) => api.put(`/medical-orders/${id}`, data),
  activate: (id: number, confirm: boolean) =>
    api.post(`/medical-orders/${id}/activate`, { confirm }),

  // 任务查询
  getDailyTasks: (taskDate: string) =>
    api.get(`/medical-orders/tasks/${taskDate}`),
  getPendingTasks: (taskDate: string) =>
    api.get(`/medical-orders/tasks/${taskDate}/pending`),

  // 打卡操作
  completeTask: (taskId: number, data: {
    completion_type: string;
    value?: Record<string, any>;
    photo_url?: string;
    notes?: string;
  }) => api.post(`/medical-orders/tasks/${taskId}/complete`, data),

  // 依从性查询
  getDailyCompliance: (taskDate: string) =>
    api.get(`/medical-orders/compliance/daily`, { params: { task_date: taskDate } }),
  getWeeklyCompliance: () =>
    api.get('/medical-orders/compliance/weekly'),
  getOrderCompliance: (orderId: number) =>
    api.get(`/medical-orders/compliance/order/${orderId}`),
  getAbnormalRecords: (days: number = 30) =>
    api.get('/medical-orders/compliance/abnormal', { params: { days } }),

  // 家属关系
  createFamilyBond: (data: {
    patient_id: number;
    family_member_phone: string;
    relationship: string;
    notification_level: string;
  }) => api.post('/medical-orders/family-bonds', data),
  getFamilyBonds: () =>
    api.get('/medical-orders/family-bonds'),
  deleteFamilyBond: (bondId: number) =>
    api.delete(`/medical-orders/family-bonds/${bondId}`),
  getFamilyMemberTasks: (patientId: number, taskDate: string) =>
    api.get(`/medical-orders/family-bonds/${patientId}/tasks`, { params: { task_date: taskDate } }),

  // 预警管理
  getAlerts: (activeOnly: boolean = true, limit: number = 50) =>
    api.get('/medical-orders/alerts', { params: { active_only: activeOnly, limit } }),
  acknowledgeAlert: (alertId: number) =>
    api.post(`/medical-orders/alerts/${alertId}/acknowledge`),
  checkAlerts: () =>
    api.post('/medical-orders/alerts/check'),
};

export default api;
