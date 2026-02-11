import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  ArrowLeft,
  AlertTriangle,
  CheckCircle,
  Clock,
  User,
  Bot,
  MessageSquare,
  Pill,
  FileText,
  TrendingUp,
  Plus,
  Loader2,
} from 'lucide-react';
import { CustomLineChart } from '@/components/charts';
import axios from 'axios';

// shadcn/ui components
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Avatar } from '@/components/ui/avatar';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Statistic } from '@/components/ui/statistic';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// ============================================
// TYPES
// ============================================

interface Message {
  id: number;
  isAi: boolean;
  content: string;
  time: string;
  created_at: string;
}

interface Task {
  id: number;
  title: string;
  scheduled_time: string;
  status: 'pending' | 'completed' | 'overdue';
  completed_at?: string;
  value?: { value: number; unit: string };
  notes?: string;
  order_type: string;
}

interface PatientDetailData {
  id: number;
  name: string;
  nickname?: string;
  avatar?: string;
  condition?: string;
  last_seen: string;
  last_consultation: string;
  alerts: Array<{ type: string; severity: string; message: string; value?: any }>;
  total_tasks: number;
  completed_tasks: number;
  completion_rate: number;
  recent_messages: Message[];
  today_tasks: Task[];
  compliance_rate: number;
  daily_compliance: Array<{ date: string; rate: number }>;
}

// ============================================
// MAIN COMPONENT
// ============================================

