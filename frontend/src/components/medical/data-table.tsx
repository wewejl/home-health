import {
  type ReactNode,
  useState,
  useMemo,
  useCallback,
} from 'react';
import { cn } from '@/lib/utils';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import {
  ChevronLeft,
  ChevronRight,
  ChevronsLeft,
  ChevronsRight,
  Search,
  SlidersHorizontal,
  Loader2,
} from 'lucide-react';

/**
 * 表格列定义
 */
export interface ColumnDef<T> {
  /** 列的唯一标识 */
  id: string;
  /** 列标题 */
  header: ReactNode | string;
  /** 获取单元格值的函数 */
  cell?: (row: T) => ReactNode;
  /** 访问行数据的键路径 */
  accessorKey?: keyof T | string;
  /** 列宽度 */
  width?: number | string;
  /** 是否可排序 */
  sortable?: boolean;
  /** 是否可筛选 */
  filterable?: boolean;
  /** 对齐方式 */
  align?: 'left' | 'center' | 'right';
  /** 自定义单元格类名 */
  cellClassName?: string | ((row: T) => string);
}

/**
 * 排序方向
 */
export type SortDirection = 'asc' | 'desc' | null;

/**
 * 排序状态
 */
export interface SortingState {
  columnId: string;
  direction: SortDirection;
}

/**
 * 分页状态
 */
export interface PaginationState {
  pageIndex: number;
  pageSize: number;
}

/**
 * 筛选状态
 */
export interface FilterState {
  columnId: string;
  value: string;
}

/**
 * 数据表格组件属性
 */
export interface DataTableProps<T> {
  /** 表格数据 */
  data: T[];
  /** 列定义 */
  columns: ColumnDef<T>[];
  /** 是否显示加载状态 */
  loading?: boolean;
  /** 加载文本 */
  loadingText?: string;
  /** 空状态文本 */
  emptyText?: string;
  /** 是否显示斑马纹 */
  striped?: boolean;
  /** 行唯一标识键 */
  rowKey?: keyof T;
  /** 行点击事件 */
  onRowClick?: (row: T) => void;
  /** 行类名 */
  rowClassName?: string | ((row: T) => string);
  /** 是否启用分页 */
  pagination?: boolean | PaginationState;
  /** 分页状态变化回调 */
  onPaginationChange?: (pagination: PaginationState) => void;
  /** 数据总数（用于服务端分页） */
  totalCount?: number;
  /** 是否启用排序 */
  sortable?: boolean;
  /** 排序状态 */
  sorting?: SortingState;
  /** 排序状态变化回调 */
  onSortingChange?: (sorting: SortingState) => void;
  /** 是否启用筛选 */
  filterable?: boolean;
  /** 筛选占位符 */
  filterPlaceholder?: string;
  /** 额外类名 */
  className?: string;
  /** 表格容器类名 */
  containerClassName?: string;
  /** 密集模式（更小的单元格） */
  dense?: boolean;
  /** 表格头部操作区域 */
  headerActions?: ReactNode;
  /** 默认显示的列数（响应式） */
  visibleColumns?: number;
}

/**
 * DataTable - 数据表格组件
 *
 * 功能特性：
 * - 支持分页（前端/后端）
 * - 支持排序
 * - 支持筛选/搜索
 * - 支持行点击
 * - 支持自定义单元格渲染
 * - 响应式设计
 *
 * @example
 * ```tsx
 * interface Patient {
 *   id: number;
 *   name: string;
 *   age: number;
 *   status: string;
 * }
 *
 * const columns: ColumnDef<Patient>[] = [
 *   { id: 'name', header: '姓名', accessorKey: 'name' },
 *   { id: 'age', header: '年龄', accessorKey: 'age' },
 *   {
 *     id: 'status',
 *     header: '状态',
 *     cell: (row) => <Badge>{row.status}</Badge>,
 *   },
 * ];
 *
 * <DataTable data={patients} columns={columns} />
 * ```
 */
