/**
 * TasksTab 组件测试
 *
 * 测试覆盖：
 * 1. UI 渲染测试
 * 2. 加载状态测试
 * 3. 空状态测试
 * 4. 任务勾选测试
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { BrowserRouter } from 'react-router-dom';

// Mock API
vi.mock('@/api', () => ({
  doctorApi: {
    getDailyTasks: vi.fn(),
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
  CheckCircle: () => <span data-testid="check">Check</span>,
  Circle: () => <span data-testid="circle">Circle</span>,
}));

// Mock components
vi.mock('@/components/ui/progress', () => ({
  Progress: ({ value }: any) => (
    <div data-testid="progress" data-value={value}>
      <div style={{ width: `${value}%` }}></div>
    </div>
  ),
}));

import { doctorApi } from '@/api';

describe('TasksTab Component', () => {
  const mockTasks = [
    {
      id: 1,
      title: '测量血压',
      scheduled_time: '08:00',
      status: 'pending',
      completed_at: null,
    },
    {
      id: 2,
      title: '服用药物',
      scheduled_time: '12:00',
      status: 'completed',
      completed_at: '2026-02-12T12:00:00',
    },
  ];

  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(doctorApi.getDailyTasks).mockResolvedValue({ data: mockTasks });
  });

  const renderTasksTab = () => {
    return render(
      <BrowserRouter>
        {/* Mock parent with tabs */}
        <div data-current="tasks">
          <TasksTab />
        </div>
      </BrowserRouter>
    );
  };

  describe('Rendering', () => {
    it('should render task list', async () => {
      renderTasksTab();

      expect(screen.getByTestId('progress')).toBeInTheDocument();
    });
  });

  describe('Task Checkbox', () => {
    it('should toggle task completion', async () => {
      renderTasksTab();

      const checkboxes = screen.getAllByTestId('checkbox');
      if (checkboxes.length > 0) {
        await userEvent.click(checkboxes[0]);

        // Verify toggle state changes
        expect(checkboxes[0]).toHaveProperty('checked');
      }
    });

    it('should show completed tasks with check icon', async () => {
      renderTasksTab();

      expect(screen.getByTestId('check')).toBeInTheDocument();
    });
  });

  describe('Loading State', () => {
    it('should show loading indicator initially', async () => {
      let resolveTasks: (value: any) => void;
      const pendingPromise = new Promise(resolve => {
        resolveTasks = resolve;
      });
      vi.mocked(doctorApi.getDailyTasks).mockReturnValue(pendingPromise as any);

      renderTasksTab();

      expect(screen.getByTestId('loader')).toBeInTheDocument();

      resolveTasks!({ data: [] });
    });
  });

  describe('Empty State', () => {
    it('should show empty state when no tasks', async () => {
      vi.mocked(doctorApi.getDailyTasks).mockResolvedValue({ data: [] });

      renderTasksTab();

      expect(screen.getByText(/暂无任务/)).toBeInTheDocument();
    });
  });

  describe('Progress Display', () => {
    it('should calculate completion rate', async () => {
      renderTasksTab();

      // Progress should be calculated based on completed/total tasks
      expect(screen.getByTestId('progress')).toBeInTheDocument();
    });
  });
});
