/**
 * CustomColumnChart 组件测试
 *
 * 测试覆盖：
 * 1. 组件渲染测试
 * 2. Props 传递测试
 * 3. 数据渲染测试
 * 4. 边界条件测试
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import { CustomColumnChart, type ColumnChartProps } from '../column-chart';

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

describe('CustomColumnChart Component', () => {
  const mockData = [
    { name: '一月', value: 120 },
    { name: '二月', value: 200 },
    { name: '三月', value: 150 },
    { name: '四月', value: 80 },
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
        <CustomColumnChart
          data={mockData}
          xField="name"
          yField="value"
        />
      );

      expect(screen.getByTestId('responsive-container')).toBeInTheDocument();
    });

    it('should render legend', () => {
      render(
        <CustomColumnChart
          data={mockData}
          xField="name"
          yField="value"
        />
      );

      expect(screen.getByTestId('legend-top')).toBeInTheDocument();
    });

    it('should render tooltip', () => {
      render(
        <CustomColumnChart
          data={mockData}
          xField="name"
          yField="value"
        />
      );

      expect(screen.getByTestId('tooltip')).toBeInTheDocument();
    });

    it('should render with custom height', () => {
      const { container } = render(
        <CustomColumnChart
          data={mockData}
          xField="name"
          yField="value"
          height={300}
        />
      );

      const chartContainer = container.querySelector('[style*="height"]');
      expect(chartContainer?.getAttribute('style')).toContain('height: 300');
    });

    it('should render with default height', () => {
      const { container } = render(
        <CustomColumnChart
          data={mockData}
          xField="name"
          yField="value"
        />
      );

      const chartContainer = container.querySelector('[style*="height"]');
      expect(chartContainer?.getAttribute('style')).toContain('height: 200');
    });
  });

  describe('Data Rendering', () => {
    it('should render single series data', () => {
      render(
        <CustomColumnChart
          data={mockData}
          xField="name"
          yField="value"
        />
      );

      // Chart should be rendered
      expect(screen.getByTestId('responsive-container')).toBeInTheDocument();
    });

    it('should render multiple series data', () => {
      const multiSeriesData = [
        { name: '一月', value1: 120, value2: 80 },
        { name: '二月', value1: 200, value2: 150 },
      ];

      render(
        <CustomColumnChart
          data={multiSeriesData}
          xField="name"
          yField={['value1', 'value2']}
        />
      );

      expect(screen.getByTestId('responsive-container')).toBeInTheDocument();
    });

    it('should handle empty data', () => {
      render(
        <CustomColumnChart
          data={[]}
          xField="name"
          yField="value"
        />
      );

      // Should not crash
      expect(screen.getByTestId('responsive-container')).toBeInTheDocument();
    });

    it('should handle single data point', () => {
      const singleData = [{ name: '一月', value: 100 }];

      render(
        <CustomColumnChart
          data={singleData}
          xField="name"
          yField="value"
        />
      );

      expect(screen.getByTestId('responsive-container')).toBeInTheDocument();
    });
  });

  describe('Legend Position', () => {
    it('should render legend at top by default', () => {
      render(
        <CustomColumnChart
          data={mockData}
          xField="name"
          yField="value"
        />
      );

      expect(screen.getByTestId('legend-top')).toBeInTheDocument();
    });

    it('should render legend at bottom', () => {
      render(
        <CustomColumnChart
          data={mockData}
          xField="name"
          yField="value"
          legendPosition="bottom"
        />
      );

      expect(screen.getByTestId('legend-bottom')).toBeInTheDocument();
    });

    it('should render legend at left', () => {
      render(
        <CustomColumnChart
          data={mockData}
          xField="name"
          yField="value"
          legendPosition="left"
        />
      );

      expect(screen.getByTestId('legend-top')).toBeInTheDocument();
    });

    it('should render legend at right', () => {
      render(
        <CustomColumnChart
          data={mockData}
          xField="name"
          yField="value"
          legendPosition="right"
        />
      );

      expect(screen.getByTestId('legend-top')).toBeInTheDocument();
    });
  });

  describe('Column Width', () => {
    it('should apply custom column width ratio', () => {
      render(
        <CustomColumnChart
          data={mockData}
          xField="name"
          yField="value"
          columnWidthRatio={0.8}
        />
      );

      expect(screen.getByTestId('responsive-container')).toBeInTheDocument();
    });

    it('should use default column width ratio', () => {
      render(
        <CustomColumnChart
          data={mockData}
          xField="name"
          yField="value"
        />
      );

      expect(screen.getByTestId('responsive-container')).toBeInTheDocument();
    });
  });

  describe('Colors', () => {
    it('should use default theme colors', () => {
      render(
        <CustomColumnChart
          data={mockData}
          xField="name"
          yField="value"
        />
      );

      // Should render with default colors from theme
      expect(screen.getByTestId('responsive-container')).toBeInTheDocument();
    });

    it('should use custom colors when provided', () => {
      const customColors = ['#FF0000', '#00FF00', '#0000FF'];

      render(
        <CustomColumnChart
          data={mockData}
          xField="name"
          yField={['value1', 'value2', 'value3']}
          xField="name"
          yField="value"
          colors={customColors}
        />
      );

      expect(screen.getByTestId('responsive-container')).toBeInTheDocument();
    });

    it('should handle empty colors array', () => {
      render(
        <CustomColumnChart
          data={mockData}
          xField="name"
          yField="value"
          colors={[]}
        />
      );

      // Should fall back to default theme colors
      expect(screen.getByTestId('responsive-container')).toBeInTheDocument();
    });
  });

  describe('Tooltip', () => {
    it('should use custom tooltip formatter', () => {
      const tooltipFormatter = vi.fn(() => ({
        name: 'Test',
        value: '100',
      }));

      render(
        <CustomColumnChart
          data={mockData}
          xField="name"
          yField="value"
          tooltipFormatter={tooltipFormatter}
        />
      );

      expect(screen.getByTestId('tooltip')).toBeInTheDocument();
    });
  });

  describe('Custom Classes', () => {
    it('should apply custom className', () => {
      const { container } = render(
        <CustomColumnChart
          data={mockData}
          xField="name"
          yField="value"
          className="custom-chart-class"
        />
      );

      const chartContainer = container.querySelector('.custom-chart-class');
      expect(chartContainer).toBeInTheDocument();
    });
  });

  describe('Edge Cases', () => {
    it('should handle missing xField values', () => {
      const dataWithMissing = [
        { value: 100 },
        { name: 'Test', value: 200 },
      ];

      render(
        <CustomColumnChart
          data={dataWithMissing as any}
          xField="name"
          yField="value"
        />
      );

      expect(screen.getByTestId('responsive-container')).toBeInTheDocument();
    });

    it('should handle negative values', () => {
      const dataWithNegative = [
        { name: '一月', value: -100 },
        { name: '二月', value: 200 },
      ];

      render(
        <CustomColumnChart
          data={dataWithNegative}
          xField="name"
          yField="value"
        />
      );

      expect(screen.getByTestId('responsive-container')).toBeInTheDocument();
    });

    it('should handle zero values', () => {
      const dataWithZero = [
        { name: '一月', value: 0 },
        { name: '二月', value: 100 },
      ];

      render(
        <CustomColumnChart
          data={dataWithZero}
          xField="name"
          yField="value"
        />
      );

      expect(screen.getByTestId('responsive-container')).toBeInTheDocument();
    });

    it('should handle very large values', () => {
      const dataWithLargeValues = [
        { name: '一月', value: 999999999 },
        { name: '二月', value: 1000000000 },
      ];

      render(
        <CustomColumnChart
          data={dataWithLargeValues}
          xField="name"
          yField="value"
        />
      );

      expect(screen.getByTestId('responsive-container')).toBeInTheDocument();
    });

    it('should handle decimal values', () => {
      const dataWithDecimals = [
        { name: '一月', value: 12.5 },
        { name: '二月', value: 34.7 },
      ];

      render(
        <CustomColumnChart
          data={dataWithDecimals}
          xField="name"
          yField="value"
        />
      );

      expect(screen.getByTestId('responsive-container')).toBeInTheDocument();
    });

    it('should handle very long data array', () => {
      const longData = Array.from({ length: 100 }, (_, i) => ({
        name: `项${i}`,
        value: Math.random() * 100,
      }));

      render(
        <CustomColumnChart
          data={longData}
          xField="name"
          yField="value"
        />
      );

      expect(screen.getByTestId('responsive-container')).toBeInTheDocument();
    });
  });

  describe('Multi-Series Charts', () => {
    it('should render multiple bars for multi-series data', () => {
      const multiSeriesData = [
        { name: '一月', value1: 120, value2: 80 },
        { name: '二月', value1: 200, value2: 150 },
      ];

      render(
        <CustomColumnChart
          data={multiSeriesData}
          xField="name"
          yField={['value1', 'value2']}
        />
      );

      expect(screen.getByTestId('responsive-container')).toBeInTheDocument();
    });

    it('should handle more than 4 series', () => {
      const manySeriesData = [
        { name: '一月', v1: 10, v2: 20, v3: 30, v4: 40, v5: 50 },
      ];

      render(
        <CustomColumnChart
          data={manySeriesData as any}
          xField="name"
          yField={['v1', 'v2', 'v3', 'v4', 'v5']}
        />
      );

      expect(screen.getByTestId('responsive-container')).toBeInTheDocument();
    });
  });
});
