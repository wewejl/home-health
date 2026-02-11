import React, { useEffect, useState } from 'react';
import { Loader2, TrendingUp } from 'lucide-react';
import { CustomLineChart } from '@/components/charts';
import { statsApi } from '../api';

// shadcn/ui components
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Select, SelectTrigger, SelectValue, SelectContent, SelectItem } from '@/components/ui/select';
import { Table, TableBody, TableHead, TableHeader, TableRow, TableCell } from '@/components/ui/table';

interface DailyStats {
  date: string;
  sessions: number;
  messages: number;
}

interface AuditLog {
  id: number;
  admin_user_id: number;
  action: string;
  resource_type: string;
  resource_id: string;
  created_at: string;
}

const Stats: React.FC = () => {
  const [loading, setLoading] = useState(true);
  const [trends, setTrends] = useState<DailyStats[]>([]);
  const [logs, setLogs] = useState<AuditLog[]>([]);
  const [days, setDays] = useState(7);

  useEffect(() => {
    fetchData();
  }, [days]);

  const fetchData = async () => {
    setLoading(true);
    try {
      const [trendsRes, logsRes] = await Promise.all([
        statsApi.getTrends(days),
        statsApi.getLogs({ limit: 20 }),
      ]);
      setTrends(trendsRes.data.daily_stats || []);
      setLogs(logsRes.data || []);
    } catch (error) {
      console.error('Failed to fetch stats:', error);
    } finally {
      setLoading(false);
    }
  };

  // 图表数据 - 转换为多系列折线图格式
  const chartData = trends.map((item) => ({
    date: item.date,
    会话数: item.sessions,
    消息数: item.messages,
  }));

  const tooltipFormatter = (name: string, value: any) => ({
    name,
    value: `${value}`,
  });

  if (loading) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="flex flex-col items-center gap-4">
          <Loader2 className="h-8 w-8 animate-spin text-primary" />
          <p className="text-sm text-foreground-secondary">加载统计数据...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background p-6">
      <div className="max-w-7xl mx-auto">
        {/* 页面标题 */}
        <div className="mb-6">
          <h1 className="text-2xl font-semibold text-foreground flex items-center gap-2">
            <TrendingUp className="h-6 w-6" />
            统计分析
          </h1>
        </div>

        {/* 趋势图表 */}
        <Card className="mb-6">
          <CardHeader className="flex flex-row items-center justify-between pb-4">
            <CardTitle className="text-base">趋势图表</CardTitle>
            <Select value={String(days)} onValueChange={(v) => setDays(Number(v))}>
              <SelectTrigger className="w-[120px]">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="7">最近7天</SelectItem>
                <SelectItem value="14">最近14天</SelectItem>
                <SelectItem value="30">最近30天</SelectItem>
              </SelectContent>
            </Select>
          </CardHeader>
          <CardContent>
            <div className="h-[300px]">
              <CustomLineChart
                data={chartData}
                xField="date"
                yField={['会话数', '消息数']}
                height={300}
                smooth={true}
                tooltipFormatter={tooltipFormatter}
              />
            </div>
          </CardContent>
        </Card>

        {/* 表格区域 */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          {/* 趋势数据表格 */}
          <Card>
            <CardHeader className="pb-4">
              <CardTitle className="text-base">趋势数据表格</CardTitle>
            </CardHeader>
            <CardContent className="p-0">
              <div className="max-h-[400px] overflow-auto">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>日期</TableHead>
                      <TableHead>会话数</TableHead>
                      <TableHead>消息数</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {trends.map((item) => (
                      <TableRow key={item.date}>
                        <TableCell>{item.date}</TableCell>
                        <TableCell>{item.sessions}</TableCell>
                        <TableCell>{item.messages}</TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>
            </CardContent>
          </Card>

          {/* 审计日志 */}
          <Card>
            <CardHeader className="pb-4">
              <CardTitle className="text-base">审计日志</CardTitle>
            </CardHeader>
            <CardContent className="p-0">
              <div className="max-h-[400px] overflow-auto">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead className="w-[60px]">ID</TableHead>
                      <TableHead className="w-[80px]">管理员ID</TableHead>
                      <TableHead className="w-[80px]">操作</TableHead>
                      <TableHead>资源类型</TableHead>
                      <TableHead className="w-[100px]">时间</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {logs.map((log) => (
                      <TableRow key={log.id}>
                        <TableCell className="text-foreground-secondary">{log.id}</TableCell>
                        <TableCell>{log.admin_user_id}</TableCell>
                        <TableCell>
                          <span className="px-2 py-0.5 rounded bg-primary/10 text-primary text-xs">
                            {log.action}
                          </span>
                        </TableCell>
                        <TableCell className="text-foreground-secondary">{log.resource_type}</TableCell>
                        <TableCell className="text-foreground-secondary text-xs">
                          {log.created_at ? new Date(log.created_at).toLocaleString() : '-'}
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
};

export default Stats;