export function DataTable<T extends Record<string, unknown>>({
  data,
  columns,
  loading = false,
  loadingText = '加载中...',
  emptyText = '暂无数据',
  striped = true,
  rowKey = 'id' as keyof T,
  onRowClick,
  rowClassName,
  pagination = true,
  onPaginationChange,
  totalCount,
  sortable: globalSortable = true,
  sorting: controlledSorting,
  onSortingChange,
  filterable: globalFilterable = true,
  filterPlaceholder = '搜索...',
  className,
  containerClassName,
  dense = false,
  headerActions,
  visibleColumns,
}: DataTableProps<T>) {
  // === 状态管理 ===

  // 内部排序状态
  const [internalSorting, setInternalSorting] = useState<SortingState>({
    columnId: '',
    direction: null,
  });

  // 内部分页状态
  const [internalPagination, setInternalPagination] = useState<PaginationState>({
    pageIndex: 0,
    pageSize: 10,
  });

  // 内部筛选状态
  const [globalFilter, setGlobalFilter] = useState('');

  // 使用受控或非受控状态
  const sorting = controlledSorting ?? internalSorting;
  const paginationState =
    typeof pagination === 'boolean'
      ? internalPagination
      : { pageIndex: pagination.pageIndex, pageSize: pagination.pageSize };

  // === 数据处理 ===

  // 排序和筛选后的数据（前端分页）
  const processedData = useMemo(() => {
    let result = [...data];

    // 全局筛选
    if (globalFilter && globalFilterable) {
      const filterLower = globalFilter.toLowerCase();
      result = result.filter((row) =>
        columns.some((col) => {
          const value = col.accessorKey
            ? String(row[col.accessorKey] ?? '')
            : col.cell
              ? String(col.cell(row) ?? '')
              : '';
          return value.toLowerCase().includes(filterLower);
        })
      );
    }

    // 排序
    if (sorting.columnId && sorting.direction) {
      const column = columns.find((col) => col.id === sorting.columnId);
      if (column) {
        result.sort((a, b) => {
          const aValue = column.accessorKey
            ? (a[column.accessorKey] as string)
            : '';
          const bValue = column.accessorKey
            ? (b[column.accessorKey] as string)
            : '';
          const compareResult = String(aValue ?? '').localeCompare(
            String(bValue ?? '')
          );
          return sorting.direction === 'asc' ? compareResult : -compareResult;
        });
      }
    }

    return result;
  }, [data, globalFilter, sorting, columns, globalFilterable]);

  // 分页后的数据
  const paginatedData = useMemo(() => {
    // 如果有 totalCount，说明是服务端分页，直接返回原始数据
    if (totalCount !== undefined) {
      return data;
    }

    const start = paginationState.pageIndex * paginationState.pageSize;
    return processedData.slice(start, start + paginationState.pageSize);
  }, [processedData, paginationState, totalCount, data]);

  // 总页数
  const totalPages = totalCount
    ? Math.ceil(totalCount / paginationState.pageSize)
    : Math.ceil(processedData.length / paginationState.pageSize);

  // === 事件处理 ===

  const handleSort = useCallback(
    (columnId: string) => {
      if (!globalSortable) return;

      const column = columns.find((col) => col.id === columnId);
      if (!column?.sortable) return;

      let newDirection: SortDirection = 'asc';
      if (sorting.columnId === columnId) {
        if (sorting.direction === 'asc') {
          newDirection = 'desc';
        } else if (sorting.direction === 'desc') {
          newDirection = null;
        }
      }

      const newSorting: SortingState = {
        columnId: newDirection ? columnId : '',
        direction: newDirection,
      };

      if (onSortingChange) {
        onSortingChange(newSorting);
      } else {
        setInternalSorting(newSorting);
      }
    },
    [sorting, columns, globalSortable, onSortingChange]
  );

  const handlePageChange = useCallback(
    (newPageIndex: number) => {
      const newPagination = {
        ...paginationState,
        pageIndex: newPageIndex,
      };
      if (onPaginationChange) {
        onPaginationChange(newPagination);
      } else {
        setInternalPagination(newPagination);
      }
    },
    [paginationState, onPaginationChange]
  );

  const handlePageSizeChange = useCallback(
    (newPageSize: number) => {
      const newPagination = {
        ...paginationState,
        pageSize: newPageSize,
        pageIndex: 0,
      };
      if (onPaginationChange) {
        onPaginationChange(newPagination);
      } else {
        setInternalPagination(newPagination);
      }
    },
    [paginationState, onPaginationChange]
  );

  // === 渲染辅助函数 ===

  const getCellValue = useCallback(
    (row: T, column: ColumnDef<T>) => {
      if (column.cell) {
        return column.cell(row);
      }
      if (column.accessorKey) {
        return String(row[column.accessorKey] ?? '');
      }
      return '';
    },
    []
  );

  const getRowKey = useCallback(
    (row: T, index: number) => {
      const keyValue = row[rowKey];
      return keyValue !== undefined ? String(keyValue) : `row-${index}`;
    },
    [rowKey]
  );

  const getRowClassName = useCallback(
    (row: T) => {
      if (typeof rowClassName === 'function') {
        return rowClassName(row);
      }
      return rowClassName || '';
    },
    [rowClassName]
  );

  const getAlignClass = (align?: 'left' | 'center' | 'right') => {
    switch (align) {
      case 'center':
        return 'text-center';
      case 'right':
        return 'text-right';
      default:
        return 'text-left';
    }
  };

  // 响应式列数
  const responsiveVisibleColumns = visibleColumns ?? columns.length;

  return (
    <div className={cn('space-y-4', containerClassName)}>
      {/* 表格工具栏 */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        {/* 左侧：搜索和筛选 */}
        {globalFilterable && (
          <div className="relative flex-1 max-w-sm">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-foreground-tertiary" />
            <Input
              type="text"
              value={globalFilter}
              onChange={(e) => setGlobalFilter(e.target.value)}
              placeholder={filterPlaceholder}
              className="pl-9"
            />
          </div>
        )}

        {/* 右侧：操作按钮 */}
        {headerActions && (
          <div className="flex items-center gap-2">{headerActions}</div>
        )}
      </div>

      {/* 表格 */}
      <div className={cn('rounded-lg border bg-surface overflow-hidden', className)}>
        <div className="overflow-x-auto">
          <Table>
            <TableHeader>
              <TableRow className="bg-secondary/50 hover:bg-secondary/50">
                {columns.slice(0, responsiveVisibleColumns).map((column) => (
                  <TableHead
                    key={column.id}
                    className={cn(
                      getAlignClass(column.align),
                      column.sortable && globalSortable && 'cursor-pointer select-none hover:bg-secondary',
                      dense ? 'h-9 px-3' : 'h-10 px-4'
                    )}
                    onClick={() => handleSort(column.id)}
                  >
                    <div className="flex items-center gap-2">
                      <span>{column.header}</span>
                      {column.sortable && globalSortable && (
                        <div className="flex flex-col">
                          <ChevronRight
                            className={cn(
                              'h-3 w-3 -rotate-45 -translate-y-0.5 transition-colors',
                              sorting.columnId === column.id && sorting.direction === 'asc'
                                ? 'text-primary'
                                : 'text-foreground-tertiary'
                            )}
                          />
                          <ChevronRight
                            className={cn(
                              'h-3 w-3 rotate-45 -translate-y-1.5 transition-colors',
                              sorting.columnId === column.id && sorting.direction === 'desc'
                                ? 'text-primary'
                                : 'text-foreground-tertiary'
                            )}
                          />
                        </div>
                      )}
                    </div>
                  </TableHead>
                ))}
              </TableRow>
            </TableHeader>
            <TableBody>
              {loading ? (
                <TableRow>
                  <TableCell
                    colSpan={columns.length}
                    className="h-32 text-center text-foreground-secondary"
                  >
                    <div className="flex flex-col items-center justify-center gap-2">
                      <Loader2 className="h-5 w-5 animate-spin text-primary" />
                      <span className="text-sm">{loadingText}</span>
                    </div>
                  </TableCell>
                </TableRow>
              ) : paginatedData.length === 0 ? (
                <TableRow>
                  <TableCell
                    colSpan={columns.length}
                    className="h-32 text-center text-foreground-secondary"
                  >
                    <div className="flex flex-col items-center justify-center gap-2">
                      <SlidersHorizontal className="h-8 w-8 text-foreground-tertiary" />
                      <span className="text-sm">{emptyText}</span>
                    </div>
                  </TableCell>
                </TableRow>
              ) : (
                paginatedData.map((row, rowIndex) => (
                  <TableRow
                    key={getRowKey(row, rowIndex)}
                    className={cn(
                      onRowClick && 'cursor-pointer',
                      striped && rowIndex % 2 === 0 && 'bg-surface-alt/30',
                      getRowClassName(row)
                    )}
                    onClick={() => onRowClick?.(row)}
                  >
                    {columns.slice(0, responsiveVisibleColumns).map((column) => (
                      <TableCell
                        key={column.id}
                        className={cn(
                          getAlignClass(column.align),
                          typeof column.cellClassName === 'function'
                            ? column.cellClassName(row)
                            : column.cellClassName,
                          dense ? 'py-2 px-3' : 'p-4'
                        )}
                      >
                        {getCellValue(row, column)}
                      </TableCell>
                    ))}
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </div>
      </div>

      {/* 分页控件 */}
      {pagination && totalPages > 1 && (
        <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
          {/* 分页信息 */}
          <div className="text-sm text-foreground-secondary">
            {totalCount !== undefined
              ? `第 ${paginationState.pageIndex * paginationState.pageSize + 1} - ${Math.min(
                  (paginationState.pageIndex + 1) * paginationState.pageSize,
                  totalCount
                )} 条，共 ${totalCount} 条`
              : `第 ${paginationState.pageIndex * paginationState.pageSize + 1} - ${Math.min(
                  (paginationState.pageIndex + 1) * paginationState.pageSize,
                  processedData.length
                )} 条，共 ${processedData.length} 条`}
          </div>

          {/* 分页按钮 */}
          <div className="flex items-center gap-2">
            {/* 每页显示数量 */}
            <select
              value={paginationState.pageSize}
              onChange={(e) => handlePageSizeChange(Number(e.target.value))}
              className="h-8 rounded-md border border-border bg-surface px-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
            >
              <option value={5}>5 条/页</option>
              <option value={10}>10 条/页</option>
              <option value={20}>20 条/页</option>
              <option value={50}>50 条/页</option>
            </select>

            <div className="flex items-center gap-1">
              <Button
                variant="outline"
                size="icon"
                className="h-8 w-8"
                onClick={() => handlePageChange(0)}
                disabled={paginationState.pageIndex === 0}
              >
                <ChevronsLeft className="h-4 w-4" />
              </Button>
              <Button
                variant="outline"
                size="icon"
                className="h-8 w-8"
                onClick={() => handlePageChange(paginationState.pageIndex - 1)}
                disabled={paginationState.pageIndex === 0}
              >
                <ChevronLeft className="h-4 w-4" />
              </Button>

              {/* 页码 */}
              <div className="flex items-center gap-1">
                {Array.from({ length: Math.min(5, totalPages) }).map((_, i) => {
                  let pageNum;
                  if (totalPages <= 5) {
                    pageNum = i;
                  } else if (paginationState.pageIndex < 3) {
                    pageNum = i;
                  } else if (paginationState.pageIndex >= totalPages - 3) {
                    pageNum = totalPages - 5 + i;
                  } else {
                    pageNum = paginationState.pageIndex - 2 + i;
                  }

                  return (
                    <Button
                      key={pageNum}
                      variant={paginationState.pageIndex === pageNum ? 'default' : 'outline'}
                      size="icon"
                      className="h-8 w-8"
                      onClick={() => handlePageChange(pageNum)}
                    >
                      {pageNum + 1}
                    </Button>
                  );
                })}
              </div>

              <Button
                variant="outline"
                size="icon"
                className="h-8 w-8"
                onClick={() => handlePageChange(paginationState.pageIndex + 1)}
                disabled={paginationState.pageIndex >= totalPages - 1}
              >
                <ChevronRight className="h-4 w-4" />
              </Button>
              <Button
                variant="outline"
                size="icon"
                className="h-8 w-8"
                onClick={() => handlePageChange(totalPages - 1)}
                disabled={paginationState.pageIndex >= totalPages - 1}
              >
                <ChevronsRight className="h-4 w-4" />
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

/**
 * DataTableColumnHeader - 表格列头部组件
 *
 * 用于自定义表格列头部
 */
export interface DataTableColumnHeaderProps<T> {
  column: ColumnDef<T>;
  sorting?: SortingState;
  onSort?: (columnId: string) => void;
}

export function DataTableColumnHeader<T>({
  column,
  sorting,
  onSort,
}: DataTableColumnHeaderProps<T>) {
  const isSortable = column.sortable;
  const isSorted = sorting?.columnId === column.id;
  const sortDirection = sorting?.direction;

  return (
    <div
      className={cn(
        'flex items-center gap-2',
        isSortable && onSort && 'cursor-pointer select-none'
      )}
      onClick={() => isSortable && onSort?.(column.id)}
    >
      <span>{column.header}</span>
      {isSortable && (
        <div className="flex flex-col">
          <ChevronRight
            className={cn(
              'h-3 w-3 -rotate-45 -translate-y-0.5 transition-colors',
              isSorted && sortDirection === 'asc'
                ? 'text-primary'
                : 'text-foreground-tertiary'
            )}
          />
          <ChevronRight
            className={cn(
              'h-3 w-3 rotate-45 -translate-y-1.5 transition-colors',
              isSorted && sortDirection === 'desc'
                ? 'text-primary'
                : 'text-foreground-tertiary'
            )}
          />
        </div>
      )}
    </div>
  );
}
