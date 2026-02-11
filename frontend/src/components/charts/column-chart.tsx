import React from 'react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';
import { getThemeColors } from '@/lib/theme';

export interface ColumnChartData {
  [key: string]: string | number;
}

export interface ColumnChartProps {
  data: ColumnChartData[];
  xField: string;
  yField: string | string[];
  height?: number;
  columnWidthRatio?: number;
  colors?: string[];
  legendPosition?: 'top' | 'bottom' | 'left' | 'right';
  tooltipFormatter?: (name: string, value: any) => { name: string; value: string };
  className?: string;
}

/**
 * ColumnChart 组件 - 使用 Recharts 替代 @ant-design/charts Column
 *
 * 支持单列或多列柱状图，自动适配 shadcn/ui 主题
 */
export const CustomColumnChart: React.FC<ColumnChartProps> = ({
  data,
  xField,
  yField,
  height = 200,
  columnWidthRatio = 0.6,
  colors,
  legendPosition = 'top',
  tooltipFormatter,
  className,
}) => {
  const themeColors = getThemeColors();
  const defaultColors = [
    themeColors.colorPrimary,
    themeColors.colorSuccess,
    themeColors.colorWarning,
    themeColors.colorInfo,
  ];

  const barColors = colors || defaultColors;

  // 处理 tooltip 格式化
  const formatTooltip = (props: any) => {
    if (!props.payload || props.payload.length === 0) return null;

    if (tooltipFormatter) {
      const data = props.payload[0];
      const result = tooltipFormatter(data.name, data.value);
      return (
        <div className="bg-popover text-popover-foreground border border-border rounded-lg shadow-lg p-2">
          <p className="text-sm font-medium">{result.name}</p>
          <p className="text-sm">{result.value}</p>
        </div>
      );
    }

    return (
      <div className="bg-popover text-popover-foreground border border-border rounded-lg shadow-lg p-2">
        <p className="text-sm font-medium">{props.payload[0].payload[xField]}</p>
        {props.payload.map((entry: any, index: number) => (
          <p key={index} className="text-sm" style={{ color: entry.color }}>
            {entry.name}: {entry.value}
          </p>
        ))}
      </div>
    );
  };

  // Legend 对齐方式
  const getLegendAlign = () => {
    switch (legendPosition) {
      case 'left': return 'flex-start';
      case 'right': return 'flex-end';
      default: return 'center';
    }
  };

  return (
    <div className={className} style={{ height }}>
      <ResponsiveContainer width="100%" height="100%">
        <BarChart
          data={data}
          margin={{ top: legendPosition === 'top' ? 20 : 5, right: 30, left: 20, bottom: 5 }}
          barCategoryGap={columnWidthRatio ? `${(1 - columnWidthRatio) * 100}%` : undefined}
        >
          <CartesianGrid strokeDasharray="3 3" className="stroke-border/30" />
          <XAxis
            dataKey={xField}
            className="text-xs text-foreground-secondary"
            stroke="hsl(var(--muted-foreground))"
          />
          <YAxis
            className="text-xs text-foreground-secondary"
            stroke="hsl(var(--muted-foreground))"
          />
          <Tooltip content={formatTooltip} />
          <Legend
            verticalAlign={legendPosition === 'bottom' ? 'bottom' : 'top'}
            align={getLegendAlign() as any}
          />
          {Array.isArray(yField) ? (
            yField.map((field, index) => (
              <Bar
                key={field}
                dataKey={field}
                fill={barColors[index % barColors.length]}
                name={field}
                radius={[4, 4, 0, 0]}
              />
            ))
          ) : (
            <Bar
              dataKey={yField}
              fill={barColors[0]}
              radius={[4, 4, 0, 0]}
            />
          )}
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
};

export default CustomColumnChart;
