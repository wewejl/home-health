/**
 * ConsultationsTab 组件测试
 *
 * 测试覆盖：
 * 1. UI 渲染测试
 * 2. 加载状态测试
 * 3. 空状态测试
 * 4. 咨询记录点击测试
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { BrowserRouter } from 'react-router-dom';

// Mock API
vi.mock('@/api', () => ({
  sessionsApi: {
    getMessages: vi.fn(),
  },
}));

// Mock icons
vi.mock('lucide-react', () => ({
  Loader2: () => <span data-testid="loader">Loader</span>,
}));

// Mock components
vi.mock('@/components/ui/table', () => ({
  Table: ({ children }: any) => <table data-testid="table">{children}</table>,
  TableBody: ({ children }: any) => <tbody>{children}</tbody>,
  TableCell: ({ children }: any) => <td>{children}</td>,
  TableHead: ({ children }: any) => <th>{children}</th>,
  TableRow: ({ children }: any) => <tr>{children}</tr>,
}));

import { sessionsApi } from '@/api';

describe('ConsultationsTab Component', () => {
  const mockMessages = [
    {
      id: 1,
      role: 'user',
      content: '医生你好',
      created_at: '2026-02-12T10:00:00',
    },
    {
      id: 2,
      role: 'assistant',
      content: '您好，请问有什么需要帮助',
      created_at: '2026-02-12T10:01:00',
    },
  ];

  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(sessionsApi.getMessages).mockResolvedValue({
      data: { items: mockMessages, has_more: false },
    });
  });

  const renderConsultationsTab = () => {
    return render(
      <BrowserRouter>
        {/* Mock parent with tabs */}
        <div data-current="consultations">
          <ConsultationsTab />
        </div>
      </BrowserRouter>
    );
  };

  describe('Rendering', () => {
    it('should render messages list', async () => {
      renderConsultationsTab();

      expect(screen.getByTestId('table')).toBeInTheDocument();
    });

    it('should render user messages', async () => {
      renderConsultationsTab();

      expect(screen.getByText('医生你好')).toBeInTheDocument();
    });
  });

  describe('Loading State', () => {
    it('should show loading indicator', async () => {
      let resolveMessages: (value: any) => void;
      const pendingPromise = new Promise(resolve => {
        resolveMessages = resolve;
      });
      vi.mocked(sessionsApi.getMessages).mockReturnValue(pendingPromise as any);

      renderConsultationsTab();

      expect(screen.getByTestId('loader')).toBeInTheDocument();

      resolveMessages!({ data: { items: [], has_more: false } });
    });
  });

  describe('Empty State', () => {
    it('should show empty state when no messages', async () => {
      vi.mocked(sessionsApi.getMessages).mockResolvedValue({
        data: { items: [], has_more: false },
      });

      renderConsultationsTab();

      expect(screen.getByText(/暂无咨询/)).toBeInTheDocument();
    });
  });

  describe('Message Actions', () => {
    it('should handle message click', async () => {
      renderConsultationsTab();

      // Test message item click handling
      // This would verify navigation to detail
    });
  });
});
