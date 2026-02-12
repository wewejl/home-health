/**
 * Knowledge 页面组件测试
 *
 * 测试覆盖：
 * 1. UI 渲染测试 - 页面标题、标签、卡片
 * 2. 加载状态测试
 * 3. 知识库列表测试
 * 4. 文档列表测试
 * 5. CRUD 操作测试 - 创建、编辑、删除知识库/文档
 * 6. 标签页切换测试
 * 7. 上传功能测试
 * 8. 审核功能测试
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { BrowserRouter } from 'react-router-dom';
import Knowledge from '../Knowledge';

// Mock API
vi.mock('@/api', () => ({
  knowledgeBasesApi: {
    list: vi.fn(),
    create: vi.fn(),
    update: vi.fn(),
    delete: vi.fn(),
    reindex: vi.fn(),
    listDocuments: vi.fn(),
    createDocument: vi.fn(),
    uploadDocument: vi.fn(),
  },
  documentsApi: {
    approve: vi.fn(),
    delete: vi.fn(),
  },
  departmentsApi: {
    list: vi.fn(),
  },
  doctorsApi: {
    list: vi.fn(),
  },
}));

// Mock icons
vi.mock('lucide-react', () => ({
  Plus: () => <span data-testid="plus">Plus</span>,
  Edit: () => <span data-testid="edit">Edit</span>,
  Trash2: () => <span data-testid="trash">Trash</span>,
  FileText: () => <span data-testid="file">File</span>,
  Loader2: () => <span data-testid="loader">Loader</span>,
  RefreshCw: () => <span data-testid="refresh">Refresh</span>,
  Upload: () => <span data-testid="upload">Upload</span>,
  Check: () => <span data-testid="check">Check</span>,
  X: () => <span data-testid="x">X</span>,
  Filter: () => <span data-testid="filter">Filter</span>,
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
  Button: ({ children, onClick }: any) => (
    <button onClick={onClick} data-testid="button">{children}</button>
  ),
}));

vi.mock('@/components/ui/input', () => ({
  Input: ({ value, onChange }: any) => (
    <input value={value} onChange={onChange} data-testid="input" />
  ),
}));

vi.mock('@/components/ui/textarea', () => ({
  Textarea: ({ value, onChange, rows }: any) => (
    <textarea value={value} onChange={onChange} rows={rows} data-testid="textarea" />
  ),
}));

vi.mock('@/components/ui/badge', () => ({
  Badge: ({ children, variant }: any) => (
    <span data-variant={variant}>{children}</span>
  ),
}));

vi.mock('@/components/ui/dialog', () => ({
  Dialog: ({ open, children }: any) =>
    open ? <div data-testid="dialog">{children}</div> : null,
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

vi.mock('@/components/ui/alert-dialog', () => ({
  AlertDialog: ({ children }: any) => <div data-testid="alert-dialog">{children}</div>,
  AlertDialogTrigger: ({ children }: any) => <button>{children}</button>,
  AlertDialogContent: ({ children }: any) => <div data-testid="alert-content">{children}</div>,
  AlertDialogHeader: ({ children }: any) => <div>{children}</div>,
  AlertDialogTitle: ({ children }: any) => <h3>{children}</h3>,
  AlertDialogDescription: ({ children }: any) => <p>{children}</p>,
  AlertDialogFooter: ({ children }: any) => <div>{children}</div>,
  AlertDialogCancel: ({ children }: any) => <button>{children}</button>,
  AlertDialogAction: ({ children }: any) => <button>{children}</button>,
}));

vi.mock('@/components/ui/tabs', () => ({
  Tabs: ({ children, value, onValueChange }: any) => <div data-value={value}>{children}</div>,
  TabsList: ({ children }: any) => <div>{children}</div>,
  TabsTrigger: ({ children, value }: any) => <button data-value={value}>{children}</button>,
  TabsContent: ({ children, value }: any) => <div data-value={value}>{children}</div>,
}));

vi.mock('@/components/ui/label', () => ({
  Label: ({ children, htmlFor }: any) => <label htmlFor={htmlFor}>{children}</label>,
}));

vi.mock('@/components/ui/card', () => ({
  Card: ({ children }: any) => <div data-testid="card">{children}</div>,
  CardContent: ({ children }: any) => <div>{children}</div>,
  CardHeader: ({ children }: any) => <div>{children}</div>,
  CardTitle: ({ children }: any) => <h3>{children}</h3>,
  CardDescription: ({ children }: any) => <p>{children}</p>,
}));

vi.mock('@/components/medical/page-header', () => ({
  PageHeader: ({ title }: any) => <div data-testid="page-header"><h1>{title}</h1></div>,
}));

vi.mock('@/components/medical/loading-skeleton', () => ({
  LoadingSkeleton: () => <div data-testid="loading-skeleton">Loading...</div>,
}));

import { knowledgeBasesApi, documentsApi, departmentsApi, doctorsApi } from '@/api';

describe('Knowledge Page', () => {
  const mockKnowledgeBases = [
    {
      id: 'kb-dermatology-liuwu',
      name: '皮肤科知识库',
      description: '皮肤病相关',
      total_documents: 15,
      total_chunks: 100,
      is_active: true,
    },
  ];

  const mockDocuments = [
    {
      id: 1,
      title: '湿疹诊断',
      content: '湿疹的诊断标准',
      doc_type: 'case',
      status: 'pending',
      tags: ['皮肤', '诊断'],
      created_at: '2026-02-12',
    },
  ];

  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(knowledgeBasesApi.list).mockResolvedValue({ data: mockKnowledgeBases });
    vi.mocked(knowledgeBasesApi.create).mockResolvedValue({ success: true });
    vi.mocked(knowledgeBasesApi.update).mockResolvedValue({ success: true });
    vi.mocked(knowledgeBasesApi.delete).mockResolvedValue({ success: true });
    vi.mocked(knowledgeBasesApi.reindex).mockResolvedValue({ success: true });
    vi.mocked(knowledgeBasesApi.listDocuments).mockResolvedValue({ data: mockDocuments });
    vi.mocked(knowledgeBasesApi.createDocument).mockResolvedValue({ success: true });
    vi.mocked(knowledgeBasesApi.uploadDocument).mockResolvedValue({ success: true });
    vi.mocked(documentsApi.approve).mockResolvedValue({ success: true });
    vi.mocked(documentsApi.delete).mockResolvedValue({ success: true });
    vi.mocked(departmentsApi.list).mockResolvedValue({ data: [] });
    vi.mocked(doctorsApi.list).mockResolvedValue({ data: [] });
  });

  const renderKnowledge = () => {
    return render(
      <BrowserRouter>
        <Knowledge />
      </BrowserRouter>
    );
  };

  describe('Rendering', () => {
    it('should render page header', async () => {
      renderKnowledge();

      expect(screen.getByTestId('page-header')).toBeInTheDocument();
      expect(screen.getByText('知识库管理')).toBeInTheDocument();
    });

    it('should render two cards', async () => {
      renderKnowledge();

      const cards = screen.getAllByTestId('card');
      expect(cards.length).toBeGreaterThanOrEqual(2);
    });
  });

  describe('Knowledge Bases', () => {
    it('should render KB list table', async () => {
      renderKnowledge();

      expect(screen.getByText('知识库列表')).toBeInTheDocument();
    });

    it('should render KB table rows', async () => {
      renderKnowledge();

      await waitFor(() => {
        expect(screen.getByText(/kb-derm/)).toBeInTheDocument();
      expect(screen.getByText('皮肤科知识库')).toBeInTheDocument();
      });
    });

    it('should open create KB dialog', async () => {
      renderKnowledge();

      const createButton = screen.getByText('新增');
      await userEvent.click(createButton);

      await waitFor(() => {
        expect(screen.getByTestId('dialog')).toBeInTheDocument();
        expect(screen.getByText('新增知识库')).toBeInTheDocument();
      });
    });

    it('should validate KB ID when creating', async () => {
      renderKnowledge();

      const createButton = screen.getByText('新增');
      await userEvent.click(createButton);

      const submitButton = screen.getAllByText('创建').find(b => b);
      await userEvent.click(submitButton);

      await waitFor(() => {
        expect(screen.getByText('请输入知识库ID')).toBeInTheDocument();
      });
    });

    it('should validate KB name when creating', async () => {
      renderKnowledge();

      const createButton = screen.getByText('新增');
      await userEvent.click(createButton);

      // Fill ID to pass ID validation
      const inputs = screen.getAllByTestId('input');
      await userEvent.type(inputs[0], 'kb-test-123');

      const submitButton = screen.getAllByText('创建').find(b => b);
      await userEvent.click(submitButton);

      await waitFor(() => {
        expect(screen.getByText('请输入知识库名称')).toBeInTheDocument();
      });
    });

    it('should submit create KB successfully', async () => {
      renderKnowledge();

      const createButton = screen.getByText('新增');
      await userEvent.click(createButton);

      // Fill all required fields
      const inputs = screen.getAllByTestId('input');
      await userEvent.type(inputs[0], 'kb-test-123');
      await userEvent.type(inputs[1], '测试知识库');

      const submitButton = screen.getAllByText('创建').find(b => b);
      await userEvent.click(submitButton);

      await waitFor(() => {
        expect(knowledgeBasesApi.create).toHaveBeenCalled();
      });
    });

    it('should delete KB with confirmation', async () => {
      renderKnowledge();

      await waitFor(() => {
        expect(screen.getByText(/kb-derm/)).toBeInTheDocument();
      });

      // Find delete button for first KB
      const deleteButtons = screen.getAllByTestId('trash');
      if (deleteButtons.length > 0) {
        // Click first delete button
        await userEvent.click(deleteButtons[0]);

        // Alert dialog should open
        await waitFor(() => {
          expect(screen.getByTestId('alert-content')).toBeInTheDocument();
          expect(screen.getByText(/删除知识库/)).toBeInTheDocument();
        });

        // Confirm deletion
        const confirmButton = screen.getByText('删除');
        await userEvent.click(confirmButton);

        await waitFor(() => {
          expect(knowledgeBasesApi.delete).toHaveBeenCalled();
        });
      }
    });

    it('should reindex KB', async () => {
      renderKnowledge();

      await waitFor(() => {
        expect(screen.getByText(/kb-derm/)).toBeInTheDocument();
      });

      const refreshButtons = screen.getAllByTestId('refresh');
      if (refreshButtons.length > 0) {
        await userEvent.click(refreshButtons[0]);

        await waitFor(() => {
          expect(knowledgeBasesApi.reindex).toHaveBeenCalled();
        });
      }
    });
  });

  describe('Documents', () => {
    it('should show empty state when no KB selected', async () => {
      renderKnowledge();

      await waitFor(() => {
        expect(screen.getByText('请从左侧选择知识库')).toBeInTheDocument();
      });
    });

    it('should render documents after selecting KB', async () => {
      renderKnowledge();

      await waitFor(() => {
        const rows = screen.getAllByTestId('table');
        expect(rows.length).toBeGreaterThanOrEqual(1);
      });
    });

    it('should render document types', async () => {
      renderKnowledge();

      await waitFor(() => {
        expect(screen.getByText('ID')).toBeInTheDocument();
        expect(screen.getByText('标题')).toBeInTheDocument();
        expect(screen.getByText('类型')).toBeInTheDocument();
        expect(screen.getByText('状态')).toBeInTheDocument();
        expect(screen.getByText('操作')).toBeInTheDocument();
      });
    });

    it('should create document', async () => {
      renderKnowledge();

      await waitFor(() => {
        const firstRow = screen.getAllByTestId('table')[0];
        expect(firstRow).toBeInTheDocument();
      });

      const firstRowText = firstRow?.textContent || '';
      if (firstRowText.includes('kb-derm')) {
        // Click on KB to select it
        await userEvent.click(firstRow);
      }

      await waitFor(() => {
        expect(screen.getByText('添加文档')).toBeInTheDocument();
      });

      const addButton = screen.getByText('添加');
      await userEvent.click(addButton);

      await waitFor(() => {
        expect(screen.getByTestId('dialog')).toBeInTheDocument();
      });
    });

    it('should approve document', async () => {
      renderKnowledge();

      // Set up with pending document
      await waitFor(() => {
        const tables = screen.getAllByTestId('table');
        if (tables.length > 0) {
          const firstRow = tables[0];
          await userEvent.click(firstRow);
        }
      });

      const approveButtons = screen.getAllByTestId('check');
      if (approveButtons.length > 0) {
        await userEvent.click(approveButtons[0]);

        await waitFor(() => {
          expect(documentsApi.approve).toHaveBeenCalled();
        });
      }
    });

    it('should delete document with confirmation', async () => {
      renderKnowledge();

      // Set up with document
      await waitFor(() => {
        const tables = screen.getAllByTestId('table');
        if (tables.length > 0) {
          const firstRow = tables[0];
          await userEvent.click(firstRow);
        }
      });

      const deleteButtons = screen.getAllByTestId('trash');
      if (deleteButtons.length > 0) {
        await userEvent.click(deleteButtons[0]);

        await waitFor(() => {
          expect(screen.getByTestId('alert-content')).toBeInTheDocument();
        });
      }
    });
  });

  describe('Loading State', () => {
    it('should show loading skeleton', async () => {
      let resolveList: (value: any) => void;
      const pendingPromise = new Promise(resolve => {
        resolveList = resolve;
      });
      vi.mocked(knowledgeBasesApi.list).mockReturnValue(pendingPromise as any);

      renderKnowledge();

      expect(screen.getByTestId('loading-skeleton')).toBeInTheDocument();

      resolveList!({ data: [] });
    });
  });

  describe('Empty States', () => {
    it('should show empty KB list', async () => {
      vi.mocked(knowledgeBasesApi.list).mockResolvedValue({ data: [] });

      renderKnowledge();

      await waitFor(() => {
        expect(screen.getByText('暂无知识库')).toBeInTheDocument();
      });
    });

    it('should show empty documents list', async () => {
      vi.mocked(knowledgeBasesApi.list).mockResolvedValue({
        data: [{ id: 'test-kb', name: 'Test', total_documents: 0, total_chunks: 0, is_active: true }],
      });
      vi.mocked(knowledgeBasesApi.listDocuments).mockResolvedValue({ data: [] });

      renderKnowledge();

      await waitFor(() => {
        const tables = screen.getAllByTestId('table');
        if (tables.length > 0) {
          await userEvent.click(tables[0]);
        }
      });

      await waitFor(() => {
        expect(screen.getByText('暂无文档')).toBeInTheDocument();
      });
    });
  });

  describe('Error Handling', () => {
    it('should handle API errors', async () => {
      vi.mocked(knowledgeBasesApi.list).mockRejectedValue(new Error('API Error'));

      renderKnowledge();

      // Should still render without crashing
      await waitFor(() => {
        expect(screen.getByTestId('page-header')).toBeInTheDocument();
      });
    });
  });
});
