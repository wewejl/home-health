import React from 'react';
import {
  PieChart,
  Pie,
  Cell,
  ResponsiveContainer,
  Tooltip,
  Legend,
} from 'recharts';
import { getThemeColors } from '@/lib/theme';

export interface PieChartData {
  type: string;
  value: number;
  [key: string]: string | number;
}

export interface CustomPieChartProps {
  data: PieChartData[];
  nameField?: string;
  valueField: string;
  height?: number;
  radius?: number;
  innerRadius?: number;
  colors?: string[];
  legendPosition?: 'top' | 'bottom' | 'left' | 'right';
  label?: boolean;
  tooltipFormatter?: (name: string, value: any) => { name: string; value: string };
  className?: string;
}

/**
 * PieChart 组件 - 使用 Recharts 替代 @ant-design/charts Pie
 *
 * 支持普通饼图和环形图，自动适配 shadcn/ui 主题
 */
export const CustomPieChart: React.FC<CustomPieChartProps> = ({
  data,
  nameField = 'type',
  valueField = 'value',
  height = 200,
  radius = 0.8,
  innerRadius = 0.6,
  colors,
  legendPosition = 'bottom',
  label = false,
  tooltipFormatter,
  className,
}) => {
  const themeColors = getThemeColors();
  const defaultColors = [
    themeColors.colorSuccess,
    themeColors.colorError,
    themeColors.colorWarning,
    themeColors.colorInfo,
    themeColors.colorPrimary,
  ];

  const pieColors = colors || defaultColors;

  // 处理 tooltip 格式化
  const formatTooltip = (props: any) => {
    if (!props.payload || props.payload.length === 0) return null;

    const data = props.payload[0];
    const name = data.payload[nameField];
    const value = data.payload[valueField];

    if (tooltipFormatter) {
      const result = tooltipFormatter(name, value);
      return (
        <div className="bg-popover text-popover-foreground border border-border rounded-lg shadow-lg p-2">
          <p className="text-sm font-medium">{result.name}</p>
          <p className="text-sm">{result.value}</p>
        </div>
      );
    }

    return (
      <div className="bg-popover text-popover-foreground border border-border rounded-lg shadow-lg p-2">
        <p className="text-sm font-medium">{name}</p>
        <p className="text-sm">数量: {value}</p>
      </div>
    );
  };

  // 自定义标签
  const renderLabel = (entry: any) => {
    const val = entry[valueField];
    return `${typeof val === 'number' ? val : 0}`;
  };

  // Legend 对齐方式
  const getLegendAlign = () => {
    switch (legendPosition) {
      case 'left': return 'flex-start';
      case 'right': return 'flex-end';
      default: return 'center';
    }
  };

  // 计算实际半径（基于容器大小）
  const outerRadius = radius * 80; // 假设容器约100px
  const innerRadiusValue = innerRadius * 80;

  return (
    <div className={className} style={{ height }}>
      <ResponsiveContainer width="100%" height="100%">
        <PieChart>
          <Pie
            data={data}
            cx="50%"
            cy="50%"
            label={label ? renderLabel : false}
            labelLine={false}
            outerRadius={outerRadius}
            innerRadius={innerRadiusValue}
            paddingAngle={2}
            dataKey={valueField}
          >
            {data.map((_entry, index) => (
              <Cell
                key={`cell-${index}`}
                fill={pieColors[index % pieColors.length]}
              />
            ))}
          </Pie>
          <Tooltip content={formatTooltip} />
          <Legend
            verticalAlign={legendPosition === 'bottom' ? 'bottom' : 'top'}
            align={getLegendAlign() as any}
            iconType="circle"
          />
        </PieChart>
      </ResponsiveContainer>
    </div>
  );
};

export default CustomPieChart;
