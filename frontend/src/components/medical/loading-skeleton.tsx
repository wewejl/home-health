import { cn } from '@/lib/utils';
import { Card } from '@/components/ui/card';

/**
 * LoadingSkeleton - 加载骨架屏组件
 *
 * 用于替代 Ant Design 的 Spin 组件
 * 提供更好的用户体验，减少内容跳动
 *
 * @example
 * ```tsx
 * <LoadingSkeleton />
 * <LoadingSkeleton variant="card" />
 * <LoadingSkeleton variant="table" rows={5} />
 * <PatientCardSkeleton />
 * <ConsultationSkeleton />
 * <OrdersTableSkeleton />
 * ```
 */
export interface LoadingSkeletonProps {
  /** 骨架屏变体 */
  variant?: 'default' | 'card' | 'table' | 'list' | 'text';
  /** 表格行数（仅 table 模式） */
  rows?: number;
  /** 表格列数（仅 table 模式） */
  cols?: number;
  /** 额外类名 */
  className?: string;
}

function SkeletonLine({ className }: { className?: string }) {
  return (
    <div
      className={cn(
        'h-4 rounded bg-surface-alt animate-pulse',
        'bg-gradient-to-r from-surface-alt via-secondary to-surface-alt',
        'bg-[length:200%_100%]',
        'animate-shimmer',
        className
      )}
      style={{
        animation: 'shimmer 1.5s infinite',
      }}
    />
  );
}

function SkeletonCircle({ size = 'md' }: { size?: 'sm' | 'md' | 'lg' }) {
  const sizes = {
    sm: 'h-8 w-8',
    md: 'h-12 w-12',
    lg: 'h-16 w-16',
  };

  return (
    <div
      className={cn(
        'rounded-full bg-surface-alt animate-pulse',
        sizes[size],
        'bg-gradient-to-r from-surface-alt via-secondary to-surface-alt'
      )}
      style={{
        animation: 'shimmer 1.5s infinite',
      }}
    />
  );
}

export function LoadingSkeleton({
  variant = 'default',
  rows = 5,
  cols = 4,
  className,
}: LoadingSkeletonProps) {
  // 默认：单行骨架
  if (variant === 'default') {
    return (
      <div className={cn('space-y-3 p-6', className)}>
        <SkeletonLine className="w-3/4 h-5" />
        <SkeletonLine className="w-1/2" />
        <SkeletonLine className="w-5/6" />
      </div>
    );
  }

  // 卡片骨架
  if (variant === 'card') {
    return (
      <div className={cn('p-6 space-y-4', className)}>
        <div className="flex items-center justify-between">
          <SkeletonLine className="w-32 h-5" />
          <SkeletonCircle size="sm" />
        </div>
        <SkeletonLine className="w-full h-8" />
        <SkeletonLine className="w-2/3" />
      </div>
    );
  }

  // 表格骨架
  if (variant === 'table') {
    return (
      <div className={cn('p-4', className)}>
        {/* 表头 */}
        <div className="flex gap-4 mb-4 pb-2 border-b">
          {Array.from({ length: cols }).map((_, i) => (
            <SkeletonLine key={`header-${i}`} className="flex-1 h-4" />
          ))}
        </div>
        {/* 表格行 */}
        <div className="space-y-3">
          {Array.from({ length: rows }).map((_, i) => (
            <div key={`row-${i}`} className="flex gap-4">
              {Array.from({ length: cols }).map((_, j) => (
                <SkeletonLine key={`cell-${i}-${j}`} className="flex-1 h-4" />
              ))}
            </div>
          ))}
        </div>
      </div>
    );
  }

  // 列表骨架
  if (variant === 'list') {
    return (
      <div className={cn('space-y-4', className)}>
        {Array.from({ length: rows }).map((_, i) => (
          <div key={i} className="flex items-center gap-4 p-4 border rounded-lg">
            <SkeletonCircle size="md" />
            <div className="flex-1 space-y-2">
              <SkeletonLine className="w-48 h-5" />
              <SkeletonLine className="w-32 h-4" />
            </div>
          </div>
        ))}
      </div>
    );
  }

  // 文本骨架
  if (variant === 'text') {
    return (
      <div className={cn('space-y-2', className)}>
        <SkeletonLine className="w-full" />
        <SkeletonLine className="w-5/6" />
        <SkeletonLine className="w-4/6" />
      </div>
    );
  }

  return null;
}

/**
 * LoadingOverlay - 全屏加载遮罩
 *
 * 用于全屏内容的加载状态
 */
export interface LoadingOverlayProps {
  /** 加载文本 */
  text?: string;
  /** 额外类名 */
  className?: string;
}

export function LoadingOverlay({ text = '加载中...', className }: LoadingOverlayProps) {
  return (
    <div
      className={cn(
        'flex flex-col items-center justify-center py-12 text-foreground-secondary',
        className
      )}
    >
      {/* 加载动画 */}
      <div className="relative mb-4">
        <div className="h-12 w-12 rounded-full border-4 border-border border-t-primary animate-spin" />
      </div>
      {/* 加载文本 */}
      <p className="text-sm">{text}</p>
    </div>
  );
}

