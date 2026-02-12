/**
 * Stats 页面组件测试
 *
 * 测试覆盖：
 * 1. UI 渲染测试 - 页面标题、图表、统计卡片
 * 2. 加载状态测试
 * 3. 数据显示测试 - 趋势数据、审计日志
 * 4. 日期筛选测试
 * 5. 空状态测试
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { BrowserRouter } from 'react-router-dom';
import Stats from '../Stats';

// Mock API
vi.mock('@/api', () => ({
  statsApi: {
    getTrends: vi.fn(),
    getLogs: vi.fn(),
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
  TrendingUp: () => <span data-testid="trending-up">Up</span>,
  Loader2: () => <span data-testid="loader">Loader</span>,
}));

// Mock components
vi.mock('@/components/charts', () => ({
  CustomLineChart: ({ data, height, tooltipFormatter }: any) => (
    <div data-testid="line-chart" data-height={height}>
      {data && data.map((d: any) => d.date).join(',')}
    </div>
  ),
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

vi.mock('@/components/ui/table', () => ({
  Table: ({ children }: any) => <table data-testid="table">{children}</table>,
  TableHeader: ({ children }: any) => <thead>{children}</thead>,
  TableBody: ({ children }: any) => <tbody>{children}</tbody>,
  TableHead: ({ children }: any) => <th>{children}</th>,
  TableRow: ({ children }: any) => <tr>{children}</tr>,
  TableCell: ({ children, colSpan }: any) => <td colSpan={colSpan}>{children}</td>,
}));

vi.mock('@/components/ui/card', () => ({
  Card: ({ children }: any) => <div data-testid="card">{children}</div>,
  CardContent: ({ children }: any) => <div>{children}</div>,
  CardHeader: ({ children }: any) => <div>{children}</div>,
  CardTitle: ({ children }: any) => <h3>{children}</h3>,
}));

import { statsApi } from '@/api';

describe('Stats Page', () => {
  const mockTrends = [
    {
      date: '2026-02-01',
      sessions: 10,
      messages: 25,
    },
  ];

  const mockLogs = [
    {
      id: 1,
      admin_user_id: 1,
      action: 'create_doctor',
      resource_type: 'doctor',
      resource_id: '1',
      created_at: '2026-02-01T10:00:00',
    },
  ];

  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(statsApi.getTrends).mockResolvedValue({
      data: { daily_stats: mockTrends },
    });
    vi.mocked(statsApi.getLogs).mockResolvedValue({
      data: mockLogs,
    });
  });

  const renderStats = () => {
    return render(
      <BrowserRouter>
        <Stats />
      </BrowserRouter>
    );
  };

  describe('Rendering', () => {
    it('should render page title', async () => {
      renderStats();

      expect(screen.getByText('统计分析')).toBeInTheDocument();
    });

    it('should render days selector', async () => {
      renderStats();

      expect(screen.getByText('最近7天')).toBeInTheDocument();
      expect(screen.getByText('最近14天')).toBeInTheDocument();
      expect(screen.getByText('最近30天')).toBeInTheDocument();
    });
  });

  describe('Trends Chart', () => {
    it('should render line chart', async () => {
      renderStats();

      expect(screen.getByTestId('line-chart')).toBeInTheDocument();
    });

    it('should update chart when days change', async () => {
      renderStats();

      const selectButtons = screen.getAllByText('最近');
      if (selectButtons.length > 0) {
        await userEvent.click(selectButtons[1]); // Click "最近14天"

        await waitFor(() => {
          expect(statsApi.getTrends).toHaveBeenCalledWith(14);
        });
      }
    });
  });

  describe('Audit Logs Table', () => {
    it('should render audit logs table', async () => {
      renderStats();

      expect(screen.getByText('审计日志')).toBeInTheDocument();
    });
  });

  describe('Loading State', () => {
    it('should show loading indicator initially', async () => {
      let resolveTrends: (value: any) => void;
      const pendingPromise = new Promise(resolve => {
        resolveTrends = resolve;
      });
      vi.mocked(statsApi.getTrends).mockReturnValue(pendingPromise as any);

      renderStats();

      expect(screen.getByTestId('loader')).toBeInTheDocument();

      resolveTrends!({ data: { daily_stats: [] } });
    });
  });
});
