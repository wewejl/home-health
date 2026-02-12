/**
 * Departments 页面组件测试
 *
 * 测试覆盖：
 * 1. UI 渲染测试 - 页面标题、表格、操作按钮
 * 2. 加载状态测试 - 加载中状态显示
 * 3. 数据显示测试 - 科室列表显示
 * 4. 空状态测试 - 无数据时的显示
 * 5. CRUD 操作测试 - 创建、编辑、删除
 * 6. 表单验证测试 - 必填字段验证
 * 7. 错误处理测试 - API 错误处理
 * 8. 用户交互测试 - 模态框打开/关闭
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { BrowserRouter } from 'react-router-dom';
import Departments from '../Departments';

// Mock API
vi.mock('@/api', () => ({
  departmentsApi: {
    list: vi.fn(),
    create: vi.fn(),
    update: vi.fn(),
    delete: vi.fn(),
  },
}));

// Mock toast hook
vi.mock('@/components/ui/toast', () => ({
  useToast: () => ({
    success: vi.fn(),
    error: vi.fn(),
  }),
}));

// Mock Lucide icons
vi.mock('lucide-react', () => ({
  Plus: () => <span data-testid="plus-icon">Plus</span>,
  Pencil: () => <span data-testid="pencil-icon">Pencil</span>,
  Trash2: () => <span data-testid="trash-icon">Trash</span>,
  Loader2: () => <span data-testid="loader-icon">Loader</span>,
}));

// Mock UI components
vi.mock('@/components/ui/button', () => ({
  Button: ({ children, onClick, disabled }: { children: React.ReactNode; onClick?: () => void; disabled?: boolean }) => (
    <button onClick={onClick} disabled={disabled} data-testid="button">
      {children}
    </button>
  ),
}));

vi.mock('@/components/ui/input', () => ({
  Input: ({ value, onChange, placeholder, className }: any) => (
    <input
      value={value}
      onChange={onChange}
      placeholder={placeholder}
      className={className}
      data-testid="input"
    />
  ),
}));

vi.mock('@/components/ui/textarea', () => ({
  Textarea: ({ value, onChange, placeholder, rows }: any) => (
    <textarea
      value={value}
      onChange={onChange}
      placeholder={placeholder}
      rows={rows}
      data-testid="textarea"
    />
  ),
}));

vi.mock('@/components/ui/label', () => ({
  Label: ({ children, htmlFor }: any) => (
    <label htmlFor={htmlFor} data-testid="label">
      {children}
    </label>
  ),
}));

vi.mock('@/components/ui/badge', () => ({
  Badge: ({ children, variant }: any) => (
    <span data-testid={`badge-${variant}`}>{children}</span>
  ),
}));

vi.mock('@/components/ui/checkbox', () => ({
  Checkbox: ({ checked, onChange }: any) => (
    <input type="checkbox" checked={checked} onChange={onChange} data-testid="checkbox" />
  ),
}));

vi.mock('@/components/ui/table', () => ({
  Table: ({ children }: any) => <table data-testid="table">{children}</table>,
  TableHeader: ({ children }: any) => <thead>{children}</thead>,
  TableBody: ({ children }: any) => <tbody>{children}</tbody>,
  TableHead: ({ children, className }: any) => <th className={className}>{children}</th>,
  TableRow: ({ children }: any) => <tr>{children}</tr>,
  TableCell: ({ children, className, colSpan }: any) => <td className={className} colSpan={colSpan}>{children}</td>,
}));

vi.mock('@/components/ui/dialog', () => ({
  Dialog: ({ open, onOpenChange, children }: any) =>
    open ? <div data-testid="dialog">{children}</div> : null,
  DialogContent: ({ children }: any) => <div>{children}</div>,
  DialogHeader: ({ children }: any) => <div>{children}</div>,
  DialogTitle: ({ children }: any) => <h2>{children}</h2>,
  DialogFooter: ({ children }: any) => <div>{children}</div>,
}));

import { departmentsApi } from '@/api';

describe('Departments Page', () => {
  const mockDepartments = [
    {
      id: 1,
      name: '内科',
      description: '内科相关诊疗',
      icon: 'stethoscope',
      sort_order: 1,
      is_active: true,
      doctor_count: 5,
    },
    {
      id: 2,
      name: '外科',
      description: '外科相关诊疗',
      icon: 'scissors',
      sort_order: 2,
      is_active: false,
      doctor_count: 0,
    },
  ];

  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(departmentsApi.list).mockResolvedValue({ data: mockDepartments });
    vi.mocked(departmentsApi.create).mockResolvedValue({ success: true });
    vi.mocked(departmentsApi.update).mockResolvedValue({ success: true });
    vi.mocked(departmentsApi.delete).mockResolvedValue({ success: true });
  });

  const renderDepartments = () => {
    return render(
      <BrowserRouter>
        <Departments />
      </BrowserRouter>
    );
  };

  describe('Loading State', () => {
    it('should show loading state initially', async () => {
      let resolveDepartments: (value: any) => void;
      const pendingPromise = new Promise(resolve => {
        resolveDepartments = resolve;
      });
      vi.mocked(departmentsApi.list).mockReturnValue(pendingPromise as any);

      renderDepartments();

      expect(screen.getByTestId('loader-icon')).toBeInTheDocument();
      expect(screen.getByText('加载中...')).toBeInTheDocument();

      resolveDepartments!({ data: [] });
    });
  });

  describe('UI Rendering', () => {
    it('should render page title "科室管理"', async () => {
      renderDepartments();

      await waitFor(() => {
        expect(screen.getByText('科室管理')).toBeInTheDocument();
      });
    });

    it('should render "新增科室" button', async () => {
      renderDepartments();

      await waitFor(() => {
        expect(screen.getByText('新增科室')).toBeInTheDocument();
        expect(screen.getByTestId('plus-icon')).toBeInTheDocument();
      });
    });

    it('should render table headers', async () => {
      renderDepartments();

      await waitFor(() => {
        expect(screen.getByText('ID')).toBeInTheDocument();
        expect(screen.getByText('名称')).toBeInTheDocument();
        expect(screen.getByText('描述')).toBeInTheDocument();
        expect(screen.getByText('图标')).toBeInTheDocument();
        expect(screen.getByText('排序')).toBeInTheDocument();
        expect(screen.getByText('状态')).toBeInTheDocument();
        expect(screen.getByText('医生数')).toBeInTheDocument();
        expect(screen.getByText('操作')).toBeInTheDocument();
      });
    });
  });

  describe('Department List Display', () => {
    it('should render department list', async () => {
      renderDepartments();

      await waitFor(() => {
        expect(screen.getByText('内科')).toBeInTheDocument();
        expect(screen.getByText('外科')).toBeInTheDocument();
      });
    });

    it('should render department descriptions', async () => {
      renderDepartments();

      await waitFor(() => {
        expect(screen.getByText('内科相关诊疗')).toBeInTheDocument();
        expect(screen.getByText('外科相关诊疗')).toBeInTheDocument();
      });
    });

    it('should render department icons', async () => {
      renderDepartments();

      await waitFor(() => {
        expect(screen.getByText('stethoscope')).toBeInTheDocument();
        expect(screen.getByText('scissors')).toBeInTheDocument();
      });
    });

    it('should render sort order', async () => {
      renderDepartments();

      await waitFor(() => {
        expect(screen.getByText('1')).toBeInTheDocument();
        expect(screen.getByText('2')).toBeInTheDocument();
      });
    });

    it('should render active status badges', async () => {
      renderDepartments();

      await waitFor(() => {
        const activeBadges = screen.getAllByText('启用');
        expect(activeBadges.length).toBeGreaterThan(0);
      });
    });

    it('should render inactive status badges', async () => {
      renderDepartments();

      await waitFor(() => {
        expect(screen.getByText('停用')).toBeInTheDocument();
      });
    });

    it('should render doctor count', async () => {
      renderDepartments();

      await waitFor(() => {
        expect(screen.getByText('5')).toBeInTheDocument();
        expect(screen.getByText('0')).toBeInTheDocument();
      });
    });

    it('should render edit and delete buttons', async () => {
      renderDepartments();

      await waitFor(() => {
        const editButtons = screen.getAllByTestId('pencil-icon');
        const deleteButtons = screen.getAllByTestId('trash-icon');
        expect(editButtons.length).toBe(2);
        expect(deleteButtons.length).toBe(2);
      });
    });

    it('should disable delete button when department has doctors', async () => {
      renderDepartments();

      await waitFor(() => {
        const deleteButtons = screen.getAllByTestId('trash-icon');
        const firstDeleteButton = deleteButtons[0]?.closest('button');
        expect(firstDeleteButton).toBeDisabled();
      });
    });
  });

  describe('Empty State', () => {
    it('should render empty state when no departments', async () => {
      vi.mocked(departmentsApi.list).mockResolvedValue({ data: [] });

      renderDepartments();

      await waitFor(() => {
        expect(screen.getByText('暂无数据')).toBeInTheDocument();
      });
    });
  });

  describe('Create Department', () => {
    it('should open create dialog when clicking "新增科室" button', async () => {
      renderDepartments();

      await waitFor(() => {
        expect(screen.getByText('新增科室')).toBeInTheDocument();
      });

      const createButton = screen.getByText('新增科室');
      await userEvent.click(createButton);

      await waitFor(() => {
        expect(screen.getByTestId('dialog')).toBeInTheDocument();
        expect(screen.getByText('新增科室')).toBeInTheDocument();
      });
    });

    it('should render form fields in create dialog', async () => {
      renderDepartments();

      const createButton = screen.getByText('新增科室');
      await userEvent.click(createButton);

      await waitFor(() => {
        expect(screen.getByText(/名称/)).toBeInTheDocument();
        expect(screen.getByText(/描述/)).toBeInTheDocument();
        expect(screen.getByText(/图标/)).toBeInTheDocument();
        expect(screen.getByText(/排序/)).toBeInTheDocument();
        expect(screen.getByText(/启用状态/)).toBeInTheDocument();
      });
    });

    it('should validate name field is required', async () => {
      renderDepartments();

      const createButton = screen.getByText('新增科室');
      await userEvent.click(createButton);

      await waitFor(() => {
        expect(screen.getByTestId('dialog')).toBeInTheDocument();
      });

      const submitButton = screen.getByText('创建');
      await userEvent.click(submitButton);

      await waitFor(() => {
        expect(screen.getByText('请输入科室名称')).toBeInTheDocument();
      });
    });

    it('should submit create form successfully', async () => {
      renderDepartments();

      const createButton = screen.getByText('新增科室');
      await userEvent.click(createButton);

      await waitFor(() => {
        expect(screen.getByTestId('dialog')).toBeInTheDocument();
      });

      const nameInput = screen.getAllByTestId('input')[0];
      await userEvent.type(nameInput, '儿科');

      const submitButton = screen.getByText('创建');
      await userEvent.click(submitButton);

      await waitFor(() => {
        expect(departmentsApi.create).toHaveBeenCalledWith({
          name: '儿科',
          description: '',
          icon: '',
          sort_order: 0,
          is_active: true,
        });
      });
    });
  });

  describe('Edit Department', () => {
    it('should open edit dialog when clicking edit button', async () => {
      renderDepartments();

      await waitFor(() => {
        expect(screen.getByText('内科')).toBeInTheDocument();
      });

      const editButtons = screen.getAllByTestId('pencil-icon');
      await userEvent.click(editButtons[0]);

      await waitFor(() => {
        expect(screen.getByTestId('dialog')).toBeInTheDocument();
        expect(screen.getByText('编辑科室')).toBeInTheDocument();
      });
    });

    it('should pre-fill form with department data', async () => {
      renderDepartments();

      await waitFor(() => {
        expect(screen.getByText('内科')).toBeInTheDocument();
      });

      const editButtons = screen.getAllByTestId('pencil-icon');
      await userEvent.click(editButtons[0]);

      await waitFor(() => {
        const inputs = screen.getAllByTestId('input');
        expect(inputs[0]).toHaveValue('内科');
        expect(inputs[1]).toHaveValue('stethoscope');
      });
    });

    it('should submit update form successfully', async () => {
      renderDepartments();

      await waitFor(() => {
        expect(screen.getByText('内科')).toBeInTheDocument();
      });

      const editButtons = screen.getAllByTestId('pencil-icon');
      await userEvent.click(editButtons[0]);

      await waitFor(() => {
        expect(screen.getByTestId('dialog')).toBeInTheDocument();
      });

      const nameInput = screen.getAllByTestId('input')[0];
      await userEvent.clear(nameInput);
      await userEvent.type(nameInput, '心血管内科');

      const submitButton = screen.getByText('更新');
      await userEvent.click(submitButton);

      await waitFor(() => {
        expect(departmentsApi.update).toHaveBeenCalledWith(1, expect.objectContaining({
          name: '心血管内科',
        }));
      });
    });
  });

  describe('Delete Department', () => {
    it('should show error when deleting department with doctors', async () => {
      renderDepartments();

      await waitFor(() => {
        expect(screen.getByText('内科')).toBeInTheDocument();
      });

      const deleteButtons = screen.getAllByTestId('trash-icon');
      const firstDeleteButton = deleteButtons[0];

      // Click should not call delete API
      await userEvent.click(firstDeleteButton);

      // Check that delete was not called (doctor_count > 0)
      expect(departmentsApi.delete).not.toHaveBeenCalled();
    });

    it('should delete department successfully when no doctors', async () => {
      renderDepartments();

      await waitFor(() => {
        expect(screen.getByText('外科')).toBeInTheDocument();
      });

      const deleteButtons = screen.getAllByTestId('trash-icon');
      const secondDeleteButton = deleteButtons[1];

      await userEvent.click(secondDeleteButton);

      await waitFor(() => {
        expect(departmentsApi.delete).toHaveBeenCalledWith(2);
      });
    });
  });

  describe('Form Interaction', () => {
    it('should clear error when user starts typing', async () => {
      renderDepartments();

      const createButton = screen.getByText('新增科室');
      await userEvent.click(createButton);

      await waitFor(() => {
        expect(screen.getByTestId('dialog')).toBeInTheDocument();
      });

      const submitButton = screen.getByText('创建');
      await userEvent.click(submitButton);

      await waitFor(() => {
        expect(screen.getByText('请输入科室名称')).toBeInTheDocument();
      });

      const nameInput = screen.getAllByTestId('input')[0];
      await userEvent.type(nameInput, 'a');

      await waitFor(() => {
        expect(screen.queryByText('请输入科室名称')).not.toBeInTheDocument();
      });
    });

    it('should close dialog when clicking cancel', async () => {
      renderDepartments();

      const createButton = screen.getByText('新增科室');
      await userEvent.click(createButton);

      await waitFor(() => {
        expect(screen.getByTestId('dialog')).toBeInTheDocument();
      });

      const cancelButton = screen.getByText('取消');
      await userEvent.click(cancelButton);

      await waitFor(() => {
        expect(screen.queryByTestId('dialog')).not.toBeInTheDocument();
      });
    });
  });

  describe('Error Handling', () => {
    it('should handle API error on list fetch', async () => {
      vi.mocked(departmentsApi.list).mockRejectedValue(new Error('API Error'));

      renderDepartments();

      await waitFor(() => {
        expect(screen.getByText('科室管理')).toBeInTheDocument();
      });
    });

    it('should handle API error on create', async () => {
      vi.mocked(departmentsApi.create).mockRejectedValue({
        response: { data: { detail: '创建失败' } },
      });

      renderDepartments();

      const createButton = screen.getByText('新增科室');
      await userEvent.click(createButton);

      await waitFor(() => {
        expect(screen.getByTestId('dialog')).toBeInTheDocument();
      });

      const nameInput = screen.getAllByTestId('input')[0];
      await userEvent.type(nameInput, '测试科室');

      const submitButton = screen.getByText('创建');
      await userEvent.click(submitButton);

      await waitFor(() => {
        expect(departmentsApi.create).toHaveBeenCalled();
      });
    });
  });

  describe('Data Fetching', () => {
    it('should call departmentsApi.list on mount', async () => {
      renderDepartments();

      await waitFor(() => {
        expect(departmentsApi.list).toHaveBeenCalledTimes(1);
      });
    });

    it('should refresh list after create', async () => {
      renderDepartments();

      await waitFor(() => {
        expect(departmentsApi.list).toHaveBeenCalledTimes(1);
      });

      const createButton = screen.getByText('新增科室');
      await userEvent.click(createButton);

      await waitFor(() => {
        expect(screen.getByTestId('dialog')).toBeInTheDocument();
      });

      const nameInput = screen.getAllByTestId('input')[0];
      await userEvent.type(nameInput, '新科室');

      const submitButton = screen.getByText('创建');
      await userEvent.click(submitButton);

      await waitFor(() => {
        expect(departmentsApi.list).toHaveBeenCalledTimes(2);
      });
    });

    it('should refresh list after delete', async () => {
      renderDepartments();

      await waitFor(() => {
        expect(departmentsApi.list).toHaveBeenCalledTimes(1);
      });

      const deleteButtons = screen.getAllByTestId('trash-icon');
      await userEvent.click(deleteButtons[1]);

      await waitFor(() => {
        expect(departmentsApi.list).toHaveBeenCalledTimes(2);
      });
    });
  });
});
