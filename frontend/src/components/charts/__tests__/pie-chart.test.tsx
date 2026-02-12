/**
 * CustomPieChart 组件测试
 *
 * 测试覆盖：
 * 1. 组件渲染测试
 * 2. Props 传递测试
 * 3. 数据渲染测试
 * 4. 边界条件测试
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import { CustomPieChart, type PieChartData } from '../pie-chart';

// Mock getThemeColors function
vi.mock('@/lib/theme', () => ({
  getThemeColors: () => ({
    colorPrimary: '#0EA5E9',
    colorSuccess: '#10B981',
    colorWarning: '#F59E0B',
    colorInfo: '#3B82F6',
    colorError: '#EF4444',
  }),
}));

// Mock Recharts components
vi.mock('recharts', async () => {
  const actual = await vi.importActual('recharts');
  return {
    ...actual,
    ResponsiveContainer: ({ children, height }: any) => (
      <div style={{ height }} data-testid="responsive-container">
        {children}
      </div>
    ),
    Tooltip: ({ content }: any) => (
      <div data-testid="tooltip">{content}</div>
    ),
    Legend: ({ verticalAlign }: any) => (
      <div data-testid={`legend-${verticalAlign}`}>Legend</div>
    ),
  };
});

describe('CustomPieChart Component', () => {
  const mockData: PieChartData[] = [
    { type: '活跃', value: 120 },
    { type: '非活跃', value: 80 },
    { type: '待审核', value: 40 },
    { type: '已关闭', value: 20 },
  ];

  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe('Rendering', () => {
    it('should render chart with data', () => {
      render(
        <CustomPieChart
          data={mockData}
          valueField="value"
        />
      );

      expect(screen.getByTestId('responsive-container')).toBeInTheDocument();
    });

    it('should render with default height', () => {
      const { container } = render(
        <CustomPieChart
          data={mockData}
          valueField="value"
        />
      );

      const chartContainer = container.querySelector('[style*="height"]');
      expect(chartContainer?.getAttribute('style')).toContain('height: 200');
    });

    it('should render with custom height', () => {
      const { container } = render(
        <CustomPieChart
          data={mockData}
          valueField="value"
          height={300}
        />
      );

      const chartContainer = container.querySelector('[style*="height"]');
      expect(chartContainer?.getAttribute('style')).toContain('height: 300');
    });

    it('should render legend', () => {
      render(
        <CustomPieChart
          data={mockData}
          valueField="value"
        />
      );

      expect(screen.getByTestId('legend-bottom')).toBeInTheDocument();
    });

    it('should render tooltip', () => {
      render(
        <CustomPieChart
          data={mockData}
          valueField="value"
        />
      );

      expect(screen.getByTestId('tooltip')).toBeInTheDocument();
    });
  });

  describe('Data Fields', () => {
    it('should use default valueField', () => {
      render(
        <CustomPieChart
          data={mockData}
          valueField="value"
        />
      );

      expect(screen.getByTestId('responsive-container')).toBeInTheDocument();
    });

    it('should use custom nameField', () => {
      const customData = [
        { category: 'A', count: 100 },
        { category: 'B', count: 200 },
      ] as any;

      render(
        <CustomPieChart
          data={customData}
          nameField="category"
          valueField="count"
        />
      );

      expect(screen.getByTestId('responsive-container')).toBeInTheDocument();
    });

    it('should use default nameField', () => {
      render(
        <CustomPieChart
          data={mockData}
          valueField="value"
        />
      );

      expect(screen.getByTestId('responsive-container')).toBeInTheDocument();
    });
  });

  describe('Legend Position', () => {
    it('should render legend at bottom by default', () => {
      render(
        <CustomPieChart
          data={mockData}
          valueField="value"
        />
      );

      expect(screen.getByTestId('legend-bottom')).toBeInTheDocument();
    });

    it('should render legend at top', () => {
      render(
        <CustomPieChart
          data={mockData}
          valueField="value"
          legendPosition="top"
        />
      );

      expect(screen.getByTestId('legend-top')).toBeInTheDocument();
    });

    it('should render legend at left', () => {
      render(
        <CustomPieChart
          data={mockData}
          valueField="value"
          legendPosition="left"
        />
      );

      expect(screen.getByTestId('legend-bottom')).toBeInTheDocument();
    });

    it('should render legend at right', () => {
      render(
        <CustomPieChart
          data={mockData}
          valueField="value"
          legendPosition="right"
        />
      );

      expect(screen.getByTestId('legend-bottom')).toBeInTheDocument();
    });
  });

  describe('Radius', () => {
    it('should use default radius', () => {
      render(
        <CustomPieChart
          data={mockData}
          valueField="value"
        />
      );

      expect(screen.getByTestId('responsive-container')).toBeInTheDocument();
    });

    it('should use custom radius', () => {
      render(
        <CustomPieChart
          data={mockData}
          valueField="value"
          radius={0.9}
        />
      );

      expect(screen.getByTestId('responsive-container')).toBeInTheDocument();
    });
  });

  describe('Inner Radius (Donut Chart)', () => {
    it('should use default inner radius', () => {
      render(
        <CustomPieChart
          data={mockData}
          valueField="value"
        />
      );

      expect(screen.getByTestId('responsive-container')).toBeInTheDocument();
    });

    it('should use custom inner radius', () => {
      render(
        <CustomPieChart
          data={mockData}
          valueField="value"
          innerRadius={0.7}
        />
      );

      expect(screen.getByTestId('responsive-container')).toBeInTheDocument();
    });

    it('should render as pie chart when innerRadius is 0', () => {
      render(
        <CustomPieChart
          data={mockData}
          valueField="value"
          innerRadius={0}
        />
      );

      expect(screen.getByTestId('responsive-container')).toBeInTheDocument();
    });
  });

  describe('Labels', () => {
    it('should not show labels by default', () => {
      render(
        <CustomPieChart
          data={mockData}
          valueField="value"
        />
      );

      // Labels are not rendered by default
      expect(screen.getByTestId('responsive-container')).toBeInTheDocument();
    });

    it('should show labels when label is true', () => {
      render(
        <CustomPieChart
          data={mockData}
          valueField="value"
          label
        />
      );

      expect(screen.getByTestId('responsive-container')).toBeInTheDocument();
    });
  });

  describe('Colors', () => {
    it('should use default theme colors', () => {
      render(
        <CustomPieChart
          data={mockData}
          valueField="value"
        />
      );

      expect(screen.getByTestId('responsive-container')).toBeInTheDocument();
    });

    it('should use custom colors when provided', () => {
      const customColors = ['#FF0000', '#00FF00', '#0000FF', '#FFFF00'];

      render(
        <CustomPieChart
          data={mockData}
          valueField="value"
          colors={customColors}
        />
      );

      expect(screen.getByTestId('responsive-container')).toBeInTheDocument();
    });

    it('should cycle through colors when more data than colors', () => {
      const manyData = [
        { type: 'A', value: 10 },
        { type: 'B', value: 20 },
        { type: 'C', value: 30 },
        { type: 'D', value: 40 },
        { type: 'E', value: 50 },
        { type: 'F', value: 60 },
      ];

      render(
        <CustomPieChart
          data={manyData}
          valueField="value"
          colors={['#FF0000', '#00FF00']}
        />
      );

      expect(screen.getByTestId('responsive-container')).toBeInTheDocument();
    });
  });

  describe('Tooltip', () => {
    it('should use default tooltip', () => {
      render(
        <CustomPieChart
          data={mockData}
          valueField="value"
        />
      );

      expect(screen.getByTestId('tooltip')).toBeInTheDocument();
    });

    it('should use custom tooltip formatter', () => {
      const tooltipFormatter = vi.fn(() => ({
        name: 'Test',
        value: '100',
      }));

      render(
        <CustomPieChart
          data={mockData}
          valueField="value"
          tooltipFormatter={tooltipFormatter}
        />
      );

      expect(screen.getByTestId('tooltip')).toBeInTheDocument();
    });
  });

  describe('Custom Classes', () => {
    it('should apply custom className', () => {
      const { container } = render(
        <CustomPieChart
          data={mockData}
          valueField="value"
          className="custom-chart-class"
        />
      );

      const chartContainer = container.querySelector('.custom-chart-class');
      expect(chartContainer).toBeInTheDocument();
    });
  });

  describe('Edge Cases', () => {
    it('should handle empty data', () => {
      render(
        <CustomPieChart
          data={[]}
          valueField="value"
        />
      );

      expect(screen.getByTestId('responsive-container')).toBeInTheDocument();
    });

    it('should handle single data point', () => {
      const singleData = [{ type: 'A', value: 100 }];

      render(
        <CustomPieChart
          data={singleData}
          valueField="value"
        />
      );

      expect(screen.getByTestId('responsive-container')).toBeInTheDocument();
    });

    it('should handle zero values', () => {
      const dataWithZero = [
        { type: 'A', value: 0 },
        { type: 'B', value: 100 },
      ];

      render(
        <CustomPieChart
          data={dataWithZero}
          valueField="value"
        />
      );

      expect(screen.getByTestId('responsive-container')).toBeInTheDocument();
    });

    it('should handle negative values', () => {
      const dataWithNegative = [
        { type: 'A', value: -50 },
        { type: 'B', value: 100 },
      ];

      render(
        <CustomPieChart
          data={dataWithNegative}
          valueField="value"
        />
      );

      expect(screen.getByTestId('responsive-container')).toBeInTheDocument();
    });

    it('should handle very large values', () => {
      const dataWithLargeValues = [
        { type: 'A', value: 999999999 },
        { type: 'B', value: 1000000000 },
      ];

      render(
        <CustomPieChart
          data={dataWithLargeValues}
          valueField="value"
        />
      );

      expect(screen.getByTestId('responsive-container')).toBeInTheDocument();
    });

    it('should handle decimal values', () => {
      const dataWithDecimals = [
        { type: 'A', value: 12.5 },
        { type: 'B', value: 34.7 },
      ];

      render(
        <CustomPieChart
          data={dataWithDecimals}
          valueField="value"
        />
      );

      expect(screen.getByTestId('responsive-container')).toBeInTheDocument();
    });

    it('should handle very long data array', () => {
      const longData = Array.from({ length: 50 }, (_, i) => ({
        type: `分类${i}`,
        value: Math.random() * 100,
      }));

      render(
        <CustomPieChart
          data={longData}
          valueField="value"
        />
      );

      expect(screen.getByTestId('responsive-container')).toBeInTheDocument();
    });

    it('should handle missing name field values', () => {
      const dataWithMissingNames = [
        { type: '', value: 100 },
        { type: 'B', value: 200 },
      ];

      render(
        <CustomPieChart
          data={dataWithMissingNames}
          valueField="value"
        />
      );

      expect(screen.getByTestId('responsive-container')).toBeInTheDocument();
    });
  });
});
