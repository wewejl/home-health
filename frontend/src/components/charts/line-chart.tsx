import React from 'react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';
import { getThemeColors } from '@/lib/theme';

export interface LineChartData {
  [key: string]: string | number;
}

export interface LineChartProps {
  data: LineChartData[];
  xField: string;
  yField: string | string[];
  seriesField?: string;
  height?: number;
  smooth?: boolean;
  colors?: string[];
  yAxisMax?: number;
  yAxisMin?: number;
  tooltipFormatter?: (name: string, value: any) => { name: string; value: string };
  className?: string;
}

/**
 * LineChart 组件 - 使用 Recharts 替代 @ant-design/charts
 *
 * 支持单条或多条折线，自动适配 shadcn/ui 主题
 */
export const CustomLineChart: React.FC<LineChartProps> = ({
  data,
  xField,
  yField,
  seriesField,
  height = 250,
  smooth = true,
  colors,
  yAxisMax,
  yAxisMin,
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

  const lineColors = colors || defaultColors;

  // 判断是否为多条线（有 seriesField）
  const isMultiLine = !!seriesField;

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
        <p className="text-sm font-medium">{props.payload[0].name}</p>
        {props.payload.map((entry: any, index: number) => (
          <p key={index} className="text-sm" style={{ color: entry.color }}>
            {entry.name}: {entry.value}
          </p>
        ))}
      </div>
    );
  };

  // Y轴域
  const yAxisDomain =
    yAxisMin !== undefined || yAxisMax !== undefined
      ? ([yAxisMin ?? 0, yAxisMax ?? 'auto'] as [number | 'auto', number | 'auto'])
      : undefined;

  return (
    <div className={className} style={{ height }}>
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={data} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" className="stroke-border/30" />
          <XAxis
            dataKey={xField}
            className="text-xs text-foreground-secondary"
            stroke="hsl(var(--muted-foreground))"
          />
          <YAxis
            domain={yAxisDomain}
            className="text-xs text-foreground-secondary"
            stroke="hsl(var(--muted-foreground))"
          />
          <Tooltip content={formatTooltip} />
          {isMultiLine && <Legend />}
          {isMultiLine && seriesField ? (
            // 多条线：根据 seriesField 分组
            Array.from(new Set(data.map((d) => d[seriesField] as string))).map((series, index) => (
              <Line
                key={series}
                type={smooth ? 'monotone' : 'linear'}
                dataKey={yField as string}
                stroke={lineColors[index % lineColors.length]}
                strokeWidth={2}
                dot={{ r: 4 }}
                activeDot={{ r: 6 }}
                name={series}
                // 这里需要重新处理数据格式，实际使用时可能需要转换
                connectNulls={false}
              />
            ))
          ) : (
            // 单条线
            Array.isArray(yField) ? (
              yField.map((field, index) => (
                <Line
                  key={field}
                  type={smooth ? 'monotone' : 'linear'}
                  dataKey={field}
                  stroke={lineColors[index % lineColors.length]}
                  strokeWidth={2}
                  dot={{ r: 4 }}
                  activeDot={{ r: 6 }}
                  name={field}
                  connectNulls={false}
                />
              ))
            ) : (
              <Line
                type={smooth ? 'monotone' : 'linear'}
                dataKey={yField}
                stroke={lineColors[0]}
                strokeWidth={2}
                dot={{ r: 4 }}
                activeDot={{ r: 6 }}
                connectNulls={false}
              />
            )
          )}
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
};

export default CustomLineChart;
