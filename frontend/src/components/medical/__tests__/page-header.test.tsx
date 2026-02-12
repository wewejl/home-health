/**
 * PageHeader 组件测试
 *
 * 测试覆盖：
 * 1. 组件渲染测试
 * 2. Props 传递测试
 * 3. 用户交互测试（返回按钮、面包屑）
 * 4. 样式变化测试
 * 5. 边界条件测试
 */

import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import * as React from 'react';
import {
  PageHeader,
  PageHeaderActions,
  PageHeaderWithCreate,
  type BreadcrumbItem,
} from '../page-header';

// Mock Link component from react-router-dom
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual as any,
    Link: ({ children, to, ...props }: any) => (
      <a href={to} {...props}>
        {children}
      </a>
    ),
  };
});

describe('PageHeader Component', () => {
  describe('Rendering', () => {
    it('should render title', () => {
      render(<PageHeader title="患者管理" />);
      expect(screen.getByText('患者管理')).toBeInTheDocument();
    });

    it('should render description when provided', () => {
      render(
        <PageHeader
          title="患者管理"
          description="管理和查看所有患者信息"
        />
      );
      expect(screen.getByText('管理和查看所有患者信息')).toBeInTheDocument();
    });

    it('should not render description when not provided', () => {
      render(<PageHeader title="患者管理" />);
      const description = screen.queryByText('管理和查看所有患者信息');
      expect(description).not.toBeInTheDocument();
    });

    it('should render actions when provided', () => {
      render(
        <PageHeader
          title="患者管理"
          actions={<button data-testid="action-btn">操作</button>}
        />
      );
      expect(screen.getByTestId('action-btn')).toBeInTheDocument();
    });

    it('should render back button when showBack is true', () => {
      render(<PageHeader title="患者管理" showBack />);
      const backIcon = screen.getByRole('button');
      expect(backIcon).toBeInTheDocument();
    });

    it('should not render back button when showBack is false', () => {
      render(<PageHeader title="患者管理" showBack={false} />);
      const backIcon = screen.queryByRole('button');
      expect(backIcon).not.toBeInTheDocument();
    });

    it('should render tags when provided', () => {
      render(
        <PageHeader
          title="患者管理"
          tags={<span data-testid="tag">活跃</span>}
        />
      );
      expect(screen.getByTestId('tag')).toBeInTheDocument();
    });
  });

  describe('Breadcrumbs', () => {
    it('should render breadcrumbs when provided', () => {
      const breadcrumbs: BreadcrumbItem[] = [
        { label: '首页', href: '/' },
        { label: '医生工作台', href: '/doctor' },
        { label: '患者管理' },
      ];

      render(<PageHeader title="患者管理" breadcrumbs={breadcrumbs} />);

      expect(screen.getByText('首页')).toBeInTheDocument();
      expect(screen.getByText('医生工作台')).toBeInTheDocument();
      expect(screen.getByText('患者管理')).toBeInTheDocument();
    });

    it('should render breadcrumbs as links when href is provided', () => {
      const breadcrumbs: BreadcrumbItem[] = [
        { label: '首页', href: '/' },
        { label: '患者管理' },
      ];

      render(<PageHeader title="患者管理" breadcrumbs={breadcrumbs} />);

      const homeLink = screen.getByText('首页').closest('a');
      expect(homeLink).toHaveAttribute('href', '/');
    });

    it('should render last breadcrumb as span without link', () => {
      const breadcrumbs: BreadcrumbItem[] = [
        { label: '首页', href: '/' },
        { label: '患者管理' },
      ];

      render(<PageHeader title="患者管理" breadcrumbs={breadcrumbs} />);

      const patientManagement = screen.getByText('患者管理');
      expect(patientManagement.tagName).toBe('SPAN');
    });

    it('should not render breadcrumbs when array is empty', () => {
      render(<PageHeader title="患者管理" breadcrumbs={[]} />);
      expect(screen.queryByText('首页')).not.toBeInTheDocument();
    });

    it('should render chevron separators between breadcrumbs', () => {
      const breadcrumbs: BreadcrumbItem[] = [
        { label: '首页', href: '/' },
        { label: '医生工作台', href: '/doctor' },
        { label: '患者管理' },
      ];

      const { container } = render(
        <PageHeader title="患者管理" breadcrumbs={breadcrumbs} />
      );

      const chevrons = container.querySelectorAll('.lucide-chevron-right');
      // Should have 2 chevrons for 3 items
      expect(chevrons.length).toBe(2);
    });
  });

  describe('User Interactions', () => {
    it('should call onBack when back button is clicked', async () => {
      const user = userEvent.setup();
      const onBack = vi.fn();

      render(<PageHeader title="患者管理" showBack onBack={onBack} />);

      const backButton = screen.getByRole('button');
      await user.click(backButton);

      expect(onBack).toHaveBeenCalledTimes(1);
    });

    it('should render clickable breadcrumbs', () => {
      const breadcrumbs: BreadcrumbItem[] = [
        { label: '首页', href: '/' },
        { label: '患者管理' },
      ];

      render(<PageHeader title="患者管理" breadcrumbs={breadcrumbs} />);

      const homeLink = screen.getByText('首页').closest('a');
      expect(homeLink).toHaveAttribute('href', '/');
    });
  });

  describe('Custom Classes', () => {
    it('should apply custom className to container', () => {
      const { container } = render(
        <PageHeader title="患者管理" className="custom-class" />
      );

      const headerContainer = container.firstChild;
      expect(headerContainer).toHaveClass('custom-class');
    });

    it('should apply default mb-6 class', () => {
      const { container } = render(<PageHeader title="患者管理" />);

      const headerContainer = container.firstChild;
      expect(headerContainer).toHaveClass('mb-6');
    });
  });

  describe('Layout', () => {
    it('should render title and actions in separate sections', () => {
      render(
        <PageHeader
          title="患者管理"
          actions={<button data-testid="action">操作</button>}
        />
      );

      expect(screen.getByText('患者管理')).toBeInTheDocument();
      expect(screen.getByTestId('action')).toBeInTheDocument();
    });

    it('should render description below title', () => {
      const { container } = render(
        <PageHeader
          title="患者管理"
          description="管理和查看所有患者信息"
        />
      );

      const titleElement = screen.getByText('患者管理');
      const descriptionElement = screen.getByText('管理和查看所有患者信息');

      const titleParent = titleElement.parentElement;
      const descriptionParent = descriptionElement.parentElement;

      // Title and description should be in same container
      expect(titleParent).toBe(descriptionParent);
    });
  });

  describe('Accessibility', () => {
    it('should have proper heading structure', () => {
      render(<PageHeader title="患者管理" />);

      const heading = screen.getByRole('heading', { level: 1 });
      expect(heading).toBeInTheDocument();
      expect(heading).toHaveTextContent('患者管理');
    });

    it('should have accessible back button', () => {
      render(<PageHeader title="患者管理" showBack />);

      const backButton = screen.getByRole('button');
      expect(backButton).toBeInTheDocument();
    });
  });
});

