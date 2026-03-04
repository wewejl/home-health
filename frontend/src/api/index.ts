import axios, { AxiosError, InternalAxiosRequestConfig } from 'axios';

// 修复: 默认端口从 8000 改为 8100
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8100';

// 读取测试模式配置（可通过环境变量 VITE_ADMIN_TEST_MODE 关闭）
const ADMIN_TEST_MODE = import.meta.env.VITE_ADMIN_TEST_MODE === 'true';

// 开发模式调试日志开关
const DEBUG_MODE = import.meta.env.MODE === 'development';

// 调试日志函数（仅在开发环境输出）
const debugLog = {
  log: (...args: unknown[]) => {
    if (DEBUG_MODE) console.log('[API]', ...args);
  },
  error: (...args: unknown[]) => {
    if (DEBUG_MODE) console.error('[API]', ...args);
  },
  warn: (...args: unknown[]) => {
    if (DEBUG_MODE) console.warn('[API]', ...args);
  },
};

// 创建 axios 实例
const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// 请求重试配置
const MAX_RETRY = 2;
const RETRY_DELAY = 1000;

// 重试延迟函数
const retryDelay = (retryCount: number) => {
  return new Promise((resolve) => setTimeout(resolve, RETRY_DELAY * retryCount));
};

// 判断是否应该重试
const shouldRetry = (error: AxiosError) => {
  const code = error.code || '';
  const isNetworkError = code === 'ECONNABORTED' || code === 'ETIMEDOUT' || !error.response;
  const isServerError = error.response?.status ? error.response.status >= 500 : false;
  const isRetryableStatus = error.response?.status === 429; // Too Many Requests
  return isNetworkError || isServerError || isRetryableStatus;
};

// 请求拦截器：添加认证头（仅在非测试模式下）
api.interceptors.request.use((config) => {
  // 测试模式下不添加认证头
  if (ADMIN_TEST_MODE) {
    return config;
  }

  // 生产模式：从 localStorage 获取 token 并添加到请求头
  const token = localStorage.getItem('admin_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
}, (error) => {
  return Promise.reject(error);
});

// 响应拦截器：处理 401 未授权和请求重试
api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const config = error.config as InternalAxiosRequestConfig & { _retry?: number; _retryCount?: number };

    // 测试模式下不处理 401 跳转
    if (ADMIN_TEST_MODE) {
      return Promise.reject(error);
    }

    // 生产模式：401 时清除本地存储并跳转登录
    if (error.response?.status === 401) {
      localStorage.removeItem('admin_token');
      localStorage.removeItem('admin_user');
      // 使用 window.location 而非 navigate 以确保跳转生效
      if (window.location.pathname !== '/login') {
        window.location.href = '/login';
      }
      return Promise.reject(error);
    }

    // 请求重试逻辑
    if (!config || !shouldRetry(error)) {
      return Promise.reject(error);
    }

    // 初始化重试计数
    config._retry = config._retry ?? 0;
    config._retryCount = config._retryCount ?? 0;

    // 检查是否超过最大重试次数
    if (config._retryCount >= MAX_RETRY) {
      return Promise.reject(error);
    }

    // 增加重试计数
    config._retryCount += 1;

    // 等待后重试
    await retryDelay(config._retryCount);

    return api(config);
  }
);

// 全局错误处理器
export const handleApiError = (error: unknown, context?: string): string => {
  if (axios.isAxiosError(error)) {
    const message = error.response?.data?.detail || error.message || '请求失败';
    return context ? `${context}: ${message}` : message;
  }
  if (error instanceof Error) {
    return error.message;
  }
  return '发生未知错误';
};

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

// Doctor Workstation API (医生工作台)
export const doctorApi = {
  // 医生信息
  getMe: () => api.get('/api/doctor/me'),

  // 患者管理
  getPatients: (search?: string) =>
    api.get('/api/doctor/patients', { params: search ? { search } : undefined }),
  getPatient: (patientId: number) => api.get(`/api/doctor/patients/${patientId}`),
  getPatientStats: () => api.get('/api/doctor/patient-stats'),

  // 患者分配管理
  getAssignablePatients: (search?: string, limit: number = 50) =>
    api.get('/api/doctor/patients/assignable', { params: { search, limit } }),
  assignPatient: (patientId: number, relationshipType: string = 'primary', notes?: string) =>
    api.post('/api/doctor/patients/assign', { patient_id: patientId, relationship_type: relationshipType, notes }),
  unassignPatient: (patientId: number) =>
    api.delete(`/api/doctor/patients/${patientId}/unassign`),

  // 医嘱管理
  getPatientOrders: (patientId: number) =>
    api.get(`/api/doctor/patients/${patientId}/orders`),
  deleteOrder: (orderId: number) =>
    api.delete(`/api/doctor/orders/${orderId}`),
  activateOrder: (orderId: number, confirm: boolean = true) =>
    api.post(`/api/doctor/orders/${orderId}/activate`, { confirm }),
  createOrder: (data: {
    patient_id: number;
    order_type: string;
    title: string;
    description?: string;
    schedule_type: string;
    start_date: string;
    end_date?: string;
    frequency?: string;
    reminder_times?: string[];
    weekdays?: number[];
    status?: string;
  }) => api.post('/api/doctor/orders', data),
  updateOrder: (orderId: number, data: {
    title?: string;
    description?: string;
    end_date?: string;
    frequency?: string;
    reminder_times?: string[];
    weekdays?: number[];
  }) => api.put(`/api/doctor/orders/${orderId}`, data),

  // 药品搜索
  searchDrugs: (q: string, limit: number = 20) =>
    api.get('/drugs/search', { params: { q, limit } }),

  // 医嘱模板
  getOrderTemplates: (orderType?: string) =>
    api.get('/api/doctor/orders/templates', { params: { order_type: orderType } }),
  createOrderTemplate: (data: {
    name: string;
    description?: string;
    order_type: string;
    template_data: any;
  }) => api.post('/api/doctor/orders/templates', data),
  deleteOrderTemplate: (templateId: number) =>
    api.delete(`/api/doctor/orders/templates/${templateId}`),

  // 医嘱复制
  copyOrder: (orderId: number, patientId?: number) =>
    api.post(`/api/doctor/orders/${orderId}/copy`, null, {
      params: patientId ? { patient_id: patientId } : undefined
    }),

  // 任务管理
  getPatientTasks: (patientId: number, taskDate: string) =>
    api.get(`/api/doctor/patients/${patientId}/tasks`, { params: { task_date: taskDate } }),

  // 会话管理
  getPatientConsultations: (patientId: number, limit: number = 20) =>
    api.get(`/api/doctor/patients/${patientId}/consultations`, { params: { limit } }),
  getConsultation: (sessionId: string) =>
    api.get(`/api/doctor/consultations/${sessionId}`),
};

