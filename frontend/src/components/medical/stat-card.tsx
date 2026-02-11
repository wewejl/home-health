import { type ReactNode } from 'react';
import { Card } from '@/components/ui/card';
import { cn } from '@/lib/utils';

/**
 * StatCard - 统计卡片组件
 *
 * 用于替代 Ant Design 的 Statistic 组件
 *
 * @example
 * ```tsx
 * <StatCard
 *   title="患者总数"
 *   value={1234}
 *   icon={<Users className="h-5 w-5" />}
 *   trend="+12%"
 *   trendUp
 * />
 * ```
 */
export interface StatCardProps {
  /** 卡片标题 */
  title: string;
  /** 数值 */
  value: number | string;
  /** 单位 */
  unit?: string;
  /** 图标 */
  icon?: ReactNode;
  /** 趋势值 */
  trend?: string;
  /** 趋势是否向上（绿色表示正面，红色表示负面） */
  trendUp?: boolean;
  /** 颜色主题 */
  variant?: 'primary' | 'success' | 'warning' | 'danger' | 'info';
  /** 额外类名 */
  className?: string;
  /** 点击事件 */
  onClick?: () => void;
}

const variantColors = {
  primary: 'text-primary',
  success: 'text-success',
  warning: 'text-warning',
  danger: 'text-danger',
  info: 'text-info',
};

const variantBgLight = {
  primary: 'bg-primary/10',
  success: 'bg-success/10',
  warning: 'bg-warning/10',
  danger: 'bg-danger/10',
  info: 'bg-info/10',
};

export function StatCard({
  title,
  value,
  unit,
  icon,
  trend,
  trendUp = true,
  variant = 'primary',
  className,
  onClick,
}: StatCardProps) {
  const clickable = !!onClick;

  return (
    <Card
      className={cn(
        'stat-card group relative overflow-hidden',
        clickable && 'cursor-pointer hover:shadow-md',
        className
      )}
      onClick={onClick}
    >
      {/* 装饰背景 */}
      <div
        className={cn(
          'absolute right-0 top-0 h-24 w-24 -translate-y-1/2 translate-x-1/2 rounded-full opacity-10 blur-2xl',
          variantBgLight[variant]
        )}
      />

      <div className="relative">
        {/* 标题行 */}
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-sm font-medium text-muted-foreground">{title}</h3>
          {icon && (
            <div className={cn('rounded-lg p-2', variantBgLight[variant])}>
              <div className={cn('h-4 w-4', variantColors[variant])}>{icon}</div>
            </div>
          )}
        </div>

        {/* 数值 */}
        <div className="flex items-baseline gap-2">
          <span className="text-2xl font-semibold text-foreground">
            {typeof value === 'number' ? value.toLocaleString() : value}
          </span>

          {/* 单位 */}
          {unit && (
            <span className="text-sm text-foreground-secondary">{unit}</span>
          )}

          {/* 趋势标签 */}
          {trend && (
            <span
              className={cn(
                'text-xs font-medium',
                trendUp ? 'text-success' : 'text-danger'
              )}
            >
              {trend}
            </span>
          )}
        </div>
      </div>
    </Card>
  );
}

/**
 * StatCardGrid - 统计卡片网格
 *
 * 快速创建统计卡片的网格布局
 */
export interface StatCardGridProps {
  /** 统计卡片数据 */
  items: Omit<StatCardProps, 'className'>[];
  /** 每行显示的卡片数量（响应式） */
  cols?: 1 | 2 | 3 | 4;
  /** 卡片之间的间距 */
  gap?: string;
  /** 额外类名 */
  className?: string;
}

export function StatCardGrid({
  items,
  cols = 4,
  gap = 'gap-4',
  className,
}: StatCardGridProps) {
  const gridCols = {
    1: 'grid-cols-1',
    2: 'grid-cols-1 md:grid-cols-2',
    3: 'grid-cols-1 md:grid-cols-2 lg:grid-cols-3',
    4: 'grid-cols-1 sm:grid-cols-2 lg:grid-cols-4',
  };

  return (
    <div className={cn('grid', gridCols[cols], gap, className)}>
      {items.map((item, index) => (
        <StatCard key={index} {...item} />
      ))}
    </div>
  );
}
