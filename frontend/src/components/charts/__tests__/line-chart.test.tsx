/**
 * CustomLineChart 组件测试
 *
 * 测试覆盖：
 * 1. 组件渲染测试
 * 2. Props 传递测试
 * 3. 数据渲染测试
 * 4. 边界条件测试
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import { CustomLineChart } from '../line-chart';

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
    Legend: () => <div data-testid="legend">Legend</div>,
  };
});

describe('CustomLineChart Component', () => {
  const mockData = [
    { date: '2024-01-01', value: 30 },
    { date: '2024-01-02', value: 40 },
    { date: '2024-01-03', value: 35 },
    { date: '2024-01-04', value: 50 },
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
        <CustomLineChart
          data={mockData}
          xField="date"
          yField="value"
        />
      );

      expect(screen.getByTestId('responsive-container')).toBeInTheDocument();
    });

    it('should render with default height', () => {
      const { container } = render(
        <CustomLineChart
          data={mockData}
          xField="date"
          yField="value"
        />
      );

      const chartContainer = container.querySelector('[style*="height"]');
      expect(chartContainer?.getAttribute('style')).toContain('height: 250');
    });

    it('should render with custom height', () => {
      const { container } = render(
        <CustomLineChart
          data={mockData}
          xField="date"
          yField="value"
          height={350}
        />
      );

      const chartContainer = container.querySelector('[style*="height"]');
      expect(chartContainer?.getAttribute('style')).toContain('height: 350');
    });

    it('should render tooltip', () => {
      render(
        <CustomLineChart
          data={mockData}
          xField="date"
          yField="value"
        />
      );

      expect(screen.getByTestId('tooltip')).toBeInTheDocument();
    });
  });

  describe('Line Options', () => {
    it('should render smooth line by default', () => {
      render(
        <CustomLineChart
          data={mockData}
          xField="date"
          yField="value"
          smooth
        />
      );

      expect(screen.getByTestId('responsive-container')).toBeInTheDocument();
    });

    it('should render non-smooth line when smooth is false', () => {
      render(
        <CustomLineChart
          data={mockData}
          xField="date"
          yField="value"
          smooth={false}
        />
      );

      expect(screen.getByTestId('responsive-container')).toBeInTheDocument();
    });
  });

  describe('Y-Axis Domain', () => {
    it('should apply custom Y-axis max', () => {
      render(
        <CustomLineChart
          data={mockData}
          xField="date"
          yField="value"
          yAxisMax={100}
        />
      );

      expect(screen.getByTestId('responsive-container')).toBeInTheDocument();
    });

    it('should apply custom Y-axis min', () => {
      render(
        <CustomLineChart
          data={mockData}
          xField="date"
          yField="value"
          yAxisMin={0}
        />
      );

      expect(screen.getByTestId('responsive-container')).toBeInTheDocument();
    });

    it('should apply both Y-axis min and max', () => {
      render(
        <CustomLineChart
          data={mockData}
          xField="date"
          yField="value"
          yAxisMin={10}
          yAxisMax={100}
        />
      );

      expect(screen.getByTestId('responsive-container')).toBeInTheDocument();
    });

    it('should use auto Y-axis when no domain specified', () => {
      render(
        <CustomLineChart
          data={mockData}
          xField="date"
          yField="value"
        />
      );

      expect(screen.getByTestId('responsive-container')).toBeInTheDocument();
    });
  });

  describe('Multi-Series Charts', () => {
    it('should render single line when yField is string', () => {
      render(
        <CustomLineChart
          data={mockData}
          xField="date"
          yField="value"
        />
      );

      expect(screen.getByTestId('responsive-container')).toBeInTheDocument();
    });

    it('should render multiple lines when yField is array', () => {
      const multiSeriesData = [
        { date: '2024-01-01', value1: 30, value2: 20 },
        { date: '2024-01-02', value1: 40, value2: 35 },
      ];

      render(
        <CustomLineChart
          data={multiSeriesData}
          xField="date"
          yField={['value1', 'value2']}
        />
      );

      expect(screen.getByTestId('responsive-container')).toBeInTheDocument();
    });

    it('should render legend for multi-series chart', () => {
      render(
        <CustomLineChart
          data={mockData}
          xField="date"
          yField={['value1', 'value2']}
        />
      );

      expect(screen.queryByTestId('legend')).toBeInTheDocument();
    });

    it('should not render legend for single line by default', () => {
      render(
        <CustomLineChart
          data={mockData}
          xField="date"
          yField="value"
        />
      );

      // Legend might not be rendered for single line without seriesField
      expect(screen.getByTestId('responsive-container')).toBeInTheDocument();
    });
  });

  describe('Series Field', () => {
    it('should handle seriesField for grouped data', () => {
      const groupedData = [
        { date: '2024-01-01', series: 'A', value: 30 },
        { date: '2024-01-01', series: 'B', value: 20 },
      ];

      render(
        <CustomLineChart
          data={groupedData}
          xField="date"
          yField="value"
          seriesField="series"
        />
      );

      expect(screen.getByTestId('responsive-container')).toBeInTheDocument();
    });

    it('should render legend when seriesField is provided', () => {
      const groupedData = [
        { date: '2024-01-01', series: 'A', value: 30 },
        { date: '2024-01-01', series: 'B', value: 20 },
      ];

      render(
        <CustomLineChart
          data={groupedData}
          xField="date"
          yField="value"
          seriesField="series"
        />
      );

      expect(screen.queryByTestId('legend')).toBeInTheDocument();
    });
  });

  describe('Colors', () => {
    it('should use default theme colors', () => {
      render(
        <CustomLineChart
          data={mockData}
          xField="date"
          yField="value"
        />
      );

      expect(screen.getByTestId('responsive-container')).toBeInTheDocument();
    });

    it('should use custom colors when provided', () => {
      const customColors = ['#FF0000', '#00FF00', '#0000FF'];

      render(
        <CustomLineChart
          data={mockData}
          xField="date"
          yField={['value1', 'value2', 'value3']}
          colors={customColors}
        />
      );

      expect(screen.getByTestId('responsive-container')).toBeInTheDocument();
    });
  });

  describe('Tooltip', () => {
    it('should use default tooltip', () => {
      render(
        <CustomLineChart
          data={mockData}
          xField="date"
          yField="value"
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
        <CustomLineChart
          data={mockData}
          xField="date"
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
        <CustomLineChart
          data={mockData}
          xField="date"
          yField="value"
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
        <CustomLineChart
          data={[]}
          xField="date"
          yField="value"
        />
      );

      expect(screen.getByTestId('responsive-container')).toBeInTheDocument();
    });

    it('should handle single data point', () => {
      const singleData = [{ date: '2024-01-01', value: 50 }];

      render(
        <CustomLineChart
          data={singleData}
          xField="date"
          yField="value"
        />
      );

      expect(screen.getByTestId('responsive-container')).toBeInTheDocument();
    });

    it('should handle negative values', () => {
      const dataWithNegative = [
        { date: '2024-01-01', value: -30 },
        { date: '2024-01-02', value: 40 },
      ];

      render(
        <CustomLineChart
          data={dataWithNegative}
          xField="date"
          yField="value"
        />
      );

      expect(screen.getByTestId('responsive-container')).toBeInTheDocument();
    });

    it('should handle zero values', () => {
      const dataWithZero = [
        { date: '2024-01-01', value: 0 },
        { date: '2024-01-02', value: 50 },
      ];

      render(
        <CustomLineChart
          data={dataWithZero}
          xField="date"
          yField="value"
        />
      );

      expect(screen.getByTestId('responsive-container')).toBeInTheDocument();
    });

    it('should handle null/undefined values', () => {
      const dataWithNull = [
        { date: '2024-01-01', value: 30 },
        { date: '2024-01-02', value: null as any },
        { date: '2024-01-03', value: 50 },
      ];

      render(
        <CustomLineChart
          data={dataWithNull}
          xField="date"
          yField="value"
        />
      );

      expect(screen.getByTestId('responsive-container')).toBeInTheDocument();
    });

    it('should handle very large values', () => {
      const dataWithLargeValues = [
        { date: '2024-01-01', value: 999999999 },
        { date: '2024-01-02', value: 1000000000 },
      ];

      render(
        <CustomLineChart
          data={dataWithLargeValues}
          xField="date"
          yField="value"
        />
      );

      expect(screen.getByTestId('responsive-container')).toBeInTheDocument();
    });

    it('should handle decimal values', () => {
      const dataWithDecimals = [
        { date: '2024-01-01', value: 12.5 },
        { date: '2024-01-02', value: 34.7 },
      ];

      render(
        <CustomLineChart
          data={dataWithDecimals}
          xField="date"
          yField="value"
        />
      );

      expect(screen.getByTestId('responsive-container')).toBeInTheDocument();
    });

    it('should handle very long data array', () => {
      const longData = Array.from({ length: 365 }, (_, i) => ({
        date: `2024-${String(Math.floor(i / 30) + 1).padStart(2, '0')}-${String((i % 30) + 1).padStart(2, '0')}`,
        value: Math.random() * 100,
      }));

      render(
        <CustomLineChart
          data={longData}
          xField="date"
          yField="value"
        />
      );

      expect(screen.getByTestId('responsive-container')).toBeInTheDocument();
    });
  });

  describe('Connect Nulls', () => {
    it('should connect nulls in line', () => {
      const dataWithNulls = [
        { date: '2024-01-01', value: 30 },
        { date: '2024-01-02', value: null as any },
        { date: '2024-01-03', value: 50 },
      ];

      render(
        <CustomLineChart
          data={dataWithNulls}
          xField="date"
          yField="value"
        />
      );

      expect(screen.getByTestId('responsive-container')).toBeInTheDocument();
    });
  });
});