describe('PageHeaderActions Component', () => {
  it('should render children', () => {
    render(
      <PageHeaderActions>
        <button data-testid="btn1">按钮1</button>
        <button data-testid="btn2">按钮2</button>
      </PageHeaderActions>
    );

    expect(screen.getByTestId('btn1')).toBeInTheDocument();
    expect(screen.getByTestId('btn2')).toBeInTheDocument();
  });

  it('should apply custom className', () => {
    const { container } = render(
      <PageHeaderActions className="custom-class">
        <button>按钮</button>
      </PageHeaderActions>
    );

    const actionsContainer = container.firstChild;
    expect(actionsContainer).toHaveClass('custom-class');
  });

  it('should apply flex layout classes by default', () => {
    const { container } = render(
      <PageHeaderActions>
        <button>按钮</button>
      </PageHeaderActions>
    );

    const actionsContainer = container.firstChild as HTMLElement;
    expect(actionsContainer).toHaveClass('flex');
    expect(actionsContainer).toHaveClass('items-center');
    expect(actionsContainer).toHaveClass('gap-2');
  });
});

describe('PageHeaderWithCreate Component', () => {
  it('should render title and create button', () => {
    const onCreate = vi.fn();
    render(
      <PageHeaderWithCreate title="患者管理" onCreate={onCreate} />
    );

    expect(screen.getByText('患者管理')).toBeInTheDocument();
    expect(screen.getByText('新增')).toBeInTheDocument();
  });

  it('should call onCreate when create button is clicked', async () => {
    const user = userEvent.setup();
    const onCreate = vi.fn();

    render(<PageHeaderWithCreate title="患者管理" onCreate={onCreate} />);

    const createButton = screen.getByText('新增');
    await user.click(createButton);

    expect(onCreate).toHaveBeenCalledTimes(1);
  });

  it('should render custom create text', () => {
    render(
      <PageHeaderWithCreate
        title="患者管理"
        createText="添加患者"
        onCreate={vi.fn()}
      />
    );

    expect(screen.getByText('添加患者')).toBeInTheDocument();
    expect(screen.queryByText('新增')).not.toBeInTheDocument();
  });

  it('should disable create button when createDisabled is true', () => {
    render(
      <PageHeaderWithCreate
        title="患者管理"
        onCreate={vi.fn()}
        createDisabled
      />
    );

    const createButton = screen.getByRole('button', { name: /新增/ });
    expect(createButton).toBeDisabled();
  });

  it('should not render create button when onCreate is not provided', () => {
    render(<PageHeaderWithCreate title="患者管理" />);

    const createButton = screen.queryByText('新增');
    expect(createButton).not.toBeInTheDocument();
  });

  it('should pass other props to PageHeader', () => {
    render(
      <PageHeaderWithCreate
        title="患者管理"
        description="管理和查看所有患者信息"
        onCreate={vi.fn()}
      />
    );

    expect(screen.getByText('管理和查看所有患者信息')).toBeInTheDocument();
  });

  it('should render custom create icon', () => {
    render(
      <PageHeaderWithCreate
        title="患者管理"
        onCreate={vi.fn()}
        createIcon={<span data-testid="custom-icon">+</span>}
      />
    );

    expect(screen.getByTestId('custom-icon')).toBeInTheDocument();
  });
});

