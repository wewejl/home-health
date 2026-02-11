import { useState, useEffect } from 'react';
import { Calendar, CheckCircle2, Clock, AlertTriangle, Loader2 } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { doctorApi } from '@/api';
import dayjs from 'dayjs';

interface TaskInstance {
  id: number;
  order_id: number;
  patient_id: number;
  scheduled_date: string;
  scheduled_time: string;
  status: string;
  completed_at?: string;
  order_title?: string;
  order_type?: string;
}

interface ComplianceSummary {
  date: string;
  total: number;
  completed: number;
  overdue: number;
  pending: number;
  rate: number;
}

interface TasksTabProps {
  patientId: number;
}

const TasksTab: React.FC<TasksTabProps> = ({ patientId }) => {
  const [selectedDate, setSelectedDate] = useState(dayjs().format('YYYY-MM-DD'));
  const [taskList, setTaskList] = useState<{
    pending: TaskInstance[];
    completed: TaskInstance[];
    overdue: TaskInstance[];
    summary: ComplianceSummary;
  } | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetchTasks(selectedDate);
  }, [patientId, selectedDate]);

  const fetchTasks = async (date: string) => {
    setLoading(true);
    try {
      const { data } = await doctorApi.getPatientTasks(patientId, date);
      setTaskList(data);
    } catch (error) {
      console.error('Failed to fetch tasks:', error);
    } finally {
      setLoading(false);
    }
  };

  const getOrderTypeBadge = (type?: string) => {
    if (!type) return <Badge variant="outline">-</Badge>;
    const typeMap: Record<string, { label: string; variant: 'default' | 'secondary' | 'outline' | 'destructive' }> = {
      'medication': { label: '用药', variant: 'default' },
      'monitoring': { label: '监测', variant: 'secondary' },
      'behavior': { label: '行为', variant: 'outline' },
      'followup': { label: '复诊', variant: 'destructive' },
    };
    const info = typeMap[type] || { label: type, variant: 'outline' as const };
    return <Badge variant={info.variant}>{info.label}</Badge>;
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircle2 className="h-5 w-5 text-success" />;
      case 'pending':
        return <Clock className="h-5 w-5 text-warning" />;
      case 'overdue':
        return <AlertTriangle className="h-5 w-5 text-danger" />;
      default:
        return <Clock className="h-5 w-5 text-muted-foreground" />;
    }
  };

  const getStatusBadge = (status: string) => {
    const statusMap: Record<string, { label: string; variant: 'default' | 'secondary' | 'outline' | 'destructive' }> = {
      'pending': { label: '待完成', variant: 'outline' },
      'completed': { label: '已完成', variant: 'default' },
      'overdue': { label: '已超时', variant: 'destructive' },
      'skipped': { label: '已跳过', variant: 'outline' },
    };
    const info = statusMap[status] || { label: status, variant: 'outline' as const };
    return <Badge variant={info.variant} className={status === 'completed' ? 'bg-medical-success' : ''}>{info.label}</Badge>;
  };

  const getRateColor = (rate: number) => {
    if (rate >= 0.8) return 'text-success';
    if (rate >= 0.5) return 'text-warning';
    return 'text-danger';
  };

  const TaskList = ({ tasks, title, emptyText }: { tasks: TaskInstance[]; title: string; emptyText: string }) => (
    <Card className="h-[calc(100vh-400px)] overflow-hidden flex flex-col">
      <CardHeader className="pb-3">
        <CardTitle className="text-base">{title}</CardTitle>
      </CardHeader>
      <CardContent className="flex-1 overflow-auto p-0">
        {tasks.length === 0 ? (
          <div className="flex items-center justify-center h-full text-muted-foreground">
            <p className="text-sm">{emptyText}</p>
          </div>
        ) : (
          <div className="divide-y">
            {tasks.map((task) => (
              <div key={task.id} className="p-4">
                <div className="flex items-start gap-3">
                  <div className="flex-shrink-0 mt-0.5">
                    {getStatusIcon(task.status)}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between mb-1">
                      <p className="font-medium text-sm truncate">{task.order_title || '未命名医嘱'}</p>
                      {getStatusBadge(task.status)}
                    </div>
                    <div className="flex items-center gap-2 text-xs text-muted-foreground">
                      {getOrderTypeBadge(task.order_type)}
                      <span>计划时间: {task.scheduled_time}</span>
                      {task.completed_at && (
                        <span>完成时间: {dayjs(task.completed_at).format('HH:mm')}</span>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );

  return (
    <div className="p-4">
      {/* 头部：日期选择 */}
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-lg font-semibold">任务执行情况</h3>
        <div className="flex items-center gap-2">
          <Calendar className="h-4 w-4 text-muted-foreground" />
          <Input
            type="date"
            value={selectedDate}
            onChange={(e) => setSelectedDate(e.target.value)}
            className="w-[150px]"
          />
        </div>
      </div>

      {loading && (
        <div className="flex items-center justify-center py-8">
          <Loader2 className="h-5 w-5 animate-spin mr-2" />
          <span>加载中...</span>
        </div>
      )}

      {taskList && !loading && (
        <>
          {/* 统计卡片 */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
            <Card className="stat-card">
              <CardContent className="p-4">
                <p className="text-xs text-muted-foreground uppercase tracking-wide mb-1">总任务数</p>
                <p className="text-2xl font-bold">{taskList.summary.total}</p>
              </CardContent>
            </Card>

            <Card className="stat-card">
              <CardContent className="p-4">
                <p className="text-xs text-muted-foreground uppercase tracking-wide mb-1">已完成</p>
                <p className="text-2xl font-bold text-success">{taskList.summary.completed}</p>
              </CardContent>
            </Card>

            <Card className="stat-card">
              <CardContent className="p-4">
                <p className="text-xs text-muted-foreground uppercase tracking-wide mb-1">待完成</p>
                <p className="text-2xl font-bold text-warning">{taskList.summary.pending}</p>
              </CardContent>
            </Card>

            <Card className="stat-card">
              <CardContent className="p-4">
                <p className="text-xs text-muted-foreground uppercase tracking-wide mb-1">完成率</p>
                <p className={`text-2xl font-bold ${getRateColor(taskList.summary.rate)}`}>
                  {Math.round(taskList.summary.rate * 100)}%
                </p>
              </CardContent>
            </Card>
          </div>

          {/* 任务列表 */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <TaskList tasks={taskList.completed} title="已完成" emptyText="该日无已完成任务" />
            <TaskList tasks={taskList.pending} title="待完成" emptyText="该日无待完成任务" />
            <TaskList tasks={taskList.overdue} title="已超时" emptyText="该日无超时任务" />
          </div>
        </>
      )}

      {!taskList && !loading && (
        <Card>
          <CardContent className="flex items-center justify-center py-8 text-muted-foreground">
            <p>请选择日期查看任务</p>
          </CardContent>
        </Card>
      )}
    </div>
  );
};

export default TasksTab;
