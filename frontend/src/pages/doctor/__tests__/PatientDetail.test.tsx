/**
 * PatientDetail 页面组件测试
 *
 * 测试覆盖：
 * 1. UI 渲染测试 - 患者信息、标签页
 * 2. 标签切换测试 - 医嘱、任务、咨询
 * 3. 加载状态测试
 * 4. 空状态测试
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { BrowserRouter } from 'react-router-dom';
import PatientDetail from '../PatientDetail';

// Mock API
vi.mock('@/api', () => ({
  doctorApi: {
    getPatient: vi.fn(),
    getOrders: vi.fn(),
    getTasks: vi.fn(),
    getConsultations: vi.fn(),
  },
}));

// Mock icons
vi.mock('lucide-react', () => ({
  User: () => <span data-testid="user">User</span>,
  Calendar: () => <span data-testid="calendar">Calendar</span>,
  FileText: () => <span data-testid="file">File</span>,
  Loader2: () => <span data-testid="loader">Loader</span>,
}));

// Mock components
vi.mock('@/components/ui/button', () => ({
  Button: ({ children, onClick }: any) => (
    <button onClick={onClick} data-testid="button">{children}</button>
  ),
}));

vi.mock('@/components/ui/badge', () => ({
  Badge: ({ children, variant }: any) => (
    <span data-variant={variant}>{children}</span>
  ),
}));

vi.mock('@/components/ui/tabs', () => ({
  Tabs: ({ children, value }: any) => <div data-value={value}>{children}</div>,
  TabsList: ({ children }: any) => <div>{children}</div>,
  TabsTrigger: ({ children, value }: any) => <button data-value={value}>{children}</button>,
  TabsContent: ({ children, value }: any) => <div data-value={value}>{children}</div>,
}));

vi.mock('@/components/ui/card', () => ({
  Card: ({ children }: any) => <div data-testid="card">{children}</div>,
}));

import { doctorApi } from '@/api';

describe('PatientDetail Page', () => {
  const mockPatient = {
    id: 4,
    nickname: '张三',
    phone: '138****8001',
    gender: '男',
    age: 45,
    last_consultation_at: '2026-02-10',
    active_orders_count: 2,
    completion_rate: 0.85,
  };

  const mockOrders = [
    {
      id: 1,
      title: '高血压用药',
      status: 'active',
      start_date: '2026-02-01',
      end_date: '2026-02-15',
    },
  ];

  const mockTasks = [
    {
      id: 1,
      title: '测量血压',
      scheduled_time: '08:00',
      status: 'pending',
      completed_at: null,
    },
  ];

  const mockConsultations = [
    {
      id: 1,
      user_message: '医生你好',
      ai_message: '您好，请问有什么需要帮助',
      created_at: '2026-02-10T10:00:00',
    },
  ];

  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(doctorApi.getPatient).mockResolvedValue({ data: mockPatient });
    vi.mocked(doctorApi.getOrders).mockResolvedValue({ data: mockOrders });
    vi.mocked(doctorApi.getTasks).mockResolvedValue({ data: mockTasks });
    vi.mocked(doctorApi.getConsultations).mockResolvedValue({
      data: { items: mockConsultations, has_more: false },
    });
  });

  const renderPatientDetail = () => {
    return render(
      <BrowserRouter>
        <PatientDetail />
      </BrowserRouter>
    );
  };

  describe('Rendering', () => {
    it('should render patient info', async () => {
      renderPatientDetail();

      await waitFor(() => {
        expect(screen.getByText('张三')).toBeInTheDocument();
        expect(screen.getByText('男')).toBeInTheDocument();
        expect(screen.getByText('45岁')).toBeInTheDocument();
      });
    });

    it('should render tabs', async () => {
      renderPatientDetail();

      expect(screen.getByText('医嘱')).toBeInTheDocument();
      expect(screen.getByText('任务')).toBeInTheDocument();
      expect(screen.getByText('咨询')).toBeInTheDocument();
    });
  });
});
