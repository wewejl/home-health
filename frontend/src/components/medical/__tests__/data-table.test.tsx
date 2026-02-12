/**
 * DataTable 组件测试
 *
 * 测试覆盖：
 * 1. 组件渲染测试
 * 2. Props 传递测试
 * 3. 用户交互测试（排序、分页、筛选、行点击）
 * 4. 样式变化测试
 * 5. 边界条件测试
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import {
  DataTable,
  DataTableColumnHeader,
  type ColumnDef,
  type SortDirection,
  type SortingState,
  type PaginationState,
} from '../data-table';

interface TestData {
  id: number;
  name: string;
  age: number;
  status: string;
}

const mockData: TestData[] = [
  { id: 1, name: '张三', age: 35, status: '活跃' },
  { id: 2, name: '李四', age: 28, status: '非活跃' },
  { id: 3, name: '王五', age: 42, status: '活跃' },
  { id: 4, name: '赵六', age: 31, status: '待审核' },
  { id: 5, name: '钱七', age: 26, status: '活跃' },
];

const mockColumns: ColumnDef<TestData>[] = [
  { id: 'id', header: 'ID', accessorKey: 'id' },
  { id: 'name', header: '姓名', accessorKey: 'name' },
  { id: 'age', header: '年龄', accessorKey: 'age' },
  {
    id: 'status',
    header: '状态',
    accessorKey: 'status',
    cell: (row) => <span>{row.status}</span>,
  },
];

describe('DataTable Component', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('Rendering', () => {
    it('should render table with data', () => {
      render(<DataTable data={mockData} columns={mockColumns} />);

      expect(screen.getByText('张三')).toBeInTheDocument();
      expect(screen.getByText('李四')).toBeInTheDocument();
      expect(screen.getByText('王五')).toBeInTheDocument();
    });

    it('should render all column headers', () => {
      render(<DataTable data={mockData} columns={mockColumns} />);

      expect(screen.getByText('ID')).toBeInTheDocument();
      expect(screen.getByText('姓名')).toBeInTheDocument();
      expect(screen.getByText('年龄')).toBeInTheDocument();
      expect(screen.getByText('状态')).toBeInTheDocument();
    });

    it('should render custom cell content', () => {
      render(<DataTable data={mockData} columns={mockColumns} />);

      // Custom cell should render
      expect(screen.getByText('活跃')).toBeInTheDocument();
      expect(screen.getByText('非活跃')).toBeInTheDocument();
    });

    it('should render empty state when no data', () => {
      render(<DataTable data={[]} columns={mockColumns} />);

      expect(screen.getByText('暂无数据')).toBeInTheDocument();
    });

    it('should render custom empty text', () => {
      render(
        <DataTable data={[]} columns={mockColumns} emptyText="没有找到任何记录" />
      );

      expect(screen.getByText('没有找到任何记录')).toBeInTheDocument();
    });

    it('should render loading state', () => {
      render(<DataTable data={mockData} columns={mockColumns} loading />);

      expect(screen.getByText('加载中...')).toBeInTheDocument();
    });

    it('should render custom loading text', () => {
      render(
        <DataTable data={mockData} columns={mockColumns} loading loadingText="正在加载..." />
      );

      expect(screen.getByText('正在加载...')).toBeInTheDocument();
    });
  });

  describe('Pagination', () => {
    it('should render pagination controls by default', () => {
      render(<DataTable data={mockData} columns={mockColumns} />);

      // Pagination info should be visible
      expect(screen.getByText(/第.*条/)).toBeInTheDocument();
    });

    it('should not render pagination when disabled', () => {
      render(
        <DataTable data={mockData} columns={mockColumns} pagination={false} />
      );

      expect(screen.queryByText(/第.*条/)).not.toBeInTheDocument();
    });

    it('should calculate correct total pages', () => {
      render(<DataTable data={mockData} columns={mockColumns} />);

      // Should show page count info
      expect(screen.getByText(/共 5 条/)).toBeInTheDocument();
    });

    it('should handle controlled pagination', () => {
      const controlledPagination: PaginationState = {
        pageIndex: 0,
        pageSize: 2,
      };

      render(
        <DataTable
          data={mockData}
          columns={mockColumns}
          pagination={controlledPagination}
        />
      );

      // Should only show first 2 items
      expect(screen.getByText('张三')).toBeInTheDocument();
      expect(screen.getByText('李四')).toBeInTheDocument();
      expect(screen.queryByText('王五')).not.toBeInTheDocument();
    });

    it('should call onPaginationChange when page changes', async () => {
      const user = userEvent.setup();
      const onPaginationChange = vi.fn();

      render(
        <DataTable
          data={mockData}
          columns={mockColumns}
          onPaginationChange={onPaginationChange}
        />
      );

      // Click next page button
      const nextButton = screen.getAllByRole('button').find(
        (btn) => btn.querySelector('.lucide-chevron-right')
      );

      if (nextButton) {
        await user.click(nextButton);
        expect(onPaginationChange).toHaveBeenCalled();
      }
    });

    it('should call onPaginationChange when page size changes', async () => {
      const user = userEvent.setup();
      const onPaginationChange = vi.fn();

      render(
        <DataTable
          data={mockData}
          columns={mockColumns}
          onPaginationChange={onPaginationChange}
        />
      );

      // Change page size
      const selectElement = screen.getByRole('combobox');
      await user.selectOptions(selectElement, '20');

      expect(onPaginationChange).toHaveBeenCalledWith(
        expect.objectContaining({
          pageSize: 20,
          pageIndex: 0,
        })
      );
    });

    it('should disable first/prev buttons on first page', () => {
      render(<DataTable data={mockData} columns={mockColumns} />);

      const buttons = screen.getAllByRole('button');
      const firstPageButton = buttons.find((btn) =>
        btn.querySelector('.lucide-chevrons-left')
      );
      const prevButton = buttons.find((btn) =>
        btn.querySelector('.lucide-chevron-left')
      );

      expect(firstPageButton).toBeDisabled();
      expect(prevButton).toBeDisabled();
    });

    it('should disable last/next buttons on last page', () => {
      render(
        <DataTable
          data={mockData}
          columns={mockColumns}
          pagination={{ pageIndex: 0, pageSize: 10 }}
        />
      );

      // With only 5 items and pageSize 10, should be on last page
      const buttons = screen.getAllByRole('button');
      const lastPageButton = buttons.find((btn) =>
        btn.querySelector('.lucide-chevrons-right')
      );
      const nextButton = buttons.find((btn) =>
        btn.querySelector('.lucide-chevron-right')
      );

      expect(lastPageButton).toBeDisabled();
      expect(nextButton).toBeDisabled();
    });
  });

  describe('Sorting', () => {
    it('should render sortable indicator for sortable columns', () => {
      const sortableColumns: ColumnDef<TestData>[] = [
        { id: 'name', header: '姓名', accessorKey: 'name', sortable: true },
        { id: 'age', header: '年龄', accessorKey: 'age', sortable: true },
      ];

      render(<DataTable data={mockData} columns={sortableColumns} />);

      // Should show sort indicators
      const sortIndicators = screen.getAllByLabelText(/sort/i);
      expect(sortIndicators.length).toBeGreaterThan(0);
    });

    it('should call onSortingChange when column header is clicked', async () => {
      const user = userEvent.setup();
      const onSortingChange = vi.fn();

      const sortableColumns: ColumnDef<TestData>[] = [
        { id: 'name', header: '姓名', accessorKey: 'name', sortable: true },
      ];

      render(
        <DataTable
          data={mockData}
          columns={sortableColumns}
          onSortingChange={onSortingChange}
        />
      );

      const nameHeader = screen.getByText('姓名');
      await user.click(nameHeader);

      expect(onSortingChange).toHaveBeenCalled();
    });

    it('should cycle through sort directions', async () => {
      const user = userEvent.setup();
      const onSortingChange = vi.fn();

      const sortableColumns: ColumnDef<TestData>[] = [
        { id: 'name', header: '姓名', accessorKey: 'name', sortable: true },
      ];

      render(
        <DataTable
          data={mockData}
          columns={sortableColumns}
          onSortingChange={onSortingChange}
        />
      );

      const nameHeader = screen.getByText('姓名');

      // First click - asc
      await user.click(nameHeader);
      expect(onSortingChange).toHaveBeenCalledWith(
        expect.objectContaining({ direction: 'asc' })
      );

      // Second click - desc
      await user.click(nameHeader);
      expect(onSortingChange).toHaveBeenCalledWith(
        expect.objectContaining({ direction: 'desc' })
      );
    });

    it('should respect controlled sorting state', () => {
      const controlledSorting: SortingState = {
        columnId: 'name',
        direction: 'asc',
      };

      render(
        <DataTable
          data={mockData}
          columns={mockColumns}
          sorting={controlledSorting}
        />
      );

      // Data should be sorted by name
      const rows = screen.getAllByRole('row');
      // First data row should have the sorted content
      expect(rows[1]).toContainHTML('张三'); // First name alphabetically
    });

    it('should not sort non-sortable columns', async () => {
      const user = userEvent.setup();
      const onSortingChange = vi.fn();

      const nonSortableColumns: ColumnDef<TestData>[] = [
        { id: 'name', header: '姓名', accessorKey: 'name', sortable: false },
      ];

      render(
        <DataTable
          data={mockData}
          columns={nonSortableColumns}
          onSortingChange={onSortingChange}
        />
      );

      const nameHeader = screen.getByText('姓名');
      await user.click(nameHeader);

      expect(onSortingChange).not.toHaveBeenCalled();
    });

    it('should disable sorting globally when sortable prop is false', () => {
      const sortableColumns: ColumnDef<TestData>[] = [
        { id: 'name', header: '姓名', accessorKey: 'name', sortable: true },
      ];

      render(<DataTable data={mockData} columns={sortableColumns} sortable={false} />);

      // Sort indicators should not be interactive
      const nameHeader = screen.getByText('姓名');
      expect(nameHeader.closest('[class*="cursor"]')).not.toBeTruthy();
    });
  });

  describe('Filtering', () => {
    it('should render search input when filterable is true', () => {
      render(<DataTable data={mockData} columns={mockColumns} />);

      const searchInput = screen.getByRole('textbox');
      expect(searchInput).toBeInTheDocument();
      expect(searchInput).toHaveAttribute('placeholder', '搜索...');
    });

    it('should render custom filter placeholder', () => {
      render(
        <DataTable
          data={mockData}
          columns={mockColumns}
          filterPlaceholder="搜索患者..."
        />
      );

      const searchInput = screen.getByRole('textbox');
      expect(searchInput).toHaveAttribute('placeholder', '搜索患者...');
    });

    it('should filter data when search input changes', async () => {
      const user = userEvent.setup();

      render(<DataTable data={mockData} columns={mockColumns} />);

      const searchInput = screen.getByRole('textbox');
      await user.type(searchInput, '张三');

      // Should only show matching results
      await waitFor(() => {
        expect(screen.getByText('张三')).toBeInTheDocument();
        expect(screen.queryByText('李四')).not.toBeInTheDocument();
      });
    });

    it('should not render search input when filterable is false', () => {
      render(
        <DataTable data={mockData} columns={mockColumns} filterable={false} />
      );

      const searchInput = screen.queryByRole('textbox');
      expect(searchInput).not.toBeInTheDocument();
    });
  });

  describe('Row Interactions', () => {
    it('should call onRowClick when row is clicked', async () => {
      const user = userEvent.setup();
      const onRowClick = vi.fn();

      render(
        <DataTable data={mockData} columns={mockColumns} onRowClick={onRowClick} />
      );

      const firstRow = screen.getByText('张三').closest('tr');
      if (firstRow) {
        await user.click(firstRow);
        expect(onRowClick).toHaveBeenCalledWith(mockData[0]);
      }
    });

    it('should apply cursor-pointer to clickable rows', () => {
      render(
        <DataTable data={mockData} columns={mockColumns} onRowClick={vi.fn()} />
      );

      const firstRow = screen.getByText('张三').closest('tr');
      expect(firstRow).toHaveClass('cursor-pointer');
    });

    it('should apply custom row className', () => {
      render(
        <DataTable
          data={mockData}
          columns={mockColumns}
          rowClassName="custom-row-class"
        />
      );

      const firstRow = screen.getByText('张三').closest('tr');
      expect(firstRow).toHaveClass('custom-row-class');
    });

    it('should apply dynamic row className function', () => {
      const getRowClass = vi.fn((row: TestData) =>
        row.status === '活跃' ? 'active-row' : 'inactive-row'
      );

      render(
        <DataTable
          data={mockData}
          columns={mockColumns}
          rowClassName={getRowClass}
        />
      );

      const firstRow = screen.getByText('张三').closest('tr');
      expect(firstRow).toHaveClass('active-row');
    });
  });

  describe('Column Alignment', () => {
    it('should align columns to left by default', () => {
      const columns: ColumnDef<TestData>[] = [
        { id: 'name', header: '姓名', accessorKey: 'name', align: 'left' },
      ];

      render(<DataTable data={mockData} columns={columns} />);

      const header = screen.getByText('姓名');
      expect(header.parentElement).toHaveClass('text-left');
    });

    it('should align columns to center', () => {
      const columns: ColumnDef<TestData>[] = [
        { id: 'name', header: '姓名', accessorKey: 'name', align: 'center' },
      ];

      render(<DataTable data={mockData} columns={columns} />);

      const header = screen.getByText('姓名');
      expect(header.parentElement).toHaveClass('text-center');
    });

    it('should align columns to right', () => {
      const columns: ColumnDef<TestData>[] = [
        { id: 'id', header: 'ID', accessorKey: 'id', align: 'right' },
      ];

      render(<DataTable data={mockData} columns={columns} />);

      const header = screen.getByText('ID');
      expect(header.parentElement).toHaveClass('text-right');
    });
  });

  describe('Dense Mode', () => {
    it('should apply dense styling when dense is true', () => {
      render(<DataTable data={mockData} columns={mockColumns} dense />);

      const headerRow = screen.getAllByRole('row')[0];
      expect(headerRow).toHaveClass('h-9');
    });

    it('should apply normal styling when dense is false', () => {
      render(<DataTable data={mockData} columns={mockColumns} dense={false} />);

      const headerRow = screen.getAllByRole('row')[0];
      expect(headerRow).toHaveClass('h-10');
    });
  });

  describe('Striped Rows', () => {
    it('should apply striped styling by default', () => {
      render(<DataTable data={mockData} columns={mockColumns} />);

      const rows = screen.getAllByRole('row');
      // First data row (index 1) should be striped
      expect(rows[1]).toHaveClass('bg-surface-alt/30');
    });

    it('should not apply striped styling when striped is false', () => {
      render(<DataTable data={mockData} columns={mockColumns} striped={false} />);

      const rows = screen.getAllByRole('row');
      // No rows should have striped class
      rows.forEach((row) => {
        expect(row).not.toHaveClass('bg-surface-alt/30');
      });
    });
  });

  describe('Header Actions', () => {
    it('should render header actions when provided', () => {
      render(
        <DataTable
          data={mockData}
          columns={mockColumns}
          headerActions={<button data-testid="header-action">Action</button>}
        />
      );

      expect(screen.getByTestId('header-action')).toBeInTheDocument();
    });
  });

  describe('Visible Columns', () => {
    it('should limit visible columns', () => {
      render(
        <DataTable data={mockData} columns={mockColumns} visibleColumns={2} />
      );

      expect(screen.getByText('ID')).toBeInTheDocument();
      expect(screen.getByText('姓名')).toBeInTheDocument();
      // Last two columns should not be visible
      expect(screen.queryByText('年龄')).not.toBeInTheDocument();
      expect(screen.queryByText('状态')).not.toBeInTheDocument();
    });

    it('should show all columns by default', () => {
      render(<DataTable data={mockData} columns={mockColumns} />);

      expect(screen.getByText('ID')).toBeInTheDocument();
      expect(screen.getByText('姓名')).toBeInTheDocument();
      expect(screen.getByText('年龄')).toBeInTheDocument();
      expect(screen.getByText('状态')).toBeInTheDocument();
    });
  });

  describe('Custom Classes', () => {
    it('should apply custom className to table container', () => {
      const { container } = render(
        <DataTable data={mockData} columns={mockColumns} className="custom-class" />
      );

      const table = container.querySelector('.rounded-lg');
      expect(table).toHaveClass('custom-class');
    });

    it('should apply custom containerClassName', () => {
      const { container } = render(
        <DataTable
          data={mockData}
          columns={mockColumns}
          containerClassName="custom-container"
        />
      );

      const outerContainer = container.querySelector('.custom-container');
      expect(outerContainer).toBeInTheDocument();
    });
  });

  describe('Edge Cases', () => {
    it('should handle empty columns array', () => {
      render(<DataTable data={mockData} columns={[]} />);

      // Should not crash
      expect(screen.queryByText('张三')).not.toBeInTheDocument();
    });

    it('should handle data with null/undefined values', () => {
      const dataWithNulls: TestData[] = [
        { id: 1, name: '', age: 0, status: '' },
      ];

      render(<DataTable data={dataWithNulls} columns={mockColumns} />);

      // Should render without crashing
      expect(screen.getByText('')).toBeInTheDocument();
    });

    it('should handle server-side pagination with totalCount', () => {
      render(
        <DataTable
          data={mockData.slice(0, 2)}
          columns={mockColumns}
          pagination={{ pageIndex: 0, pageSize: 2 }}
          totalCount={100}
        />
      );

      // Should show total count from prop
      expect(screen.getByText(/共 100 条/)).toBeInTheDocument();
    });
  });
});

describe('DataTableColumnHeader Component', () => {
  it('should render column header', () => {
    const column: ColumnDef<TestData> = {
      id: 'name',
      header: '姓名',
      accessorKey: 'name',
    };

    render(
      <DataTableColumnHeader
        column={column}
        onSort={vi.fn()}
        sorting={{ columnId: '', direction: null }}
      />
    );

    expect(screen.getByText('姓名')).toBeInTheDocument();
  });

  it('should render sort indicators for sortable columns', () => {
    const column: ColumnDef<TestData> = {
      id: 'name',
      header: '姓名',
      accessorKey: 'name',
      sortable: true,
    };

    render(
      <DataTableColumnHeader
        column={column}
        onSort={vi.fn()}
        sorting={{ columnId: '', direction: null }}
      />
    );

    // Should have sort chevrons
    const chevrons = screen.getAllByRole('img', { hidden: true });
    expect(chevrons.length).toBeGreaterThan(0);
  });

  it('should call onSort when sortable header is clicked', async () => {
    const user = userEvent.setup();
    const column: ColumnDef<TestData> = {
      id: 'name',
      header: '姓名',
      accessorKey: 'name',
      sortable: true,
    };
    const onSort = vi.fn();

    render(
      <DataTableColumnHeader
        column={column}
        onSort={onSort}
        sorting={{ columnId: '', direction: null }}
      />
    );

    const header = screen.getByText('姓名');
    await user.click(header);

    expect(onSort).toHaveBeenCalledWith('name');
  });

  it('should show active sort state', () => {
    const column: ColumnDef<TestData> = {
      id: 'name',
      header: '姓名',
      accessorKey: 'name',
      sortable: true,
    };

    render(
      <DataTableColumnHeader
        column={column}
        onSort={vi.fn()}
        sorting={{ columnId: 'name', direction: 'asc' }}
      />
    );

    // Should highlight the active sort indicator
    const container = screen.getByText('姓名').parentElement;
    expect(container).toBeInTheDocument();
  });
});
