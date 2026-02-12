/**
 * Feedbacks 页面组件测试
 *
 * 测试覆盖：
 * 1. UI 渲染测试 - 页面标题、统计卡片、筛选器
 * 2. 加载状态测试
 * 3. 数据显示测试 - 反馈列表
 * 4. 空状态测试
 * 5. CRUD 操作测试 - 处理反馈
 * 6. 类型徽章测试
 * 7. 状态徽章测试
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { BrowserRouter } from 'react-router-dom';
import Feedbacks from '../Feedbacks';

// Mock API
vi.mock('@/api', () => ({
  feedbacksApi: {
    list: vi.fn(),
    getStats: vi.fn(),
    handle: vi.fn(),
  },
}));

// Mock toast
vi.mock('@/components/ui/toast', () => ({
  useToast: () => ({
    success: vi.fn(),
    error: vi.fn(),
  }),
}));

// Mock icons
vi.mock('lucide-react', () => ({
  ThumbsUp: () => <span data-testid="thumbs-up">Up</span>,
  ThumbsDown: () => <span data-testid="thumbs-down">Down</span>,
  AlertTriangle: () => <span data-testid="alert-triangle">Alert</span>,
  XOctagon: () => <span data-testid="x-octagon">X</span>,
  Loader2: () => <span data-testid="loader">Loader</span>,
}));

// Mock components
vi.mock('@/components/ui/table', () => ({
  Table: ({ children }: any) => <table data-testid="table">{children}</table>,
  TableHeader: ({ children }: any) => <thead>{children}</thead>,
  TableBody: ({ children }: any) => <tbody>{children}</tbody>,
  TableHead: ({ children }: any) => <th>{children}</th>,
  TableRow: ({ children }: any) => <tr>{children}</tr>,
  TableCell: ({ children, colSpan }: any) => <td colSpan={colSpan}>{children}</td>,
}));

vi.mock('@/components/ui/button', () => ({
  Button: ({ children, onClick }: any) => <button onClick={onClick}>{children}</button>,
}));

vi.mock('@/components/ui/badge', () => ({
  Badge: ({ children, variant }: any) => <span data-variant={variant}>{children}</span>,
}));

vi.mock('@/components/ui/card', () => ({
  Card: ({ children }: any) => <div data-testid="card">{children}</div>,
}));

vi.mock('@/components/ui/dialog', () => ({
  Dialog: ({ open, children }: any) => (open ? <div data-testid="dialog">{children}</div> : null),
  DialogContent: ({ children }: any) => <div>{children}</div>,
  DialogHeader: ({ children }: any) => <div>{children}</div>,
  DialogTitle: ({ children }: any) => <h2>{children}</h2>,
  DialogFooter: ({ children }: any) => <div>{children}</div>,
}));

vi.mock('@/components/ui/select', () => ({
  Select: ({ children, value, onValueChange }: any) => (
    <select value={value} onChange={(e) => onValueChange?.(e.target.value)}>
      {children}
    </select>
  ),
  SelectTrigger: ({ children }: any) => <button>{children}</button>,
  SelectValue: ({ placeholder }: any) => <span>{placeholder}</span>,
  SelectContent: ({ children }: any) => <div>{children}</div>,
  SelectItem: ({ children, value }: any) => <option value={value}>{children}</option>,
}));

vi.mock('@/components/ui/label', () => ({
  Label: ({ children, htmlFor }: any) => <label htmlFor={htmlFor}>{children}</label>,
}));

vi.mock('@/components/ui/textarea', () => ({
  Textarea: ({ value, onChange, placeholder, rows }: any) => (
    <textarea value={value} onChange={onChange} placeholder={placeholder} rows={rows} />
  ),
}));

import { feedbacksApi } from '@/api';

describe('Feedbacks Page', () => {
  const mockFeedbacks = [
    {
      id: 1,
      session_id: 'session-123',
      message_id: 456,
      user_id: 1,
      rating: 5,
      feedback_type: 'helpful',
      feedback_text: '非常有帮助',
      status: 'pending',
      created_at: '2026-02-12T10:00:00',
    },
    {
      id: 2,
      session_id: 'session-456',
      rating: 2,
      feedback_type: 'unhelpful',
      feedback_text: '不太清楚',
      status: 'reviewed',
      created_at: '2026-02-11T10:00:00',
    },
    {
      id: 3,
      session_id: 'session-789',
      rating: 4,
      feedback_type: 'unsafe',
      feedback_text: '信息不准确',
      status: 'resolved',
      created_at: '2026-02-10T10:00:00',
    },
  ];

  const mockStats = {
    total: 100,
    by_status: { pending: 10, reviewed: 20, resolved: 70 },
    by_type: { helpful: 50, unhelpful: 25, unsafe: 15, inaccurate: 10 },
  };

  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(feedbacksApi.list).mockResolvedValue({ data: mockFeedbacks });
    vi.mocked(feedbacksApi.getStats).mockResolvedValue({ data: mockStats });
    vi.mocked(feedbacksApi.handle).mockResolvedValue({ success: true });
  });

  const renderFeedbacks = () => {
    return render(
      <BrowserRouter>
        <Feedbacks />
      </BrowserRouter>
    );
  };

  describe('Rendering', () => {
    it('should render page title', async () => {
      renderFeedbacks();

      expect(screen.getByText('反馈管理')).toBeInTheDocument();
    });

    it('should render stats cards', async () => {
      renderFeedbacks();

      expect(screen.getByText('总反馈')).toBeInTheDocument();
      expect(screen.getByText('待处理')).toBeInTheDocument();
      expect(screen.getByText('有帮助')).toBeInTheDocument();
      expect(screen.getByText('无帮助')).toBeInTheDocument();
      expect(screen.getByText('不安全')).toBeInTheDocument();
      expect(screen.getByText('不准确')).toBeInTheDocument();
    });

    it('should render filter', async () => {
      renderFeedbacks();

      expect(screen.getByText('状态筛选:')).toBeInTheDocument();
    });
  });

  describe('Stats Display', () => {
    it('should display stats values', async () => {
      renderFeedbacks();

      expect(screen.getByText('100')).toBeInTheDocument();
      expect(screen.getByText('10')).toBeInTheDocument();
      expect(screen.getByText('70')).toBeInTheDocument();
      expect(screen.getByText('50')).toBeInTheDocument();
      expect(screen.getByText('25')).toBeInTheDocument();
      expect(screen.getByText('15')).toBeInTheDocument();
      expect(screen.getByText('10')).toBeInTheDocument();
    });
  });

  describe('Filter Functionality', () => {
    it('should filter by status', async () => {
      renderFeedbacks();

      const select = screen.getByPlaceholderText('全部状态') || screen.getAllByText('全部状态')[0];
      await userEvent.selectOptions(select, 'pending');

      await waitFor(() => {
        expect(feedbacksApi.list).toHaveBeenCalledWith(expect.objectContaining({
          status: 'pending',
        }));
      });
    });

    it('should filter by "all" status', async () => {
      renderFeedbacks();

      const select = screen.getByPlaceholderText('全部状态') || screen.getAllByText('全部状态')[0];
      await userEvent.selectOptions(select, 'all');

      await waitFor(() => {
        expect(feedbacksApi.list).toHaveBeenCalledWith(expect.objectContaining({
          status: undefined,
        }));
      });
    });
  });

  describe('Feedback List', () => {
    it('should render feedback list', async () => {
      renderFeedbacks();

      // Check table headers
      expect(screen.getByText('ID')).toBeInTheDocument();
      expect(screen.getByText('会话ID')).toBeInTheDocument();
      expect(screen.getByText('评分')).toBeInTheDocument();
      expect(screen.getByText('类型')).toBeInTheDocument();
      expect(screen.getByText('状态')).toBeInTheDocument();
    });

    it('should render feedback type badges', async () => {
      renderFeedbacks();

      expect(screen.getByText('有帮助')).toBeInTheDocument();
      expect(screen.getByText('无帮助')).toBeInTheDocument();
      expect(screen.getByText('不安全')).toBeInTheDocument();
      expect(screen.getByText('不准确')).toBeInTheDocument();
    });
  });

  describe('Handle Feedback', () => {
    it('should open handle dialog', async () => {
      renderFeedbacks();

      const handleButtons = screen.getAllByText('处理');
      if (handleButtons.length > 0) {
        await userEvent.click(handleButtons[0]);

        await waitFor(() => {
          expect(screen.getByTestId('dialog')).toBeInTheDocument();
          expect(screen.getByText('处理反馈')).toBeInTheDocument();
        });
      }
    });

    it('should show feedback details in dialog', async () => {
      renderFeedbacks();

      const handleButtons = screen.getAllByText('处理');
      if (handleButtons.length > 0) {
        await userEvent.click(handleButtons[0]);

        await waitFor(() => {
          expect(screen.getByText(/反馈内容/)).toBeInTheDocument();
          expect(screen.getByText('非常有帮助')).toBeInTheDocument();
        });
      }
    });

    it('should submit handle with status', async () => {
      renderFeedbacks();

      const handleButtons = screen.getAllByText('处理');
      if (handleButtons.length > 0) {
        await userEvent.click(handleButtons[0]);

        const submitButton = screen.getByText('提交');
        await userEvent.click(submitButton);

        await waitFor(() => {
          expect(feedbacksApi.handle).toHaveBeenCalled();
        });
      }
    });
  });

  describe('Empty State', () => {
    it('should render empty state', async () => {
      vi.mocked(feedbacksApi.list).mockResolvedValue({ data: [] });

      renderFeedbacks();

      await waitFor(() => {
        expect(screen.getByText('暂无数据')).toBeInTheDocument();
      });
    });
  });

  describe('Loading State', () => {
    it('should show loading indicator', async () => {
      let resolveList: (value: any) => void;
      const pendingPromise = new Promise(resolve => {
        resolveList = resolve;
      });
      vi.mocked(feedbacksApi.list).mockReturnValue(pendingPromise as any);

      renderFeedbacks();

      expect(screen.getByTestId('loader')).toBeInTheDocument();

      resolveList!({ data: [] });
    });
  });
});