// Doctors API (管理员端)
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
  // 使用 fetch API 而非 EventSource，因为 EventSource 不支持自定义请求头（如 Authorization）
  createSessionStream: (chiefComplaint?: string, callbacks?: {
    onMeta?: (data: any) => void;
    onChunk?: (text: string) => void;
    onStep?: (step: { type: string; content: string }) => void;
    onComplete?: (data: any) => void;
    onError?: (error: string) => void;
  }) => {
    const token = localStorage.getItem('admin_token');

    const url = new URL(`${API_BASE_URL}/derma/start`);
    if (chiefComplaint) {
      url.searchParams.append('chief_complaint', chiefComplaint);
    }

    fetch(url.toString(), {
      method: 'GET',
      headers: {
        'Accept': 'text/event-stream',
        ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
      },
    }).then(async (response) => {
      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`HTTP error! status: ${response.status}, body: ${errorText}`);
      }

      const reader = response.body?.getReader();
      const decoder = new TextDecoder();

      if (!reader) {
        throw new Error('No reader available');
      }

      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          if (!line.trim()) continue;

          const eventMatch = line.match(/event:\s*(.+)/);
          const dataMatch = line.match(/data:\s*(.+)/s);

          if (eventMatch && dataMatch) {
            const eventType = eventMatch[1].trim();
            const dataStr = dataMatch[1].trim();

            try {
              const data = JSON.parse(dataStr);

              switch (eventType) {
                case 'meta':
                  callbacks?.onMeta?.(data);
                  break;
                case 'chunk':
                  callbacks?.onChunk?.(data.text);
                  break;
                case 'step':
                  callbacks?.onStep?.(data);
                  break;
                case 'complete':
                  callbacks?.onComplete?.(data);
                  break;
                case 'error':
                  callbacks?.onError?.(data.error);
                  break;
              }
            } catch (parseError) {
              debugLog.error('[createSessionStream] JSON parse error:', parseError);
            }
          }
        }
      }
    }).catch((error) => {
      debugLog.error('[createSessionStream] Fetch error:', error);
      callbacks?.onError?.(error.message);
    });

    // 返回一个空对象（没有实际的关闭方法，因为 fetch 不像 EventSource）
    return { close: () => {} } as any;
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

    debugLog.log('[SSE] Starting stream request to:', `${API_BASE_URL}/derma/${sessionId}/continue`);

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
      debugLog.log('[SSE] Response status:', response.status);
      debugLog.log('[SSE] Response headers:', Object.fromEntries(response.headers.entries()));

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
          debugLog.log('[SSE] Stream ended, total events:', eventCount);
          break;
        }

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          if (!line.trim()) continue;

          debugLog.log('[SSE] Raw line:', line);

          // 改进的解析逻辑
          const eventMatch = line.match(/event:\s*(.+)/);
          const dataMatch = line.match(/data:\s*(.+)/s);

          if (eventMatch && dataMatch) {
            const eventType = eventMatch[1].trim();
            const dataStr = dataMatch[1].trim();

            debugLog.log('[SSE] Event type:', eventType);
            debugLog.log('[SSE] Data string:', dataStr);

            try {
              const data = JSON.parse(dataStr);
              eventCount++;

              switch (eventType) {
                case 'meta':
                  debugLog.log('[SSE] Meta event:', data);
                  callbacks?.onMeta?.(data);
                  break;
                case 'chunk':
                  debugLog.log('[SSE] Chunk event:', data.text);
                  callbacks?.onChunk?.(data.text);
                  break;
                case 'step':
                  debugLog.log('[SSE] Step event:', data);
                  callbacks?.onStep?.(data);
                  break;
                case 'complete':
                  debugLog.log('[SSE] Complete event:', data);
                  callbacks?.onComplete?.(data);
                  break;
                case 'error':
                  debugLog.error('[SSE] Error event:', data.error);
                  callbacks?.onError?.(data.error);
                  break;
                default:
                  debugLog.warn('[SSE] Unknown event type:', eventType);
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
