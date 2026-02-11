import { type ReactNode } from 'react';
import { Link } from 'react-router-dom';
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import { ArrowLeft, ChevronRight, Plus } from 'lucide-react';

/**
 * 面包屑项
 */
export interface BreadcrumbItem {
  /** 标签 */
  label: string;
  /** 链接地址（可选，最后一项通常不设置） */
  href?: string;
}

/**
 * PageHeader - 页面头部组件
 *
 * 统一的页面头部布局，包含标题、操作按钮、面包屑等
 *
 * @example
 * ```tsx
 * <PageHeader
 *   title="患者管理"
 *   description="管理和查看所有患者信息"
 *   breadcrumbs={[
 *     { label: '首页', href: '/' },
 *     { label: '医生工作台', href: '/doctor' },
 *     { label: '患者管理' },
 *   ]}
 *   actions={<Button>新增患者</Button>}
 * />
 * ```
 */
export interface PageHeaderProps {
  /** 页面标题 */
  title: string;
  /** 页面描述 */
  description?: string;
  /** 操作按钮区域 */
  actions?: ReactNode;
  /** 是否显示返回按钮 */
  showBack?: boolean;
  /** 返回按钮点击事件 */
  onBack?: () => void;
  /** 额外类名 */
  className?: string;
  /** 标签区域（放在标题下方） */
  tags?: ReactNode;
  /** 面包屑导航 */
  breadcrumbs?: BreadcrumbItem[];
}

export function PageHeader({
  title,
  description,
  actions,
  showBack = false,
  onBack,
  className,
  tags,
  breadcrumbs,
}: PageHeaderProps) {
  return (
    <div className={cn('mb-6', className)}>
      {/* 面包屑导航 */}
      {breadcrumbs && breadcrumbs.length > 0 && (
        <nav className="flex items-center gap-1 text-sm mb-3">
          {breadcrumbs.map((item, index) => (
            <div key={index} className="flex items-center gap-1">
              {index > 0 && (
                <ChevronRight className="h-4 w-4 text-foreground-tertiary" />
              )}
              {item.href ? (
                <Link
                  to={item.href}
                  className="text-foreground-secondary hover:text-foreground transition-colors"
                >
                  {item.label}
                </Link>
              ) : (
                <span className="text-foreground">{item.label}</span>
              )}
            </div>
          ))}
        </nav>
      )}

      <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-4">
        {/* 左侧：标题区域 */}
        <div className="space-y-1">
          {/* 标题 + 返回按钮 */}
          <div className="flex items-center gap-3">
            {showBack && (
              <Button
                variant="ghost"
                size="icon"
                onClick={onBack}
                className="h-7 w-7"
              >
                <ArrowLeft className="h-4 w-4" />
              </Button>
            )}
            <h1 className="text-xl font-semibold text-foreground">{title}</h1>
          </div>

          {/* 描述 */}
          {description && (
            <p className="text-sm text-foreground-secondary">{description}</p>
          )}

          {/* 标签 */}
          {tags && <div className="flex items-center gap-2 mt-2">{tags}</div>}
        </div>

        {/* 右侧：操作按钮 */}
        {actions && <div className="flex items-center gap-2">{actions}</div>}
      </div>
    </div>
  );
}

/**
 * PageHeaderActions - 页面头部操作按钮容器
 *
 * 用于包裹多个操作按钮
 */
export interface PageHeaderActionsProps {
  children: ReactNode;
  /** 额外类名 */
  className?: string;
}

export function PageHeaderActions({ children, className }: PageHeaderActionsProps) {
  return (
    <div className={cn('flex items-center gap-2', className)}>
      {children}
    </div>
  );
}

/**
 * PageHeader - 快速创建带新增按钮的页面头部
 */
export interface PageHeaderWithCreateProps extends Omit<PageHeaderProps, 'actions'> {
  /** 新增按钮文本 */
  createText?: string;
  /** 新增按钮点击事件 */
  onCreate?: () => void;
  /** 是否禁用新增按钮 */
  createDisabled?: boolean;
  /** 新增按钮图标 */
  createIcon?: ReactNode;
}

export function PageHeaderWithCreate({
  createText = '新增',
  onCreate,
  createDisabled = false,
  createIcon = <Plus className="h-4 w-4" />,
  ...props
}: PageHeaderWithCreateProps) {
  return (
    <PageHeader
      {...props}
      actions={
        onCreate && (
          <Button onClick={onCreate} disabled={createDisabled}>
            {createIcon}
            {createText}
          </Button>
        )
      }
    />
  );
}