describe('PageHeader Edge Cases', () => {
  it('should handle empty title', () => {
    render(<PageHeader title="" />);
    const heading = screen.getByRole('heading');
    expect(heading).toBeInTheDocument();
    expect(heading).toHaveTextContent('');
  });

  it('should handle very long title', () => {
    const longTitle = '这是一个非常非常非常非常非常非常非常非常长的标题';
    render(<PageHeader title={longTitle} />);
    expect(screen.getByText(longTitle)).toBeInTheDocument();
  });

  it('should handle many breadcrumb items', () => {
    const breadcrumbs: BreadcrumbItem[] = [
      { label: '首页', href: '/' },
      { label: '医生工作台', href: '/doctor' },
      { label: '患者管理', href: '/patients' },
      { label: '详情', href: '/patients/1' },
      { label: '编辑' },
    ];

    render(<PageHeader title="编辑" breadcrumbs={breadcrumbs} />);

    expect(screen.getByText('首页')).toBeInTheDocument();
    expect(screen.getByText('医生工作台')).toBeInTheDocument();
    expect(screen.getByText('患者管理')).toBeInTheDocument();
    expect(screen.getByText('详情')).toBeInTheDocument();
    expect(screen.getByText('编辑')).toBeInTheDocument();
  });

  it('should handle null actions gracefully', () => {
    render(<PageHeader title="患者管理" actions={null as any} />);
    expect(screen.getByText('患者管理')).toBeInTheDocument();
  });

  it('should handle multiple actions', () => {
    render(
      <PageHeader
        title="患者管理"
        actions={
          <>
            <button data-testid="btn1">按钮1</button>
            <button data-testid="btn2">按钮2</button>
            <button data-testid="btn3">按钮3</button>
          </>
        }
      />
    );

    expect(screen.getByTestId('btn1')).toBeInTheDocument();
    expect(screen.getByTestId('btn2')).toBeInTheDocument();
    expect(screen.getByTestId('btn3')).toBeInTheDocument();
  });
});
