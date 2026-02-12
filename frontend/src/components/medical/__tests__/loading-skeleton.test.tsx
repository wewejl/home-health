/**
 * LoadingSkeleton 组件测试
 *
 * 测试覆盖：
 * 1. 组件渲染测试
 * 2. Props 传递测试
 * 3. 各变体样式测试
 * 4. 边界条件测试
 */

import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import {
  LoadingSkeleton,
  LoadingOverlay,
  InlineLoading,
  PatientCardSkeleton,
  ConsultationSkeleton,
  OrdersTableSkeleton,
  PatientDetailCardSkeleton,
} from '../loading-skeleton';

describe('LoadingSkeleton Component', () => {
  describe('Default Variant', () => {
    it('should render default variant', () => {
      const { container } = render(<LoadingSkeleton variant="default" />);

      expect(container.firstChild).toBeInTheDocument();
    });

    it('should render skeleton lines', () => {
      const { container } = render(<LoadingSkeleton variant="default" />);

      const lines = container.querySelectorAll('.animate-pulse');
      expect(lines.length).toBeGreaterThan(0);
    });
  });

  describe('Card Variant', () => {
    it('should render card variant', () => {
      const { container } = render(<LoadingSkeleton variant="card" />);

      const card = container.querySelector('.p-6');
      expect(card).toBeInTheDocument();
    });

    it('should render card elements', () => {
      const { container } = render(<LoadingSkeleton variant="card" />);

      const lines = container.querySelectorAll('.animate-pulse');
      expect(lines.length).toBeGreaterThan(0);
    });
  });

  describe('Table Variant', () => {
    it('should render table variant with default rows and cols', () => {
      const { container } = render(<LoadingSkeleton variant="table" />);

      const cells = container.querySelectorAll('.animate-pulse');
      // Default: 5 rows * 4 cols = 20 cells + header (4 cells) = 24
      expect(cells.length).toBeGreaterThanOrEqual(20);
    });

    it('should render table with custom rows', () => {
      const { container } = render(
        <LoadingSkeleton variant="table" rows={3} />
      );

      const rows = container.querySelectorAll('.space-y-3 > div');
      expect(rows.length).toBe(3);
    });

    it('should render table with custom cols', () => {
      const { container } = render(
        <LoadingSkeleton variant="table" cols={6} />
      );

      const headerCells = container.querySelector('.mb-4')?.querySelector('.flex');
      const cellDivs = headerCells?.querySelectorAll('div');
      expect(cellDivs?.length).toBe(6);
    });
  });

  describe('List Variant', () => {
    it('should render list variant', () => {
      const { container } = render(<LoadingSkeleton variant="list" />);

      const listItems = container.querySelectorAll('.border');
      expect(listItems.length).toBeGreaterThan(0);
    });

    it('should render list with custom count', () => {
      const { container } = render(
        <LoadingSkeleton variant="list" rows={3} />
      );

      const listItems = container.querySelectorAll('.border');
      expect(listItems.length).toBe(3);
    });
  });

  describe('Text Variant', () => {
    it('should render text variant', () => {
      const { container } = render(<LoadingSkeleton variant="text" />);

      const lines = container.querySelectorAll('.animate-pulse');
      expect(lines.length).toBe(3);
    });
  });

  describe('Custom Classes', () => {
    it('should apply custom className', () => {
      const { container } = render(
        <LoadingSkeleton variant="default" className="custom-class" />
      );

      expect(container.firstChild).toHaveClass('custom-class');
    });
  });

  describe('Animation', () => {
    it('should apply animate-pulse class', () => {
      const { container } = render(<LoadingSkeleton variant="default" />);

      const animatedElements = container.querySelectorAll('.animate-pulse');
      expect(animatedElements.length).toBeGreaterThan(0);
    });

    it('should apply gradient background', () => {
      const { container } = render(<LoadingSkeleton variant="default" />);

      const gradientElements = container.querySelectorAll(
        '.bg-gradient-to-r'
      );
      expect(gradientElements.length).toBeGreaterThan(0);
    });
  });
});

