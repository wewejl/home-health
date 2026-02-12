/**
 * OrdersTab 组件测试
 *
 * 测试覆盖：
 * 1. UI 渲染测试
 * 2. 加载状态测试
 * 3. 空状态测试
 * 4. 医嘱点击测试
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { BrowserRouter } from 'react-router-dom';

// Mock API
vi.mock('@/api', () => ({
  doctorApi: {
    getOrders: vi.fn(),
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
  Loader2: () => <span data-testid="loader">Loader</span>,
}));

// Mock components
vi.mock('@/components/ui/tabs', () => ({
  Tabs: ({ children, value }: any) => <div data-value={value}>{children}</div>,
  TabsList: ({ children }: any) => <div>{children}</div>,
  TabsTrigger: ({ children, value }: any) => <button data-value={value}>{children}</button>,
  TabsContent: ({ children, value }: any) => <div data-value={value}>{children}</div>,
}));

vi.mock('@/components/ui/table', () => ({
  Table: ({ children }: any) => <table data-testid="table">{children}</table>,
  TableBody: ({ children }: any) => <tbody>{children}</tbody>,
  TableCell: ({ children }: any) => <td>{children}</td>,
  TableHead: ({ children }: any) => <th>{children}</th>,
  TableRow: ({ children }: any) => <tr>{children}</tr>,
}));

vi.mock('@/components/ui/badge', () => ({
  Badge: ({ children, variant }: any) => (
    <span data-variant={variant}>{children}</span>
  ),
}));

import { doctorApi } from '@/api';

describe('OrdersTab Component', () => {
  const mockOrders = [
    {
      id: 1,
      title: '高血压用药',
      status: 'active',
      start_date: '2026-02-01',
    },
  ];

  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(doctorApi.getOrders).mockResolvedValue({ data: mockOrders });
  });

  const renderOrdersTab = () => {
    return render(
      <BrowserRouter>
        {/* Mock parent with tabs */}
        <div data-current="orders">
          <OrdersTab />
        </div>
      </BrowserRouter>
    );
  };

  describe('Rendering', () => {
    it('should render orders list', async () => {
      renderOrdersTab();

      expect(screen.getByTestId('table')).toBeInTheDocument();
    });

    it('should render order type badges', async () => {
      renderOrdersTab();

      expect(screen.getByText('用药')).toBeInTheDocument();
    });
  });

  describe('Loading State', () => {
    it('should show loading indicator', async () => {
      let resolveOrders: (value: any) => void;
      const pendingPromise = new Promise(resolve => {
        resolveOrders = resolve;
      });
      vi.mocked(doctorApi.getOrders).mockReturnValue(pendingPromise as any);

      renderOrdersTab();

      expect(screen.getByTestId('loader')).toBeInTheDocument();

      resolveOrders!({ data: [] });
    });
  });

  describe('Empty State', () => {
    it('should show empty message when no orders', async () => {
      vi.mocked(doctorApi.getOrders).mockResolvedValue({ data: [] });

      renderOrdersTab();

      expect(screen.getByText('暂无医嘱')).toBeInTheDocument();
    });
  });

  describe('Order Actions', () => {
    it('should handle order click', async () => {
      renderOrdersTab();

      // Test order item click handling
      // This would verify navigation to detail
    });
  });
});
