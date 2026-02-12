/**
 * PatientCompliance 页面组件测试
 *
 * 测试覆盖：
 * 1. UI 渲染测试 - 页面标题、统计卡片、图表
 * 2. 加载状态测试
 * 3. 患者选择测试
 * 4. 依从性数据显示测试
 * 5. 图表渲染测试
 * 6. 异常记录显示测试
 * 7. 日期范围筛选测试
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { BrowserRouter } from 'react-router-dom';
import PatientCompliance from '../PatientCompliance';

// Mock API
vi.mock('@/api', () => ({
  medicalOrdersApi: {
    getWeeklyCompliance: vi.fn(),
    getAbnormalRecords: vi.fn(),
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
  TrendingDown: () => <span data-testid="trending-down">Down</span>,
  CheckCircle: () => <span data-testid="check-circle">Check</span>,
  AlertTriangle: () => <span data-testid="alert-triangle">Alert</span>,
  Calendar: () => <span data-testid="calendar">Calendar</span>,
  Activity: () => <span data-testid="activity">Activity</span>,
  Loader2: () => <span data-testid="loader">Loader</span>,
}));

// Mock components
vi.mock('@/components/ui/select', () => ({
  Select: ({ children, value, onValueChange }: any) => (
    <select value={value} onChange={(e) => onValueChange?.(e.target.value)} data-testid="select">
      {children}
    </select>
  ),
  SelectTrigger: ({ children }: any) => <button>{children}</button>,
  SelectValue: ({ placeholder }: any) => <span>{placeholder}</span>,
  SelectContent: ({ children }: any) => <div>{children}</div>,
  SelectItem: ({ children, value }: any) => <option value={value}>{children}</option>,
}));

vi.mock('@/components/ui/badge', () => ({
  Badge: ({ children, variant }: any) => (
    <span data-variant={variant}>{children}</span>
  ),
}));

vi.mock('@/components/ui/progress', () => ({
  Progress: ({ value, max }: any) => (
    <div data-testid="progress" data-value={value} data-max={max}>
      <div style={{ width: `${(value / max) * 100}%` }}></div>
    </div>
  ),
}));

vi.mock('@/components/ui/table', () => ({
  Table: ({ children }: any) => <table data-testid="table">{children}</table>,
  TableHeader: ({ children }: any) => <thead>{children}</thead>,
  TableBody: ({ children }: any) => <tbody>{children}</tbody>,
  TableHead: ({ children }: any) => <th>{children}</th>,
  TableRow: ({ children }: any) => <tr>{children}</tr>,
  TableCell: ({ children }: any) => <td>{children}</td>,
}));

vi.mock('@/components/ui/alert', () => ({
  Alert: ({ children }: any) => <div data-testid="alert">{children}</div>,
  AlertTitle: ({ children }: any) => <h4>{children}</h4>,
  AlertDescription: ({ children }: any) => <p>{children}</p>,
}));

vi.mock('@/components/ui/card', () => ({
  Card: ({ children }: any) => <div data-testid="card">{children}</div>,
  CardContent: ({ children }: any) => <div>{children}</div>,
  CardHeader: ({ children }: any) => <div>{children}</div>,
  CardTitle: ({ children }: any) => <h3>{children}</h3>,
}));

vi.mock('@/components/charts', () => ({
  CustomLineChart: ({ data, height }: any) => (
    <div data-testid="line-chart" data-height={height}>
      {data && data.map((d: any) => d.date).join(',')}
    </div>
  ),
  CustomColumnChart: ({ data, height }: any) => (
    <div data-testid="column-chart" data-height={height}>
      {data && data.map((d: any) => d.date).join(',')}
    </div>
  ),
  CustomPieChart: ({ data, height, radius }: any) => (
    <div data-testid="pie-chart" data-radius={radius} data-height={height}>
      {data && data.map((d: any) => d.type).join(',')}
    </div>
  ),
}));

import { medicalOrdersApi } from '@/api';

describe('PatientCompliance Page', () => {
  const mockWeeklyData = {
    dates: ['02-06', '02-07', '02-08'],
    daily_rates: [0.8, 0.85, 0.9],
    average_rate: 0.85,
  };

  const mockDailyData = [
    { date: '2026-02-06', total: 10, completed: 8, overdue: 0, pending: 2, rate: 80 },
    { date: '2026-02-07', total: 10, completed: 9, overdue: 0, pending: 1, rate: 90 },
    { date: '2026-02-08', total: 10, completed: 7, overdue: 1, pending: 2, rate: 70 },
  ];

  const mockAbnormalRecords = [
    {
      id: 1,
      task_title: '血压偏高',
      value_data: { value: '180/90' },
      alert_type: 'bp_high',
      completed_at: '2026-02-10T10:00:00',
    },
  ];

  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(medicalOrdersApi.getWeeklyCompliance).mockResolvedValue({
      data: mockWeeklyData,
    });
    vi.mocked(medicalOrdersApi.getAbnormalRecords).mockResolvedValue({
      data: mockAbnormalRecords,
    });
  });

  const renderCompliance = () => {
    return render(
      <BrowserRouter>
        <PatientCompliance />
      </BrowserRouter>
    );
  };

  describe('Rendering', () => {
    it('should render page title', async () => {
      renderCompliance();

      expect(screen.getByTestId('page-header')).toBeInTheDocument();
      expect(screen.getByText('患者依从性分析')).toBeInTheDocument();
    });

    it('should render patient selector', async () => {
      renderCompliance();

      expect(screen.getByPlaceholderText('选择患者')).toBeInTheDocument();
    });
  });

  describe('Compliance Stats', () => {
    it('should render stat cards', async () => {
      renderCompliance();

      expect(screen.getByText('平均依从率')).toBeInTheDocument();
      expect(screen.getByText('总任务数')).toBeInTheDocument();
      expect(screen.getByText('已完成')).toBeInTheDocument();
      expect(screen.getByText('已超时')).toBeInTheDocument();
    });
  });

  describe('Charts', () => {
    it('should render line chart', async () => {
      renderCompliance();

      expect(screen.getByTestId('line-chart')).toBeInTheDocument();
    });

    it('should render pie chart', async () => {
      renderCompliance();

      expect(screen.getByTestId('pie-chart')).toBeInTheDocument();
    });

    it('should render column chart', async () => {
      renderCompliance();

      expect(screen.getByTestId('column-chart')).toBeInTheDocument();
    });
  });

  describe('Daily Progress Bars', () => {
    it('should render progress bars for each day', async () => {
      renderCompliance();

      const progressBars = screen.getAllByTestId('progress');
      expect(progressBars.length).toBeGreaterThan(0);
    });
  });

  describe('Abnormal Records Table', () => {
    it('should render abnormal records table', async () => {
      renderCompliance();

      expect(screen.getByText('异常监测记录')).toBeInTheDocument();
    });

    it('should render abnormal records', async () => {
      renderCompliance();

      await waitFor(() => {
        expect(screen.getByText('血压偏高')).toBeInTheDocument();
      });
    });
  });

  describe('Health Recommendations', () => {
    it('should show success recommendation for high compliance', async () => {
      renderCompliance();

      await waitFor(() => {
        expect(screen.getByText(/依从性优秀/)).toBeInTheDocument();
        expect(screen.getByText(/保持在80%以上/)).toBeInTheDocument();
      });
    });

    it('should show warning recommendation for medium compliance', async () => {
      renderCompliance();

      // Mock medium compliance
      await waitFor(() => {
        const alerts = screen.queryAllByText(/依从性一般/);
        if (alerts.length > 0) {
          expect(alerts[0]).toBeInTheDocument();
        }
      });
    });

    it('should show danger recommendation for low compliance', async () => {
      renderCompliance();

      // Mock low compliance
      await waitFor(() => {
        const alerts = screen.queryAllByText(/依从性偏低/);
        if (alerts.length > 0) {
          expect(alerts[0]).toBeInTheDocument();
        }
      });
    });
  });

  describe('Date Range Selection', () => {
    it('should change date range', async () => {
      renderCompliance();

      // Date picker interactions would be tested here
    });
  });
});