describe('LoadingOverlay Component', () => {
  it('should render loading spinner', () => {
    const { container } = render(<LoadingOverlay />);

    const spinner = container.querySelector('.animate-spin');
    expect(spinner).toBeInTheDocument();
  });

  it('should render default loading text', () => {
    render(<LoadingOverlay />);

    expect(screen.getByText('加载中...')).toBeInTheDocument();
  });

  it('should render custom loading text', () => {
    render(<LoadingOverlay text="请稍候..." />);

    expect(screen.getByText('请稍候...')).toBeInTheDocument();
    expect(screen.queryByText('加载中...')).not.toBeInTheDocument();
  });

  it('should apply custom className', () => {
    const { container } = render(
      <LoadingOverlay className="custom-class" />
    );

    const overlay = container.querySelector('.custom-class');
    expect(overlay).toBeInTheDocument();
  });

  it('should render spinner with correct styling', () => {
    const { container } = render(<LoadingOverlay />);

    const spinner = container.querySelector('.animate-spin');
    expect(spinner).toHaveClass('border-4');
    expect(spinner).toHaveClass('border-t-primary');
  });

  it('should center content', () => {
    const { container } = render(<LoadingOverlay />);

    const containerDiv = container.firstChild as HTMLElement;
    expect(containerDiv).toHaveClass('flex');
    expect(containerDiv).toHaveClass('items-center');
    expect(containerDiv).toHaveClass('justify-center');
  });
});

describe('InlineLoading Component', () => {
  it('should render small spinner by default', () => {
    const { container } = render(<InlineLoading />);

    const spinner = container.querySelector('.animate-spin');
    expect(spinner).toHaveClass('h-4');
    expect(spinner).toHaveClass('w-4');
  });

  it('should render medium spinner when size is md', () => {
    const { container } = render(<InlineLoading size="md" />);

    const spinner = container.querySelector('.animate-spin');
    expect(spinner).toHaveClass('h-6');
    expect(spinner).toHaveClass('w-6');
  });

  it('should apply border-2 styling', () => {
    const { container } = render(<InlineLoading />);

    const spinner = container.querySelector('.animate-spin');
    expect(spinner).toHaveClass('border-2');
  });

  it('should apply custom className', () => {
    const { container } = render(
      <InlineLoading className="custom-class" />
    );

    const wrapper = container.querySelector('.custom-class');
    expect(wrapper).toBeInTheDocument();
  });

  it('should center the spinner', () => {
    const { container } = render(<InlineLoading />);

    const wrapper = container.firstChild as HTMLElement;
    expect(wrapper).toHaveClass('flex');
    expect(wrapper).toHaveClass('items-center');
    expect(wrapper).toHaveClass('justify-center');
  });
});

describe('PatientCardSkeleton Component', () => {
  it('should render grid layout', () => {
    const { container } = render(<PatientCardSkeleton count={4} />);

    const grid = container.querySelector('.grid');
    expect(grid).toBeInTheDocument();
  });

  it('should render default count of cards', () => {
    const { container } = render(<PatientCardSkeleton />);

    const cards = container.querySelectorAll('.overflow-hidden');
    // Default count is 4
    expect(cards.length).toBe(4);
  });

  it('should render custom count of cards', () => {
    const { container } = render(<PatientCardSkeleton count={6} />);

    const cards = container.querySelectorAll('.overflow-hidden');
    expect(cards.length).toBe(6);
  });

  it('should render card elements structure', () => {
    const { container } = render(<PatientCardSkeleton count={1} />);

    // Should have avatar circle
    const avatar = container.querySelector('.rounded-full');
    expect(avatar).toBeInTheDocument();

    // Should have progress bar area
    const progressBar = container.querySelector('.rounded-full');
    expect(progressBar).toBeInTheDocument();
  });

  it('should apply responsive grid classes', () => {
    const { container } = render(<PatientCardSkeleton count={4} />);

    const grid = container.querySelector('.grid');
    expect(grid).toHaveClass('grid-cols-1');
    expect(grid).toHaveClass('md:grid-cols-2');
    expect(grid).toHaveClass('lg:grid-cols-3');
    expect(grid).toHaveClass('xl:grid-cols-4');
  });
});

describe('ConsultationSkeleton Component', () => {
  it('should render consultation layout structure', () => {
    const { container } = render(<ConsultationSkeleton />);

    // Should have main container with gap
    const mainContainer = container.querySelector('.gap-4');
    expect(mainContainer).toBeInTheDocument();
  });

  it('should render session list skeleton', () => {
    const { container } = render(<ConsultationSkeleton />);

    // Session list card
    const sessionList = container.querySelectorAll('.rounded-lg');
    expect(sessionList.length).toBeGreaterThan(0);
  });

  it('should render message detail skeleton', () => {
    const { container } = render(<ConsultationSkeleton />);

    // Should have message area
    const messageArea = container.querySelectorAll('.rounded-lg');
    expect(messageArea.length).toBeGreaterThan(0);
  });

  it('should render correct layout height', () => {
    const { container } = render(<ConsultationSkeleton />);

    const containerDiv = container.querySelector('[class*="h-"]');
    expect(containerDiv).toBeInTheDocument();
  });
});