const RoundingDetail: React.FC = () => {
  const { patientId } = useParams<{ patientId: string }>();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [patientData, setPatientData] = useState<PatientDetailData | null>(null);

  // 加载患者详情数据
  useEffect(() => {
    const fetchPatientDetail = async () => {
      if (!patientId) {
        navigate('/rounding');
        return;
      }

      try {
        setLoading(true);
        const response = await axios.get<PatientDetailData>(
          `${API_BASE}/rounding/patients/${patientId}`
        );
        setPatientData(response.data);
      } catch (error) {
        console.error('Failed to fetch patient detail:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchPatientDetail();
  }, [patientId, navigate]);

  if (loading) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="flex flex-col items-center gap-4">
          <Loader2 className="h-8 w-8 animate-spin text-primary" />
          <p className="text-sm text-foreground-secondary">加载患者数据...</p>
        </div>
      </div>
    );
  }

  if (!patientData) {
    return (
      <div className="min-h-screen bg-background flex flex-col items-center justify-center p-6">
        <p className="text-foreground-secondary mb-4">患者数据不存在</p>
        <Button onClick={() => navigate('/rounding')}>返回列表</Button>
      </div>
    );
  }

  // 图表数据
  const chartData = patientData.daily_compliance.map((d) => ({
    date: d.date,
    rate: d.rate,
  }));

  const tooltipFormatter = (_name: string, value: any) => ({
    name: '完成率',
    value: `${value}%`,
  });

  const getTaskStatusText = (status: string) => {
    switch (status) {
      case 'completed': return '已完成';
      case 'overdue': return '已超时';
      default: return '待完成';
    }
  };

  const getTaskStatusVariant = (status: string): 'success' | 'warning' | 'default' => {
    switch (status) {
      case 'completed': return 'success';
      case 'overdue': return 'warning';
      default: return 'default';
    }
  };

  return (
    <div className="min-h-screen bg-background p-6">
      <div className="max-w-7xl mx-auto">
        {/* 顶部导航 */}
        <div className="mb-6">
          <Button
            variant="ghost"
            onClick={() => navigate('/rounding')}
            className="gap-2"
          >
            <ArrowLeft className="h-4 w-4" />
            返回患者列表
          </Button>
        </div>

        {/* 患者信息 + 预警横幅 */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 mb-6">
          {/* 患者信息 */}
          <Card className="lg:col-span-1">
            <CardContent className="p-6">
              <div className="flex items-start gap-4">
                <Avatar className="h-16 w-16" fallback={patientData.name.charAt(0)} />
                <div className="flex-1 min-w-0">
                  <h2 className="text-xl font-semibold text-foreground mb-1">
                    {patientData.name}
                  </h2>
                  <p className="text-sm text-foreground-secondary mb-2">
                    {patientData.condition || '居家患者'}
                  </p>
                  <div className="space-y-1">
                    <p className="text-xs text-foreground-secondary flex items-center gap-1.5">
                      <Clock className="h-3 w-3" />
                      上次问诊: {patientData.last_consultation}
                    </p>
                    <p className="text-xs text-foreground-secondary">
                      上次活跃: {patientData.last_seen}
                    </p>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* 预警信息 */}
          <Card className="lg:col-span-2">
            <CardContent className="p-4">
              <div className="space-y-3">
                {patientData.alerts.length > 0 ? (
                  patientData.alerts.map((alert, index) => (
                    <Alert
                      key={index}
                      variant={alert.severity === 'high' ? 'destructive' : 'warning'}
                      icon={
                        alert.severity === 'high' ? (
                          <AlertTriangle className="h-4 w-4" />
                        ) : (
                          <AlertTriangle className="h-4 w-4" />
                        )
                      }
                    >
                      <AlertDescription>
                        <span className="font-medium">
                          {alert.severity === 'high' ? '危险预警' : '注意事项'}
                        </span>
                        : {alert.message}
                      </AlertDescription>
                    </Alert>
                  ))
                ) : (
                  <Alert variant="success" icon={<CheckCircle className="h-4 w-4" />}>
                    <AlertDescription>
                      <span className="font-medium">暂无预警</span>
                      : 患者当前状态正常，无异常预警
                    </AlertDescription>
                  </Alert>
                )}
              </div>
            </CardContent>
          </Card>
        </div>

        {/* 今日统计 */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
          <Card>
            <CardContent className="p-4">
              <Statistic
                title="今日任务"
                value={patientData.total_tasks}
                suffix={`/ ${patientData.completed_tasks}`}
                prefix={<FileText className="h-4 w-4" />}
              />
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4">
              <Statistic
                title="完成率"
                value={patientData.completion_rate}
                suffix="%"
                valueStyle={{
                  color:
                    patientData.completion_rate >= 80
                      ? 'hsl(var(--success))'
                      : patientData.completion_rate >= 50
                        ? 'hsl(var(--warning))'
                        : 'hsl(var(--danger))',
                }}
              />
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4">
              <Statistic
                title="近7天平均"
                value={patientData.compliance_rate}
                suffix="%"
                prefix={<TrendingUp className="h-4 w-4" />}
                valueStyle={{ color: 'hsl(var(--info))' }}
              />
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4">
              <Statistic
                title="未完成"
                value={patientData.total_tasks - patientData.completed_tasks}
                valueStyle={{
                  color:
                    patientData.total_tasks - patientData.completed_tasks > 0
                      ? 'hsl(var(--warning))'
                      : 'hsl(var(--success))',
                }}
              />
            </CardContent>
          </Card>
        </div>

        {/* 中间区域：对话 + 医嘱 */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 mb-6">
          {/* 左侧：最近对话 */}
          <Card>
            <CardHeader className="flex flex-row items-center justify-between pb-4">
              <CardTitle className="text-base flex items-center gap-2">
                <MessageSquare className="h-4 w-4" />
                最近对话
              </CardTitle>
              <Button variant="link" size="sm" className="h-auto p-0">
                查看全部
              </Button>
            </CardHeader>
            <CardContent className="pt-0">
              <div className="space-y-4">
                {patientData.recent_messages.map((msg) => (
                  <div
                    key={msg.id}
                    className={`flex items-start gap-3 ${msg.isAi ? '' : 'flex-row-reverse'}`}
                  >
                    <Avatar
                      className={`h-8 w-8 ${msg.isAi ? 'bg-primary text-primary-foreground' : 'bg-muted'}`}
                      fallback={msg.isAi ? <Bot className="h-4 w-4" /> : <User className="h-4 w-4" />}
                    />
                    <div
                      className={`max-w-[80%] rounded-lg px-3 py-2 ${
                        msg.isAi
                          ? 'bg-muted text-foreground'
                          : 'bg-primary text-primary-foreground'
                      }`}
                    >
                      <p className="text-sm">{msg.content}</p>
                      <p className={`text-xs mt-1 ${msg.isAi ? 'text-foreground-secondary' : 'text-primary-foreground/70'}`}>
                        {msg.time}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* 右侧：医嘱列表 */}
          <Card>
            <CardHeader className="flex flex-row items-center justify-between pb-4">
              <CardTitle className="text-base flex items-center gap-2">
                <Pill className="h-4 w-4" />
                今日医嘱
              </CardTitle>
              <Button size="sm" className="gap-1">
                <Plus className="h-3.5 w-3.5" />
                添加医嘱
              </Button>
            </CardHeader>
            <CardContent className="pt-0">
              <div className="space-y-3">
                {patientData.today_tasks.map((task) => (
                  <div
                    key={task.id}
                    className="flex items-start justify-between gap-3 p-3 rounded-lg border border-border bg-surface-alt/50"
                  >
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-1.5 mb-1">
                        {task.status === 'completed' && (
                          <CheckCircle className="h-4 w-4 text-success shrink-0" />
                        )}
                        {task.status === 'overdue' && (
                          <AlertTriangle className="h-4 w-4 text-danger shrink-0" />
                        )}
                        <span className="text-sm font-medium text-foreground">
                          {task.title}
                        </span>
                      </div>
                      <p className="text-xs text-foreground-secondary mb-1">
                        计划时间: {task.scheduled_time}
                        {task.completed_at && ` · 完成于 ${task.completed_at}`}
                      </p>
                      {task.value && (
                        <div className="text-xs text-foreground">
                          {task.value.value} {task.value.unit}
                        </div>
                      )}
                      {task.notes && (
                        <p className="text-xs text-foreground-secondary mt-1">{task.notes}</p>
                      )}
                    </div>
                    <Badge variant={getTaskStatusVariant(task.status)} className="shrink-0">
                      {getTaskStatusText(task.status)}
                    </Badge>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>

        {/* 底部：依从性趋势 */}
        <Card>
          <CardHeader className="pb-4">
            <CardTitle className="text-base flex items-center gap-2">
              <TrendingUp className="h-4 w-4" />
              依从性趋势（近7天）
            </CardTitle>
          </CardHeader>
          <CardContent className="pt-0">
            <div className="h-[200px]">
              <CustomLineChart
                data={chartData}
                xField="date"
                yField="rate"
                height={200}
                smooth={true}
                yAxisMax={100}
                yAxisMin={0}
                colors={['#3b82f6']}
                tooltipFormatter={tooltipFormatter}
              />
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default RoundingDetail;