/**
 * InlineLoading - 行内加载状态
 *
 * 用于表格单元格、卡片等小区域的加载状态
 */
export interface InlineLoadingProps {
  /** 尺寸 */
  size?: 'sm' | 'md';
  /** 额外类名 */
  className?: string;
}

export function InlineLoading({ size = 'sm', className }: InlineLoadingProps) {
  const sizes = {
    sm: 'h-4 w-4 border-2',
    md: 'h-6 w-6 border-2',
  };

  return (
    <div className={cn('flex items-center justify-center', className)}>
      <div className={cn('rounded-full border-border border-t-primary animate-spin', sizes[size])} />
    </div>
  );
}

// 添加 shimmer 动画到全局样式
// 在 index.css 中添加：
// @keyframes shimmer {
//   0% { background-position: -200% 0; }
//   100% { background-position: 200% 0; }
// }

/**
 * PatientCardSkeleton - 患者卡片骨架屏
 *
 * 模拟 PatientCard 组件的布局结构
 */
export function PatientCardSkeleton({ count = 4 }: { count?: number }) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
      {Array.from({ length: count }).map((_, i) => (
        <Card key={i} className="overflow-hidden">
          <div className="p-5 space-y-4">
            {/* 头部：头像和基本信息 */}
            <div className="flex items-start gap-4 mb-4">
              {/* 头像圆形骨架 */}
              <div className="w-14 h-14 rounded-full bg-muted animate-pulse flex-shrink-0" />
              {/* 姓名和性别 */}
              <div className="flex-1 min-w-0 space-y-2">
                <div className="flex items-center gap-2">
                  <div className="h-5 w-24 bg-muted animate-pulse rounded" />
                  <div className="h-5 w-10 bg-muted animate-pulse rounded" />
                </div>
                <div className="flex items-center gap-3">
                  <div className="h-4 w-12 bg-muted animate-pulse rounded" />
                  <div className="h-4 w-24 bg-muted animate-pulse rounded" />
                </div>
              </div>
            </div>

            {/* 医嘱数量和完成率 */}
            <div className="space-y-3">
              {/* 医嘱数量 */}
              <div className="flex items-center justify-between">
                <div className="h-4 w-20 bg-muted animate-pulse rounded" />
                <div className="h-6 w-8 bg-muted animate-pulse rounded" />
              </div>

              {/* 完成率进度条 */}
              <div>
                <div className="flex items-center justify-between mb-1">
                  <div className="h-4 w-16 bg-muted animate-pulse rounded" />
                  <div className="h-4 w-10 bg-muted animate-pulse rounded" />
                </div>
                <div className="h-2 w-full bg-muted rounded-full overflow-hidden">
                  <div className="h-full w-2/3 bg-muted/50 animate-pulse" />
                </div>
              </div>
            </div>

            {/* 最后咨询时间 */}
            <div className="mt-4 pt-3 border-t border-border/50">
              <div className="flex items-center justify-between">
                <div className="h-3 w-16 bg-muted animate-pulse rounded" />
                <div className="h-3 w-16 bg-muted animate-pulse rounded" />
              </div>
            </div>
          </div>
        </Card>
      ))}
    </div>
  );
}

/**
 * ConsultationSkeleton - 对话界面骨架屏
 *
 * 模拟 ConsultationsTab 的布局结构
 */
export function ConsultationSkeleton() {
  return (
    <div className="p-4">
      <div className="flex gap-4 h-[calc(100vh-300px)]">
        {/* 会话列表骨架 */}
        <Card className="w-[350px] overflow-hidden flex flex-col">
          <div className="p-4 pb-3 border-b">
            <div className="h-5 w-24 bg-muted animate-pulse rounded" />
          </div>
          <div className="p-4 space-y-4 overflow-auto flex-1">
            {Array.from({ length: 4 }).map((_, i) => (
              <div key={i} className="flex items-start gap-3 p-4 border rounded-lg">
                <div className="h-5 w-5 bg-muted animate-pulse rounded mt-0.5" />
                <div className="flex-1 min-w-0 space-y-2">
                  <div className="flex items-center justify-between">
                    <div className="h-4 w-20 bg-muted animate-pulse rounded" />
                    <div className="h-5 w-10 bg-muted animate-pulse rounded" />
                  </div>
                  <div className="h-4 w-full bg-muted animate-pulse rounded" />
                  <div className="flex items-center gap-1">
                    <div className="h-3 w-3 bg-muted animate-pulse rounded" />
                    <div className="h-3 w-24 bg-muted animate-pulse rounded" />
                  </div>
                </div>
              </div>
            ))}
          </div>
        </Card>

        {/* 消息详情骨架 */}
        <Card className="flex-1 overflow-hidden flex flex-col">
          <div className="p-4 pb-3 border-b">
            <div className="h-5 w-28 bg-muted animate-pulse rounded" />
          </div>
          <div className="p-4 space-y-4 overflow-auto flex-1">
            {/* 会话信息骨架 */}
            <div className="p-3 bg-muted/50 rounded-lg">
              <div className="h-4 w-48 bg-muted animate-pulse rounded" />
            </div>

            {/* 消息列表骨架 */}
            {Array.from({ length: 3 }).map((_, i) => (
              <div key={i} className="p-3 rounded-lg border-l-4 bg-muted/30">
                <div className="h-5 w-16 bg-muted animate-pulse rounded mb-2" />
                <div className="space-y-2">
                  <div className="h-4 w-full bg-muted animate-pulse rounded" />
                  <div className="h-4 w-4/5 bg-muted animate-pulse rounded" />
                </div>
                <div className="h-3 w-32 bg-muted animate-pulse rounded mt-2" />
              </div>
            ))}
          </div>
        </Card>
      </div>
    </div>
  );
}

