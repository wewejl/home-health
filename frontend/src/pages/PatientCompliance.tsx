import React, { useEffect, useState } from 'react';
import { medicalOrdersApi } from '../api';
import dayjs from 'dayjs';
import {
  TrendingUp,
  TrendingDown,
  CheckCircle,
  AlertTriangle,
  Calendar,
  Activity,
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { DatePicker } from '@/components/ui/date-picker';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { StatCardGrid } from '@/components/medical/stat-card';
import { PageHeader } from '@/components/medical/page-header';
import { Progress } from '@/components/ui/progress';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
// 使用自定义图表组件（基于 Recharts）
import { CustomLineChart, CustomColumnChart, CustomPieChart } from '@/components/charts';
import { getThemeColors } from '@/lib/theme';

// 依从性数据类型
interface DailyCompliance {
  date: string;
  total: number;
  completed: number;
  overdue: number;
  pending: number;
  rate: number;
}

interface WeeklyCompliance {
  daily_rates: number[];
  average_rate: number;
  dates: string[];
}

interface AbnormalRecord {
  id: number;
  task_title: string;
  value_data: Record<string, any>;
  completed_at: string;
  alert_type?: string;
}

const PatientCompliance: React.FC = () => {
  // const [loading, setLoading] = useState(false);
  const [selectedPatient, setSelectedPatient] = useState<number>(1);
  const [dateRange, setDateRange] = useState<{
    start: Date;
    end: Date;
  }>({
    start: dayjs().subtract(7, 'day').toDate(),
    end: dayjs().toDate(),
  });

  // 依从性数据
  const [weeklyData, setWeeklyData] = useState<WeeklyCompliance | null>(null);
  const [dailyData, setDailyData] = useState<DailyCompliance[]>([]);
  const [abnormalRecords, setAbnormalRecords] = useState<AbnormalRecord[]>([]);

  // 患者列表（模拟数据，实际应从用户API获取）
  const patients = [
    { id: 1, name: '测试患者' },
    { id: 2, name: '张三' },
    { id: 3, name: '李四' },
  ];

  // 获取周依从性数据
  const fetchWeeklyCompliance = async () => {
    try {
      const response = await medicalOrdersApi.getWeeklyCompliance();
      setWeeklyData(response.data);

      // 转换为每日数据格式
      const daily: DailyCompliance[] = response.data.dates.map((date: string, index: number) => ({
        date,
        total: 10, // 模拟数据
        completed: Math.round(10 * response.data.daily_rates[index]),
        overdue: Math.round(Math.random() * 2),
        pending: Math.round(10 * (1 - response.data.daily_rates[index])),
        rate: response.data.daily_rates[index],
      }));
      setDailyData(daily);
    } catch (error) {
      console.error('Failed to fetch weekly compliance:', error);
    }
  };

  // 获取异常记录
  const fetchAbnormalRecords = async () => {
    try {
      const response = await medicalOrdersApi.getAbnormalRecords(30);
      setAbnormalRecords(response.data);
    } catch (error) {
      console.error('Failed to fetch abnormal records:', error);
    }
  };

  useEffect(() => {
    // setLoading(true);
    Promise.all([fetchWeeklyCompliance(), fetchAbnormalRecords()]).finally(() => {
      // setLoading(false);
    });
  }, [selectedPatient]);

  // 计算统计数据
  const averageRate = weeklyData?.average_rate || 0;
  const totalTasks = dailyData.reduce((sum, day) => sum + day.total, 0);
  const completedTasks = dailyData.reduce((sum, day) => sum + day.completed, 0);
  const overdueTasks = dailyData.reduce((sum, day) => sum + day.overdue, 0);

  // 趋势图表数据
  const trendLineData = dailyData.map((day) => ({
    date: dayjs(day.date).format('MM/DD'),
    value: Math.round(day.rate * 100),
  }));

  const barChartData = dailyData.map((day) => ({
    date: dayjs(day.date).format('MM/DD'),
    总任务数: day.total,
    已完成: day.completed,
  }));

  // 饼图数据
  const pieData = [
    { type: '已完成', value: completedTasks },
    { type: '已超时', value: overdueTasks },
    { type: '待完成', value: totalTasks - completedTasks - overdueTasks },
  ];

  // 获取主题颜色
  const themeColors = getThemeColors();

  // 折线图配置
  const lineTooltipFormatter = (_name: string, value: any) => ({
    name: '完成率',
    value: `${value}%`,
  });

  // 柱状图配置
  const barTooltipFormatter = (name: string, value: any) => ({
    name,
    value: `${value}`,
  });

  // 饼图配置
  const pieTooltipFormatter = (name: string, value: any) => ({
    name,
    value: `${value}`,
  });

  // 异常记录表格列
  const abnormalColumns = [
    { title: '任务', key: 'task', render: (_: any, record: AbnormalRecord) => record.task_title },
    {
      title: '异常值',
      key: 'value',
      render: (_: any, record: AbnormalRecord) => {
        if (!record.value_data) return '-';
        try {
          return JSON.stringify(record.value_data);
        } catch {
          return '-';
        }
      },
    },
    {
      title: '记录时间',
      key: 'time',
      render: (_: any, record: AbnormalRecord) => dayjs(record.completed_at).format('MM-DD HH:mm'),
    },
    {
      title: '类型',
      key: 'type',
      render: (_: any, record: AbnormalRecord) => {
        const typeMap: Record<string, { text: string; variant: 'success' | 'warning' | 'danger' | 'info' | 'default' }> = {
          glucose_low: { text: '低血糖', variant: 'danger' },
          glucose_high: { text: '高血糖', variant: 'warning' },
          bp_high: { text: '高血压', variant: 'danger' },
          temp_high: { text: '发烧', variant: 'warning' },
        };
        const config = typeMap[record.alert_type || ''] || { text: record.alert_type || '-', variant: 'default' as const };
        return <Badge variant={config.variant}>{config.text}</Badge>;
      },
    },
  ];

  // 统计卡片
  const getComplianceVariant = (): 'success' | 'warning' | 'danger' | 'primary' | 'info' => {
    if (averageRate >= 0.8) return 'success';
    if (averageRate >= 0.6) return 'warning';
    return 'danger';
  };

  const getOverdueVariant = (): 'success' | 'danger' => {
    return overdueTasks > 0 ? 'danger' : 'success';
  };

  const statsCards = [
    {
      title: '平均依从率',
      value: Math.round(averageRate * 100),
      unit: '%',
      icon: averageRate >= 0.8 ? <TrendingUp className="h-5 w-5" /> : <TrendingDown className="h-5 w-5" />,
      variant: getComplianceVariant(),
    },
    {
      title: '总任务数',
      value: totalTasks,
      icon: <Calendar className="h-5 w-5" />,
      variant: 'primary' as const,
    },
    {
      title: '已完成',
      value: completedTasks,
      icon: <CheckCircle className="h-5 w-5" />,
      variant: 'success' as const,
    },
    {
      title: '已超时',
      value: overdueTasks,
      icon: <AlertTriangle className="h-5 w-5" />,
      variant: getOverdueVariant(),
    },
  ];

  return (
    <div className="space-y-6">
      {/* 页面头部 */}
      <PageHeader
        title="患者依从性分析"
        description="查看患者医嘱执行情况、依从性趋势和异常记录"
        actions={
          <div className="flex items-center gap-2">
            <Select
              value={selectedPatient.toString()}
              onValueChange={(v) => setSelectedPatient(Number(v))}
            >
              <SelectTrigger className="w-[120px]">
                <SelectValue placeholder="选择患者" />
              </SelectTrigger>
              <SelectContent>
                {patients.map((p) => (
                  <SelectItem key={p.id} value={p.id.toString()}>
                    {p.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            <div className="flex items-center gap-2 border border-border rounded-sm px-3 py-1.5">
              <DatePicker
                value={dateRange.start}
                onChange={(date) => date && setDateRange(prev => ({ ...prev, start: date }))}
              />
              <span className="text-foreground-secondary">-</span>
              <DatePicker
                value={dateRange.end}
                onChange={(date) => date && setDateRange(prev => ({ ...prev, end: date }))}
              />
            </div>
          </div>
        }
      />

      {/* 统计概览 */}
      <StatCardGrid items={statsCards} cols={4} />

      {/* 趋势图表 */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle className="text-base font-medium">近7天依从性趋势</CardTitle>
          </CardHeader>
          <CardContent>
            <CustomLineChart
              data={trendLineData}
              xField="date"
              yField="value"
              height={250}
              smooth={true}
              yAxisMax={100}
              yAxisMin={0}
              colors={[themeColors.colorPrimary]}
              tooltipFormatter={lineTooltipFormatter}
            />
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle className="text-base font-medium">任务完成分布</CardTitle>
          </CardHeader>
          <CardContent>
            <CustomPieChart
              data={pieData}
              nameField="type"
              valueField="value"
              height={200}
              radius={0.8}
              innerRadius={0.6}
              colors={[themeColors.colorSuccess, themeColors.colorError, themeColors.colorWarning]}
              legendPosition="bottom"
              tooltipFormatter={pieTooltipFormatter}
            />
          </CardContent>
        </Card>
      </div>

      {/* 每日详细数据 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <Card>
          <CardHeader>
            <CardTitle className="text-base font-medium">每日任务详情</CardTitle>
          </CardHeader>
          <CardContent>
            <CustomColumnChart
              data={barChartData}
              xField="date"
              yField={['总任务数', '已完成']}
              height={200}
              columnWidthRatio={0.6}
              colors={[themeColors.colorPrimary, themeColors.colorSuccess]}
              legendPosition="top"
              tooltipFormatter={barTooltipFormatter}
            />
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle className="text-base font-medium">近7天完成率</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {dailyData.map((day) => {
                const percent = Math.round(day.rate * 100);
                return (
                  <div key={day.date} className="space-y-2">
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-foreground">
                        {dayjs(day.date).format('MM月DD日')}
                      </span>
                      <span className="text-foreground-secondary">
                        ({day.completed}/{day.total})
                      </span>
                    </div>
                    <div className="space-y-1">
                      <Progress
                        value={percent}
                        max={100}
                        className={cn(
                          "h-2",
                          percent >= 80 && "[&_div]:bg-success",
                          percent >= 60 && percent < 80 && "[&_div]:bg-warning",
                          percent < 60 && "[&_div]:bg-danger"
                        )}
                      />
                    </div>
                  </div>
                );
              })}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* 异常记录 */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <AlertTriangle className="h-5 w-5 text-danger" />
            <span>异常监测记录</span>
            <Badge variant="danger">{abnormalRecords.length}</Badge>
          </CardTitle>
        </CardHeader>
        <CardContent>
          {abnormalRecords.length === 0 ? (
            <Alert variant="success">
              <CheckCircle className="h-4 w-4" />
              <AlertTitle>暂无异常记录</AlertTitle>
              <AlertDescription>
                患者近30天内没有监测到异常数值
              </AlertDescription>
            </Alert>
          ) : (
            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow>
                    {abnormalColumns.map((col, i) => (
                      <TableHead key={i}>{col.title}</TableHead>
                    ))}
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {abnormalRecords.map((record) => (
                    <TableRow key={record.id}>
                      {abnormalColumns.map((col, i) => (
                        <TableCell key={i}>{col.render(null, record)}</TableCell>
                      ))}
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          )}
        </CardContent>
      </Card>

      {/* 健康建议 */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Activity className="h-5 w-5" />
            健康建议
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {averageRate >= 0.8 ? (
              <Alert variant="success">
                <CheckCircle className="h-4 w-4" />
                <AlertTitle>依从性优秀</AlertTitle>
                <AlertDescription>
                  患者近7天医嘱执行率保持在80%以上，请继续保持！
                </AlertDescription>
              </Alert>
            ) : averageRate >= 0.6 ? (
              <Alert>
                <AlertTriangle className="h-4 w-4" />
                <AlertTitle>依从性一般</AlertTitle>
                <AlertDescription>
                  患者近7天医嘱执行率为60%-80%，建议关注提醒，帮助患者按时完成医嘱。
                </AlertDescription>
              </Alert>
            ) : (
              <Alert className="border-danger/50 text-danger">
                <AlertTriangle className="h-4 w-4" />
                <AlertTitle>依从性偏低</AlertTitle>
                <AlertDescription>
                  患者近7天医嘱执行率低于60%，需要重点关注，建议联系患者了解原因并提供帮助。
                </AlertDescription>
              </Alert>
            )}

            {overdueTasks > 0 && (
              <Alert>
                <AlertTriangle className="h-4 w-4" />
                <AlertTitle>发现 {overdueTasks} 个超时任务</AlertTitle>
                <AlertDescription>
                  有部分任务未按时完成，建议患者设置提醒，或联系家属协助监督。
                </AlertDescription>
              </Alert>
            )}

            {abnormalRecords.length > 0 && (
              <Alert className="border-danger/50 text-danger">
                <AlertTriangle className="h-4 w-4" />
                <AlertTitle>发现 {abnormalRecords.length} 条异常记录</AlertTitle>
                <AlertDescription>
                  监测到异常数值，建议及时就医或调整治疗方案。
                </AlertDescription>
              </Alert>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default PatientCompliance;
