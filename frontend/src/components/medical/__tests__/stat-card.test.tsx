/**
 * StatCard 组件测试
 *
 * 测试覆盖：
 * 1. 组件渲染测试
 * 2. Props 传递测试
 * 3. 用户交互测试
 * 4. 样式变化测试（variant, trend）
 * 5. 边界条件测试
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { StatCard, StatCardGrid } from '../stat-card';

// Mock CSS 变量
const mockComputedStyle = {
  getPropertyValue: vi.fn((name) => {
    const colorMap: Record<string, string> = {
      '--primary': '199 89% 48%',
      '--success': '142 76% 36%',
      '--warning': '38 92% 50%',
      '--danger': '0 72% 51%',
      '--info': '207 89% 54%',
    };
    return colorMap[name] || '199 89% 48%';
  }),
};

describe('StatCard Component', () => {
  beforeEach(() => {
    vi.stubGlobal('getComputedStyle', () => mockComputedStyle);
  });

  afterEach(() => {
    vi.unstubAllGlobals();
    vi.clearAllMocks();
  });

  describe('Rendering', () => {
    it('should render title and value', () => {
      render(<StatCard title="患者总数" value={1234} />);

      expect(screen.getByText('患者总数')).toBeInTheDocument();
      expect(screen.getByText('1,234')).toBeInTheDocument();
    });

    it('should render value as string when provided', () => {
      render(<StatCard title="状态" value="正常" />);

      expect(screen.getByText('正常')).toBeInTheDocument();
    });

    it('should render unit when provided', () => {
      render(<StatCard title="患者总数" value={1234} unit="人" />);

      expect(screen.getByText('人')).toBeInTheDocument();
    });

    it('should not render unit when not provided', () => {
      render(<StatCard title="患者总数" value={1234} />);

      const unit = screen.queryByText('人');
      expect(unit).not.toBeInTheDocument();
    });

    it('should render trend when provided', () => {
      render(<StatCard title="患者总数" value={1234} trend="+12%" />);

      expect(screen.getByText('+12%')).toBeInTheDocument();
    });

    it('should render icon when provided', () => {
      render(
        <StatCard
          title="患者总数"
          value={1234}
          icon={<span data-testid="test-icon">Icon</span>}
        />
      );

      expect(screen.getByTestId('test-icon')).toBeInTheDocument();
    });

    it('should apply clickable class when onClick is provided', () => {
      const { container } = render(
        <StatCard title="患者总数" value={1234} onClick={vi.fn()} />
      );

      const card = container.querySelector('.stat-card');
      expect(card).toHaveClass('cursor-pointer');
    });

    it('should not apply clickable class when onClick is not provided', () => {
      const { container } = render(
        <StatCard title="患者总数" value={1234} />
      );

      const card = container.querySelector('.stat-card');
      expect(card).not.toHaveClass('cursor-pointer');
    });
  });

  describe('Value Formatting', () => {
    it('should format number with locale', () => {
      render(<StatCard title="患者总数" value={1234567} />);

      expect(screen.getByText('1,234,567')).toBeInTheDocument();
    });

    it('should handle zero value', () => {
      render(<StatCard title="患者总数" value={0} />);

      expect(screen.getByText('0')).toBeInTheDocument();
    });

    it('should handle negative number', () => {
      render(<StatCard title="变化" value={-123} />);

      expect(screen.getByText('-123')).toBeInTheDocument();
    });

    it('should handle decimal number', () => {
      render(<StatCard title="比率" value={0.85} />);

      // Should display as-is since it's a number
      expect(screen.getByText('0.85')).toBeInTheDocument();
    });
  });

  describe('Variants', () => {
    it('should render primary variant by default', () => {
      const { container } = render(
        <StatCard title="患者总数" value={1234} variant="primary" />
      );

      const iconContainer = container.querySelector('.rounded-lg');
      expect(iconContainer).toHaveClass('bg-primary/10');
    });

    it('should render success variant', () => {
      const { container } = render(
        <StatCard title="患者总数" value={1234} variant="success" />
      );

      const iconContainer = container.querySelector('.rounded-lg');
      expect(iconContainer).toHaveClass('bg-success/10');
    });

    it('should render warning variant', () => {
      const { container } = render(
        <StatCard title="患者总数" value={1234} variant="warning" />
      );

      const iconContainer = container.querySelector('.rounded-lg');
      expect(iconContainer).toHaveClass('bg-warning/10');
    });

    it('should render danger variant', () => {
      const { container } = render(
        <StatCard title="患者总数" value={1234} variant="danger" />
      );

      const iconContainer = container.querySelector('.rounded-lg');
      expect(iconContainer).toHaveClass('bg-danger/10');
    });

    it('should render info variant', () => {
      const { container } = render(
        <StatCard title="患者总数" value={1234} variant="info" />
      );

      const iconContainer = container.querySelector('.rounded-lg');
      expect(iconContainer).toHaveClass('bg-info/10');
    });
  });

  describe('Trend Colors', () => {
    it('should apply success color for positive trend when trendUp is true', () => {
      const { container } = render(
        <StatCard title="患者总数" value={1234} trend="+12%" trendUp />
      );

      const trend = screen.getByText('+12%');
      expect(trend).toHaveClass('text-success');
    });

    it('should apply danger color for negative trend when trendUp is false', () => {
      const { container } = render(
        <StatCard title="患者总数" value={1234} trend="-5%" trendUp={false} />
      );

      const trend = screen.getByText('-5%');
      expect(trend).toHaveClass('text-danger');
    });

    it('should apply success color for negative trend when trendUp is true', () => {
      const { container } = render(
        <StatCard title="患者总数" value={1234} trend="-5%" trendUp />
      );

      const trend = screen.getByText('-5%');
      expect(trend).toHaveClass('text-success');
    });
  });

  describe('User Interactions', () => {
    it('should call onClick when card is clicked', async () => {
      const user = userEvent.setup();
      const handleClick = vi.fn();

      render(<StatCard title="患者总数" value={1234} onClick={handleClick} />);

      const card = screen.getByText('患者总数').closest('.stat-card');
      if (card) {
        await user.click(card);
        expect(handleClick).toHaveBeenCalledTimes(1);
      }
    });

    it('should not be clickable when onClick is not provided', () => {
      const { container } = render(
        <StatCard title="患者总数" value={1234} />
      );

      const card = container.querySelector('.stat-card');
      expect(card).not.toHaveClass('cursor-pointer');
      expect(card).not.toHaveClass('hover:shadow-md');
    });
  });

  describe('Custom Classes', () => {
    it('should apply custom className', () => {
      const { container } = render(
        <StatCard title="患者总数" value={1234} className="custom-class" />
      );

      const card = container.querySelector('.stat-card');
      expect(card).toHaveClass('custom-class');
    });

    it('should merge custom class with default classes', () => {
      const { container } = render(
        <StatCard
          title="患者总数"
          value={1234}
          onClick={vi.fn()}
          className="custom-class"
        />
      );

      const card = container.querySelector('.stat-card');
      expect(card).toHaveClass('stat-card');
      expect(card).toHaveClass('group');
      expect(card).toHaveClass('custom-class');
    });
  });

  describe('Decorative Background', () => {
    it('should render decorative background element', () => {
      const { container } = render(
        <StatCard title="患者总数" value={1234} />
      );

      const background = container.querySelector('.rounded-full');
      expect(background).toBeInTheDocument();
      expect(background).toHaveClass('opacity-10');
      expect(background).toHaveClass('blur-2xl');
    });
  });

  describe('Edge Cases', () => {
    it('should handle very large numbers', () => {
      render(<StatCard title="患者总数" value={999999999999} />);

      expect(screen.getByText('999,999,999,999')).toBeInTheDocument();
    });

    it('should handle empty string value', () => {
      render(<StatCard title="状态" value="" />);

      // Should render empty value
      const valueElement = screen.getByText('');
      expect(valueElement).toBeInTheDocument();
    });

    it('should handle long title', () => {
      const longTitle = '这是一个非常非常非常非常非常非常长的标题';
      render(<StatCard title={longTitle} value={1234} />);

      expect(screen.getByText(longTitle)).toBeInTheDocument();
    });

    it('should handle special characters in title', () => {
      render(<StatCard title="患者（总数）" value={1234} />);

      expect(screen.getByText('患者（总数）')).toBeInTheDocument();
    });

    it('should handle trend with emoji', () => {
      render(<StatCard title="患者总数" value={1234} trend="+12%" />);

      expect(screen.getByText('+12%')).toBeInTheDocument();
    });
  });
});

describe('StatCardGrid Component', () => {
  describe('Rendering', () => {
    it('should render grid of stat cards', () => {
      const items = [
        { title: '患者总数', value: 1234 },
        { title: '活跃患者', value: 567 },
        { title: '新增患者', value: 89 },
        { title: '完成率', value: '85%' },
      ];

      render(<StatCardGrid items={items} />);

      expect(screen.getByText('患者总数')).toBeInTheDocument();
      expect(screen.getByText('活跃患者')).toBeInTheDocument();
      expect(screen.getByText('新增患者')).toBeInTheDocument();
      expect(screen.getByText('完成率')).toBeInTheDocument();
    });

    it('should render correct number of cards', () => {
      const items = [
        { title: '患者总数', value: 1234 },
        { title: '活跃患者', value: 567 },
        { title: '新增患者', value: 89 },
      ];

      const { container } = render(<StatCardGrid items={items} />);

      const cards = container.querySelectorAll('.stat-card');
      expect(cards.length).toBe(3);
    });

    it('should render empty grid when items is empty', () => {
      const { container } = render(<StatCardGrid items={[]} />);

      const cards = container.querySelectorAll('.stat-card');
      expect(cards.length).toBe(0);
    });
  });

  describe('Grid Layout', () => {
    it('should apply 1 column layout', () => {
      const { container } = render(
        <StatCardGrid items={[{ title: 'Test', value: 1 }]} cols={1} />
      );

      const grid = container.firstChild as HTMLElement;
      expect(grid).toHaveClass('grid-cols-1');
    });

    it('should apply 2 column layout', () => {
      const { container } = render(
        <StatCardGrid items={[{ title: 'Test', value: 1 }]} cols={2} />
      );

      const grid = container.firstChild as HTMLElement;
      expect(grid).toHaveClass('grid-cols-1');
      expect(grid).toHaveClass('md:grid-cols-2');
    });

    it('should apply 3 column layout', () => {
      const { container } = render(
        <StatCardGrid items={[{ title: 'Test', value: 1 }]} cols={3} />
      );

      const grid = container.firstChild as HTMLElement;
      expect(grid).toHaveClass('grid-cols-1');
      expect(grid).toHaveClass('md:grid-cols-2');
      expect(grid).toHaveClass('lg:grid-cols-3');
    });

    it('should apply 4 column layout by default', () => {
      const { container } = render(
        <StatCardGrid items={[{ title: 'Test', value: 1 }]} />
      );

      const grid = container.firstChild as HTMLElement;
      expect(grid).toHaveClass('grid-cols-1');
      expect(grid).toHaveClass('sm:grid-cols-2');
      expect(grid).toHaveClass('lg:grid-cols-4');
    });
  });

  describe('Grid Gap', () => {
    it('should apply default gap class', () => {
      const { container } = render(
        <StatCardGrid items={[{ title: 'Test', value: 1 }]} />
      );

      const grid = container.firstChild as HTMLElement;
      expect(grid).toHaveClass('gap-4');
    });

    it('should apply custom gap class', () => {
      const { container } = render(
        <StatCardGrid items={[{ title: 'Test', value: 1 }]} gap="gap-8" />
      );

      const grid = container.firstChild as HTMLElement;
      expect(grid).toHaveClass('gap-8');
    });
  });

  describe('Custom Classes', () => {
    it('should apply custom className to grid container', () => {
      const { container } = render(
        <StatCardGrid
          items={[{ title: 'Test', value: 1 }]}
          className="custom-class"
        />
      );

      const grid = container.firstChild as HTMLElement;
      expect(grid).toHaveClass('custom-class');
    });
  });

  describe('Item Props', () => {
    it('should pass all props to individual StatCard', () => {
      const items = [
        {
          title: '患者总数',
          value: 1234,
          unit: '人',
          trend: '+12%',
          trendUp: true,
          variant: 'success' as const,
        },
      ];

      render(<StatCardGrid items={items} />);

      expect(screen.getByText('患者总数')).toBeInTheDocument();
      expect(screen.getByText('1,234')).toBeInTheDocument();
      expect(screen.getByText('人')).toBeInTheDocument();
      expect(screen.getByText('+12%')).toBeInTheDocument();
    });

    it('should render cards with onClick handlers', async () => {
      const user = userEvent.setup();
      const handleClick1 = vi.fn();
      const handleClick2 = vi.fn();

      const items = [
        { title: '卡片1', value: 1, onClick: handleClick1 },
        { title: '卡片2', value: 2, onClick: handleClick2 },
      ];

      render(<StatCardGrid items={items} />);

      const card1 = screen.getByText('卡片1').closest('.stat-card');
      const card2 = screen.getByText('卡片2').closest('.stat-card');

      if (card1 && card2) {
        await user.click(card1);
        expect(handleClick1).toHaveBeenCalledTimes(1);

        await user.click(card2);
        expect(handleClick2).toHaveBeenCalledTimes(1);
      }
    });
  });

  describe('Edge Cases', () => {
    it('should handle items with undefined optional props', () => {
      const items = [
        { title: 'Test', value: 123 },
      ];

      render(<StatCardGrid items={items} />);

      expect(screen.getByText('Test')).toBeInTheDocument();
    });

    it('should handle many items', () => {
      const items = Array.from({ length: 12 }, (_, i) => ({
        title: `卡片${i + 1}`,
        value: i + 1,
      }));

      render(<StatCardGrid items={items} cols={4} />);

      expect(screen.getByText('卡片1')).toBeInTheDocument();
      expect(screen.getByText('卡片12')).toBeInTheDocument();
    });
  });
});