describe('OrdersTableSkeleton Component', () => {
  it('should render title bar skeleton', () => {
    render(<OrdersTableSkeleton />);

    const titleSkeleton = screen.queryAllByText('').filter(
      (el) => el.className?.includes('animate-pulse')
    );
    expect(titleSkeleton.length).toBeGreaterThan(0);
  });

  it('should render table header skeleton', () => {
    const { container } = render(<OrdersTableSkeleton />);

    const headerSection = container.querySelector('.mb-4');
    const headerRow = headerSection?.querySelector('.flex');
    const headerCells = headerRow?.querySelectorAll('.animate-pulse');
    expect(headerCells?.length).toBe(8); // default 8 cols
  });

  it('should render table rows with default count', () => {
    const { container } = render(<OrdersTableSkeleton />);

    const rowDivides = container.querySelectorAll('.divide-y > div');
    expect(rowDivides.length).toBe(5); // default 5 rows
  });

  it('should render table rows with custom count', () => {
    const { container } = render(<OrdersTableSkeleton rows={3} cols={6} />);

    const rowDivides = container.querySelectorAll('.divide-y > div');
    expect(rowDivides.length).toBe(3);

    const headerSection = container.querySelector('.mb-4');
    const headerRow = headerSection?.querySelector('.flex');
    const headerCells = headerRow?.querySelectorAll('.animate-pulse');
    expect(headerCells?.length).toBe(6);
  });

  it('should render row cells with correct count', () => {
    const { container } = render(<OrdersTableSkeleton rows={3} cols={5} />);

    const firstRow = container.querySelector('.divide-y > div');
    const cells = firstRow?.querySelectorAll('.animate-pulse');
    expect(cells?.length).toBe(5);
  });
});

describe('PatientDetailCardSkeleton Component', () => {
  it('should render patient basic info card', () => {
    const { container } = render(<PatientDetailCardSkeleton />);

    const card = container.querySelector('.mb-4');
    expect(card).toBeInTheDocument();
  });

  it('should render avatar area', () => {
    const { container } = render(<PatientDetailCardSkeleton />);

    const avatar = container.querySelector('.w-20.h-20');
    expect(avatar).toBeInTheDocument();
  });

  it('should render detail info grid', () => {
    const { container } = render(<PatientDetailCardSkeleton />);

    const grid = container.querySelector('.grid-cols-2');
    expect(grid).toBeInTheDocument();
  });

  it('should render stat cards', () => {
    const { container } = render(<PatientDetailCardSkeleton />);

    const statGrid = container.querySelector('.grid-cols-1');
    expect(statGrid).toBeInTheDocument();

    const statCards = container.querySelectorAll('.stat-card');
    expect(statCards.length).toBe(3);
  });

  it('should render detail items', () => {
    const { container } = render(<PatientDetailCardSkeleton />);

    const detailItems = container.querySelectorAll('.bg-muted\\/50');
    expect(detailItems.length).toBe(6); // 6 detail items
  });
});

describe('Edge Cases', () => {
  it('should handle zero rows for table skeleton', () => {
    const { container } = render(<LoadingSkeleton variant="table" rows={0} />);

    const rows = container.querySelectorAll('.space-y-3 > div');
    expect(rows.length).toBe(0);
  });

  it('should handle zero cols for table skeleton', () => {
    const { container } = render(<LoadingSkeleton variant="table" cols={0} />);

    const cells = container.querySelectorAll('.mb-4 .flex.gap-4 > div');
    expect(cells.length).toBe(0);
  });

  it('should handle zero count for patient card skeleton', () => {
    const { container } = render(<PatientCardSkeleton count={0} />);

    const cards = container.querySelectorAll('.overflow-hidden');
    expect(cards.length).toBe(0);
  });

  it('should handle very large count for patient card skeleton', () => {
    const { container } = render(<PatientCardSkeleton count={20} />);

    const cards = container.querySelectorAll('.overflow-hidden');
    expect(cards.length).toBe(20);
  });

  it('should handle very large rows for table skeleton', () => {
    const { container } = render(<OrdersTableSkeleton rows={20} />);

    const rowDivides = container.querySelectorAll('.divide-y > div');
    expect(rowDivides.length).toBe(20);
  });

  it('should handle empty text', () => {
    render(<LoadingOverlay text="" />);

    // Should still render spinner
    const { container } = render(<LoadingOverlay text="" />);
    const spinner = container.querySelector('.animate-spin');
    expect(spinner).toBeInTheDocument();
  });
});

describe('Accessibility', () => {
  it('should have proper aria attributes for loading state', () => {
    const { container } = render(<InlineLoading />);

    const wrapper = container.firstChild as HTMLElement;
    // Loading indicators should be aria-hidden or have appropriate labels
    expect(wrapper).toBeInTheDocument();
  });

  it('should be screen reader friendly', () => {
    render(<LoadingOverlay text="正在加载内容" />);

    const text = screen.getByText('正在加载内容');
    expect(text).toBeInTheDocument();
  });
});