/**
 * OrdersTableSkeleton - 医嘱表格骨架屏
 *
 * 模拟 OrdersTab 的表格布局结构
 */
export function OrdersTableSkeleton({ rows = 5, cols = 8 }: { rows?: number; cols?: number }) {
  return (
    <div className="p-4">
      {/* 标题栏骨架 */}
      <div className="flex justify-between items-center mb-4">
        <div className="h-6 w-24 bg-muted animate-pulse rounded" />
        <div className="h-9 w-24 bg-muted animate-pulse rounded" />
      </div>

      {/* 表格骨架 */}
      <Card>
        <div className="w-full overflow-auto">
          {/* 表头 */}
          <div className="flex gap-4 p-4 border-b bg-muted/30">
            {Array.from({ length: cols }).map((_, i) => (
              <div
                key={`header-${i}`}
                className={cn(
                  'h-4 bg-muted animate-pulse rounded',
                  i === 0 ? 'w-[60px]' : '',
                  i === 1 ? 'w-[120px]' : '',
                  i === 4 || i === 5 ? 'w-[120px]' : '',
                  i === 6 ? 'w-[100px]' : '',
                  i === 7 ? 'w-[180px]' : '',
                  i === 2 || i === 3 ? 'flex-1' : ''
                )}
              />
            ))}
          </div>

          {/* 表格行 */}
          <div className="divide-y">
            {Array.from({ length: rows }).map((_, rowIndex) => (
              <div key={`row-${rowIndex}`} className="flex gap-4 p-4">
                {Array.from({ length: cols }).map((_, colIndex) => (
                  <div
                    key={`cell-${rowIndex}-${colIndex}`}
                    className={cn(
                      'h-4 bg-muted animate-pulse rounded',
                      colIndex === 0 ? 'w-[60px]' : '',
                      colIndex === 1 ? 'w-[120px]' : '',
                      colIndex === 4 || colIndex === 5 ? 'w-[120px]' : '',
                      colIndex === 6 ? 'w-[100px]' : '',
                      colIndex === 7 ? 'w-[180px]' : '',
                      colIndex === 2 || colIndex === 3 ? 'flex-1' : ''
                    )}
                  />
                ))}
              </div>
            ))}
          </div>
        </div>
      </Card>
    </div>
  );
}

/**
 * PatientDetailCardSkeleton - 患者详情卡片骨架屏
 *
 * 模拟 PatientDetail 页面顶部卡片布局
 */
export function PatientDetailCardSkeleton() {
  return (
    <>
      {/* 患者基本信息卡片骨架 */}
      <Card className="mb-4">
        <div className="p-6">
          <div className="flex flex-col md:flex-row gap-6">
            {/* 头像区域 */}
            <div className="flex-shrink-0 flex flex-col items-center">
              <div className="w-20 h-20 rounded-full bg-muted animate-pulse mb-3" />
              <div className="h-5 w-24 bg-muted animate-pulse rounded mb-2" />
              <div className="h-4 w-28 bg-muted animate-pulse rounded" />
            </div>

            {/* 详细信息 */}
            <div className="flex-1">
              <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                {Array.from({ length: 6 }).map((_, i) => (
                  <div key={i} className="flex items-center justify-between p-3 rounded-lg bg-muted/50">
                    <div className="h-4 w-16 bg-muted/50 animate-pulse rounded" />
                    <div className="h-5 w-12 bg-muted animate-pulse rounded" />
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </Card>

      {/* 统计卡片骨架 */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
        {Array.from({ length: 3 }).map((_, i) => (
          <Card key={i} className="stat-card">
            <div className="p-5">
              <div className="h-3 w-20 bg-muted animate-pulse rounded mb-2" />
              <div className="h-8 w-16 bg-muted animate-pulse rounded" />
            </div>
          </Card>
        ))}
      </div>
    </>
  );
}
