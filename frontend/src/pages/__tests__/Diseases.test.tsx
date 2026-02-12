/**
 * Diseases 页面组件测试
 *
 * 测试覆盖：
 * 1. UI 渲染测试 - 页面标题、表格、筛选器
 * 2. 加载状态测试 - 骨架屏显示
 * 3. 数据显示测试 - 疾病列表显示
 * 4. 空状态测试 - 无数据时的显示
 * 5. CRUD 操作测试 - 创建、编辑、删除
 * 6. 筛选功能测试 - 科室、状态、搜索
 * 7. 热门/启用切换测试 - Switch 操作
 * 8. 表单验证测试 - 必填字段验证
 * 9. 标签页测试 - 基本信息、内容、作者信息
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { BrowserRouter } from 'react-router-dom';
import Diseases from '../Diseases';

// Mock API
vi.mock('@/api', () => ({
  diseasesApi: {
    list: vi.fn(),
    get: vi.fn(),
    create: vi.fn(),
    update: vi.fn(),
    delete: vi.fn(),
    toggleHot: vi.fn(),
    toggleActive: vi.fn(),
  },
  departmentsApi: {
    list: vi.fn(),
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
  Edit: () => <span data-testid="edit-icon">Edit</span>,
  Trash2: () => <span data-testid="trash-icon">Trash</span>,
  Flame: () => <span data-testid="flame-icon">Flame</span>,
  Search: () => <span data-testid="search-icon">Search</span>,
  Filter: () => <span data-testid="filter-icon">Filter</span>,
  Loader2: () => <span data-testid="loader-icon">Loader</span>,
}));

// Mock PageHeader
vi.mock('@/components/medical/page-header', () => ({
  PageHeader: ({ title, description }: any) => (
    <div data-testid="page-header">
      <h1>{title}</h1>
      <p>{description}</p>
    </div>
  ),
}));

// Mock LoadingSkeleton
vi.mock('@/components/medical/loading-skeleton', () => ({
  LoadingSkeleton: () => <div data-testid="loading-skeleton">Loading...</div>,
}));

// Mock other UI components
vi.mock('@/components/ui/select', () => ({
  Select: ({ children, onValueChange, value }: any) => (
    <div data-testid="select" data-value={value}>
      {children}
      <button onClick={() => onValueChange?.('1')}>Change</button>
    </div>
  ),
  SelectTrigger: ({ children }: any) => <span>{children}</span>,
  SelectValue: ({ placeholder }: any) => <span>{placeholder}</span>,
  SelectContent: ({ children }: any) => <div>{children}</div>,
  SelectItem: ({ children, value }: any) => (
    <div data-value={value} onClick={() => {}}>
      {children}
    </div>
  ),
}));

vi.mock('@/components/ui/switch', () => ({
  Switch: ({ checked, onCheckedChange }: any) => (
    <input
      type="checkbox"
      checked={checked}
      onChange={(e) => onCheckedChange?.(e.target.checked)}
      data-testid="switch"
    />
  ),
}));

vi.mock('@/components/ui/tabs', () => ({
  Tabs: ({ children, defaultValue }: any) => (
    <div data-testid="tabs" data-default-value={defaultValue}>
      {children}
    </div>
  ),
  TabsList: ({ children }: any) => <div data-testid="tabs-list">{children}</div>,
  TabsTrigger: ({ children, value }: any) => (
    <button data-value={value}>{children}</button>
  ),
  TabsContent: ({ children, value }: any) => (
    <div data-testid={`tabs-content-${value}`}>{children}</div>
  ),
}));

import { diseasesApi, departmentsApi } from '@/api';

describe('Diseases Page', () => {
  const mockDiseases = [
    {
      id: 1,
      name: '高血压',
      pinyin: 'gaoxueya',
      pinyin_abbr: 'gxy',
      aliases: '高血压病',
      department_id: 1,
      department_name: '内科',
      recommended_department: '心血管内科',
      overview: '血压升高的疾病',
      symptoms: '头晕、头痛',
      causes: '遗传、环境',
      diagnosis: '血压测量',
      treatment: '药物治疗',
      prevention: '低盐饮食',
      care: '定期测量血压',
      author_name: '张医生',
      author_title: '主治医师',
      author_avatar: '',
      reviewer_info: '三甲医生专业编审',
      is_hot: true,
      sort_order: 1,
      is_active: true,
      view_count: 100,
      created_at: '2026-01-01',
      updated_at: '2026-01-01',
    },
    {
      id: 2,
      name: '糖尿病',
      pinyin: 'tangniaobing',
      pinyin_abbr: 'tnb',
      aliases: '糖代谢病',
      department_id: 1,
      department_name: '内科',
      recommended_department: '内分泌科',
      overview: '血糖代谢异常',
      symptoms: '多饮、多尿',
      causes: '胰岛素分泌异常',
      diagnosis: '血糖检测',
      treatment: '胰岛素治疗',
      prevention: '控制饮食',
      care: '定期检查血糖',
      author_name: '李医生',
      author_title: '副主任医师',
      author_avatar: '',
      reviewer_info: '三甲医生专业编审',
      is_hot: false,
      sort_order: 2,
      is_active: true,
      view_count: 50,
      created_at: '2026-01-02',
      updated_at: '2026-01-02',
    },
  ];

  const mockDepartments = [
    { id: 1, name: '内科' },
    { id: 2, name: '外科' },
  ];

  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(diseasesApi.list).mockResolvedValue({ data: mockDiseases });
    vi.mocked(diseasesApi.get).mockResolvedValue({ data: mockDiseases[0] });
    vi.mocked(diseasesApi.create).mockResolvedValue({ success: true });
    vi.mocked(diseasesApi.update).mockResolvedValue({ success: true });
    vi.mocked(diseasesApi.delete).mockResolvedValue({ success: true });
    vi.mocked(diseasesApi.toggleHot).mockResolvedValue({ success: true });
    vi.mocked(diseasesApi.toggleActive).mockResolvedValue({ success: true });
    vi.mocked(departmentsApi.list).mockResolvedValue({ data: mockDepartments });
  });

  const renderDiseases = () => {
    return render(
      <BrowserRouter>
        <Diseases />
      </BrowserRouter>
    );
  };

  describe('Loading State', () => {
    it('should show loading skeleton initially', async () => {
      let resolveDiseases: (value: any) => void;
      const pendingPromise = new Promise(resolve => {
        resolveDiseases = resolve;
      });
      vi.mocked(diseasesApi.list).mockReturnValue(pendingPromise as any);

      renderDiseases();

      expect(screen.getByTestId('loading-skeleton')).toBeInTheDocument();

      resolveDiseases!({ data: [] });
    });
  });

  describe('UI Rendering', () => {
    it('should render page header', async () => {
      renderDiseases();

      await waitFor(() => {
        expect(screen.getByTestId('page-header')).toBeInTheDocument();
        expect(screen.getByText('疾病百科管理')).toBeInTheDocument();
        expect(screen.getByText('管理系统中的疾病信息，包括症状、病因、诊断、治疗等')).toBeInTheDocument();
      });
    });

    it('should render filter controls', async () => {
      renderDiseases();

      await waitFor(() => {
        expect(screen.getByText('选择科室')).toBeInTheDocument();
        expect(screen.getByText('状态')).toBeInTheDocument();
        expect(screen.getByPlaceholderText('搜索疾病名称')).toBeInTheDocument();
        expect(screen.getByText('新增疾病')).toBeInTheDocument();
      });
    });

    it('should render table headers', async () => {
      renderDiseases();

      await waitFor(() => {
        expect(screen.getByText('ID')).toBeInTheDocument();
        expect(screen.getByText('名称')).toBeInTheDocument();
        expect(screen.getByText('科室')).toBeInTheDocument();
        expect(screen.getByText('拼音')).toBeInTheDocument();
        expect(screen.getByText('别名')).toBeInTheDocument();
        expect(screen.getByText('浏览量')).toBeInTheDocument();
        expect(screen.getByText('热门')).toBeInTheDocument();
        expect(screen.getByText('状态')).toBeInTheDocument();
        expect(screen.getByText('操作')).toBeInTheDocument();
      });
    });
  });

  describe('Disease List Display', () => {
    it('should render disease list', async () => {
      renderDiseases();

      await waitFor(() => {
        expect(screen.getByText('高血压')).toBeInTheDocument();
        expect(screen.getByText('糖尿病')).toBeInTheDocument();
      });
    });

    it('should render hot icon for hot diseases', async () => {
      renderDiseases();

      await waitFor(() => {
        expect(screen.getByTestId('flame-icon')).toBeInTheDocument();
      });
    });

    it('should render department name', async () => {
      renderDiseases();

      await waitFor(() => {
        expect(screen.getByText('内科')).toBeInTheDocument();
      });
    });

    it('should render pinyin', async () => {
      renderDiseases();

      await waitFor(() => {
        expect(screen.getByText('gaoxueya')).toBeInTheDocument();
        expect(screen.getByText('tangniaobing')).toBeInTheDocument();
      });
    });

    it('should render aliases', async () => {
      renderDiseases();

      await waitFor(() => {
        expect(screen.getByText('高血压病')).toBeInTheDocument();
        expect(screen.getByText('糖代谢病')).toBeInTheDocument();
      });
    });

    it('should render view count badge', async () => {
      renderDiseases();

      await waitFor(() => {
        expect(screen.getByText('100')).toBeInTheDocument();
        expect(screen.getByText('50')).toBeInTheDocument();
      });
    });

    it('should render edit and delete buttons', async () => {
      renderDiseases();

      await waitFor(() => {
        const editButtons = screen.getAllByTestId('edit-icon');
        const deleteButtons = screen.getAllByTestId('trash-icon');
        expect(editButtons.length).toBe(2);
        expect(deleteButtons.length).toBe(2);
      });
    });
  });

  describe('Filter Functionality', () => {
    it('should filter by department', async () => {
      renderDiseases();

      await waitFor(() => {
        expect(screen.getByText('高血压')).toBeInTheDocument();
      });

      // Click on department filter select
      const selectButtons = screen.getAllByText('Change');
      await userEvent.click(selectButtons[0]);

      await waitFor(() => {
        expect(diseasesApi.list).toHaveBeenCalled();
      });
    });

    it('should filter by status', async () => {
      renderDiseases();

      await waitFor(() => {
        expect(screen.getByText('已启用')).toBeInTheDocument();
        expect(screen.getByText('已禁用')).toBeInTheDocument();
      });

      // Click on status filter
      const selectButtons = screen.getAllByText('Change');
      if (selectButtons.length > 1) {
        await userEvent.click(selectButtons[1]);
      }
    });

    it('should filter by search text', async () => {
      renderDiseases();

      await waitFor(() => {
        expect(screen.getByPlaceholderText('搜索疾病名称')).toBeInTheDocument();
      });

      const searchInput = screen.getByPlaceholderText('搜索疾病名称');
      await userEvent.type(searchInput, '高血压');

      await waitFor(() => {
        expect(diseasesApi.list).toHaveBeenCalledWith(expect.objectContaining({
          search: '高血压',
        }));
      });
    });
  });

  describe('Empty State', () => {
    it('should render empty state when no diseases', async () => {
      vi.mocked(diseasesApi.list).mockResolvedValue({ data: [] });

      renderDiseases();

      await waitFor(() => {
        expect(screen.getByText('暂无数据')).toBeInTheDocument();
        expect(screen.getByTestId('filter-icon')).toBeInTheDocument();
      });
    });
  });

  describe('Create Disease', () => {
    it('should open create dialog when clicking "新增疾病" button', async () => {
      renderDiseases();

      await waitFor(() => {
        expect(screen.getByText('新增疾病')).toBeInTheDocument();
      });

      const createButton = screen.getByText('新增疾病');
      await userEvent.click(createButton);

      await waitFor(() => {
        expect(screen.getByTestId('tabs')).toBeInTheDocument();
        expect(screen.getByText('新增疾病')).toBeInTheDocument();
      });
    });

    it('should render all tab triggers', async () => {
      renderDiseases();

      const createButton = screen.getByText('新增疾病');
      await userEvent.click(createButton);

      await waitFor(() => {
        expect(screen.getByText('基本信息')).toBeInTheDocument();
        expect(screen.getByText('疾病内容')).toBeInTheDocument();
        expect(screen.getByText('作者信息')).toBeInTheDocument();
      });
    });

    it('should validate required fields', async () => {
      renderDiseases();

      const createButton = screen.getByText('新增疾病');
      await userEvent.click(createButton);

      await waitFor(() => {
        expect(screen.getByTestId('tabs')).toBeInTheDocument();
      });

      // Try to submit without filling required fields
      const submitButton = screen.getByText('创建');
      await userEvent.click(submitButton);

      // Should show error for missing required fields
      await waitFor(() => {
        expect(diseasesApi.create).not.toHaveBeenCalled();
      });
    });

    it('should submit create form successfully', async () => {
      renderDiseases();

      const createButton = screen.getByText('新增疾病');
      await userEvent.click(createButton);

      await waitFor(() => {
        expect(screen.getByTestId('tabs-content-basic')).toBeInTheDocument();
      });

      // Fill in the name field
      const nameInput = screen.getByPlaceholderText('请输入疾病名称');
      await userEvent.type(nameInput, '感冒');

      // Select department
      const selectButtons = screen.getAllByText('Change');
      await userEvent.click(selectButtons[1]); // Department select in form

      const submitButton = screen.getByText('创建');
      await userEvent.click(submitButton);

      await waitFor(() => {
        expect(diseasesApi.create).toHaveBeenCalled();
      });
    });
  });

  describe('Edit Disease', () => {
    it('should open edit dialog and fetch disease details', async () => {
      renderDiseases();

      await waitFor(() => {
        expect(screen.getByText('高血压')).toBeInTheDocument();
      });

      const editButtons = screen.getAllByTestId('edit-icon');
      await userEvent.click(editButtons[0]);

      await waitFor(() => {
        expect(diseasesApi.get).toHaveBeenCalledWith(1);
      });
    });

    it('should pre-fill form with disease data', async () => {
      renderDiseases();

      const editButtons = screen.getAllByTestId('edit-icon');
      await userEvent.click(editButtons[0]);

      await waitFor(() => {
        expect(screen.getByText('编辑疾病')).toBeInTheDocument();
      });
    });
  });

  describe('Delete Disease', () => {
    it('should show confirmation dialog before delete', async () => {
      renderDiseases();

      await waitFor(() => {
        expect(screen.getByText('高血压')).toBeInTheDocument();
      });

      const deleteButtons = screen.getAllByTestId('trash-icon');
      await userEvent.click(deleteButtons[0]);

      await waitFor(() => {
        expect(screen.getByText('确认删除')).toBeInTheDocument();
        expect(screen.getByText(/确定要删除疾病 "高血压" 吗/)).toBeInTheDocument();
      });
    });

    it('should call delete API after confirmation', async () => {
      renderDiseases();

      await waitFor(() => {
        expect(screen.getByText('高血压')).toBeInTheDocument();
      });

      const deleteButtons = screen.getAllByTestId('trash-icon');
      await userEvent.click(deleteButtons[0]);

      await waitFor(() => {
        expect(screen.getByText('确认删除')).toBeInTheDocument();
      });

      const confirmButton = screen.getByText('删除');
      await userEvent.click(confirmButton);

      await waitFor(() => {
        expect(diseasesApi.delete).toHaveBeenCalledWith(1);
      });
    });
  });

  describe('Toggle Hot Status', () => {
    it('should toggle hot status', async () => {
      renderDiseases();

      await waitFor(() => {
        expect(screen.getByText('高血压')).toBeInTheDocument();
      });

      const switches = screen.getAllByTestId('switch');
      // First switch is for hot status
      await userEvent.click(switches[0]);

      await waitFor(() => {
        expect(diseasesApi.toggleHot).toHaveBeenCalledWith(1, false);
      });
    });
  });

  describe('Toggle Active Status', () => {
    it('should toggle active status', async () => {
      renderDiseases();

      await waitFor(() => {
        expect(screen.getByText('高血压')).toBeInTheDocument();
      });

      const switches = screen.getAllByTestId('switch');
      // Second switch is for active status
      await userEvent.click(switches[1]);

      await waitFor(() => {
        expect(diseasesApi.toggleActive).toHaveBeenCalledWith(1, false);
      });
    });
  });

  describe('Form Tabs', () => {
    it('should render basic info fields', async () => {
      renderDiseases();

      const createButton = screen.getByText('新增疾病');
      await userEvent.click(createButton);

      await waitFor(() => {
        expect(screen.getByText(/疾病名称/)).toBeInTheDocument();
        expect(screen.getByText(/所属科室/)).toBeInTheDocument();
        expect(screen.getByText(/拼音/)).toBeInTheDocument();
        expect(screen.getByText(/拼音首字母/)).toBeInTheDocument();
        expect(screen.getByText(/别名/)).toBeInTheDocument();
        expect(screen.getByText(/推荐就诊科室/)).toBeInTheDocument();
        expect(screen.getByText(/排序/)).toBeInTheDocument();
        expect(screen.getByText(/热门/)).toBeInTheDocument();
        expect(screen.getByText(/启用/)).toBeInTheDocument();
      });
    });

    it('should render content fields', async () => {
      renderDiseases();

      const createButton = screen.getByText('新增疾病');
      await userEvent.click(createButton);

      // Click on content tab
      const contentTab = screen.getByText('疾病内容');
      await userEvent.click(contentTab);

      await waitFor(() => {
        expect(screen.getByTestId('tabs-content-content')).toBeInTheDocument();
        expect(screen.getByText(/简介/)).toBeInTheDocument();
        expect(screen.getByText(/症状/)).toBeInTheDocument();
        expect(screen.getByText(/病因/)).toBeInTheDocument();
        expect(screen.getByText(/诊断/)).toBeInTheDocument();
        expect(screen.getByText(/治疗/)).toBeInTheDocument();
        expect(screen.getByText(/预防/)).toBeInTheDocument();
        expect(screen.getByText(/日常护理/)).toBeInTheDocument();
      });
    });

    it('should render author info fields', async () => {
      renderDiseases();

      const createButton = screen.getByText('新增疾病');
      await userEvent.click(createButton);

      // Click on author tab
      const authorTab = screen.getByText('作者信息');
      await userEvent.click(authorTab);

      await waitFor(() => {
        expect(screen.getByTestId('tabs-content-author')).toBeInTheDocument();
        expect(screen.getByText(/作者姓名/)).toBeInTheDocument();
        expect(screen.getByText(/作者职称/)).toBeInTheDocument();
        expect(screen.getByText(/作者头像URL/)).toBeInTheDocument();
        expect(screen.getByText(/审核信息/)).toBeInTheDocument();
      });
    });
  });

  describe('Error Handling', () => {
    it('should handle API error on list fetch', async () => {
      vi.mocked(diseasesApi.list).mockRejectedValue(new Error('API Error'));

      renderDiseases();

      await waitFor(() => {
        expect(screen.getByTestId('page-header')).toBeInTheDocument();
      });
    });

    it('should handle API error on delete', async () => {
      vi.mocked(diseasesApi.delete).mockRejectedValue({
        response: { data: { detail: '删除失败' } },
      });

      renderDiseases();

      await waitFor(() => {
        expect(screen.getByText('高血压')).toBeInTheDocument();
      });

      const deleteButtons = screen.getAllByTestId('trash-icon');
      await userEvent.click(deleteButtons[0]);

      const confirmButton = await screen.findByText('删除');
      await userEvent.click(confirmButton);

      await waitFor(() => {
        expect(diseasesApi.delete).toHaveBeenCalled();
      });
    });
  });
});
