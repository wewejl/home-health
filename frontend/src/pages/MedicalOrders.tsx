import React, { useEffect, useState } from 'react';
import { medicalOrdersApi } from '../api';
import dayjs from 'dayjs';
import {
  Plus,
  Edit,
  CheckCircle,
  Ban,
  Eye,
  Clock,
  Pill,
  FileText,
  Calendar,
  Bot,
  AlertCircle,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Dialog, DialogContent, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { DatePicker } from '@/components/ui/date-picker';
import { Tooltip } from '@/components/ui/tooltip';
import { Textarea } from '@/components/ui/textarea';
import { StatCardGrid } from '@/components/medical/stat-card';
import { PageHeader } from '@/components/medical/page-header';
import { useToast } from '@/components/ui/toast';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';

// 类型定义
interface MedicalOrder {
  id: number;
  patient_id: number;
  order_type: string;
  title: string;
  description?: string;
  schedule_type: string;
  start_date: string;
  end_date?: string;
  frequency?: string;
  reminder_times: string[];
  ai_generated: boolean;
  status: string;
  created_at: string;
  updated_at: string;
}

interface TaskInstance {
  id: number;
  order_id: number;
  patient_id: number;
  scheduled_date: string;
  scheduled_time: string;
  status: string;
  completed_at?: string;
  completion_notes?: string;
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

interface TaskListResponse {
  date: string;
  pending: TaskInstance[];
  completed: TaskInstance[];
  overdue: TaskInstance[];
  summary: ComplianceSummary;
}

// 医嘱类型配置
const ORDER_TYPE_CONFIG: Record<string, { label: string; variant: 'primary' | 'success' | 'warning' | 'info' | 'danger'; icon: React.ReactNode }> = {
  medication: { label: '用药', variant: 'primary', icon: <Pill className="h-3 w-3" /> },
  monitoring: { label: '监测', variant: 'success', icon: <FileText className="h-3 w-3" /> },
  behavior: { label: '行为', variant: 'warning', icon: <Clock className="h-3 w-3" /> },
  followup: { label: '复诊', variant: 'info', icon: <Calendar className="h-3 w-3" /> },
};

// 调度类型映射
const SCHEDULE_TYPE_MAP: Record<string, string> = {
  once: '一次性',
  daily: '每日',
  weekly: '每周',
  custom: '自定义',
};

// 状态配置
const STATUS_CONFIG: Record<string, { label: string; variant: 'default' | 'success' | 'warning' | 'danger' | 'info' | 'primary' }> = {
  draft: { label: '草稿', variant: 'default' },
  active: { label: '进行中', variant: 'primary' },
  completed: { label: '已完成', variant: 'success' },
  stopped: { label: '已停用', variant: 'danger' },
};

// 任务状态配置
const TASK_STATUS_CONFIG: Record<string, { label: string; variant: 'default' | 'success' | 'warning' | 'danger' | 'info' }> = {
  pending: { label: '待完成', variant: 'default' },
  completed: { label: '已完成', variant: 'success' },
  overdue: { label: '已超时', variant: 'danger' },
  skipped: { label: '已跳过', variant: 'warning' },
};

// 移除未使用的 TASK_STATUS_CONFIG 警告
void TASK_STATUS_CONFIG;

// 表单字段类型
interface FormField {
  value: string | Date | string[] | boolean;
  error?: string;
}

type FormData = Record<string, FormField>;

// 更新医嘱数据类型
interface UpdateOrderData {
  title?: string;
  description?: string;
  end_date?: string;
  frequency?: string;
  reminder_times?: string[];
}

const MedicalOrders: React.FC = () => {
  // 列表数据
  const [orders, setOrders] = useState<MedicalOrder[]>([]);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState<string>('');
  const [activeTab, setActiveTab] = useState('orders');

  // 今日任务数据
  const [todayTasks, setTodayTasks] = useState<TaskListResponse | null>(null);
  const [tasksLoading, setTasksLoading] = useState(true);

  // 移除未使用警告
  void tasksLoading;

  // 弹窗状态
  const [createModalVisible, setCreateModalVisible] = useState(false);
  const [editModalVisible, setEditModalVisible] = useState(false);
  const [detailModalVisible, setDetailModalVisible] = useState(false);
  const [currentOrder, setCurrentOrder] = useState<MedicalOrder | null>(null);

  // 表单状态
  const [formData, setFormData] = useState<FormData>({});

  // Toast hook
  const toast = useToast();

  // 获取医嘱列表
  const fetchOrders = async () => {
    try {
      setLoading(true);
      const response = await medicalOrdersApi.list(statusFilter);
      setOrders(response.data);
    } catch (error) {
      console.error('Failed to fetch orders:', error);
      toast.error('获取医嘱列表失败');
    } finally {
      setLoading(false);
    }
  };

  // 获取今日任务
  const fetchTodayTasks = async () => {
    try {
      setTasksLoading(true);
      const today = dayjs().format('YYYY-MM-DD');
      const response = await medicalOrdersApi.getDailyTasks(today);
      setTodayTasks(response.data);
    } catch (error) {
      console.error('Failed to fetch today tasks:', error);
    } finally {
      setTasksLoading(false);
    }
  };

  useEffect(() => {
    fetchOrders();
    fetchTodayTasks();
  }, [statusFilter]);

  // 创建医嘱
  const handleCreate = async () => {
    try {
      const data = {
        order_type: formData.order_type?.value as string,
        title: formData.title?.value as string,
        description: formData.description?.value as string | undefined,
        schedule_type: formData.schedule_type?.value as string,
        start_date: formData.start_date?.value instanceof Date
          ? dayjs(formData.start_date.value).format('YYYY-MM-DD')
          : dayjs().format('YYYY-MM-DD'),
        end_date: formData.end_date?.value instanceof Date
          ? dayjs(formData.end_date.value).format('YYYY-MM-DD')
          : undefined,
        frequency: formData.frequency?.value as string | undefined,
        reminder_times: Array.isArray(formData.reminder_times?.value)
          ? (formData.reminder_times.value as string[])
          : [],
        ai_generated: formData.ai_generated?.value as boolean ?? false,
      };

      await medicalOrdersApi.create(data);
      toast.success('医嘱创建成功');
      setCreateModalVisible(false);
      setFormData({});
      fetchOrders();
    } catch (error) {
      console.error('Create failed:', error);
      toast.error('创建失败');
    }
  };

  // 更新医嘱
  const handleUpdate = async () => {
    if (!currentOrder) return;
    try {
      const data: UpdateOrderData = {};
      if (formData.title?.value) data.title = String(formData.title.value);
      if (formData.description?.value) data.description = String(formData.description.value);
      if (formData.end_date?.value instanceof Date) {
        data.end_date = dayjs(formData.end_date.value).format('YYYY-MM-DD');
      }
      if (formData.frequency?.value) data.frequency = String(formData.frequency.value);
      if (Array.isArray(formData.reminder_times?.value)) {
        data.reminder_times = formData.reminder_times.value as string[];
      }

      await medicalOrdersApi.update(currentOrder.id, data);
      toast.success('医嘱更新成功');
      setEditModalVisible(false);
      setCurrentOrder(null);
      setFormData({});
      fetchOrders();
    } catch (error) {
      console.error('Update failed:', error);
      toast.error('更新失败');
    }
  };

  // 激活医嘱
  const handleActivate = async (id: number) => {
    try {
      await medicalOrdersApi.activate(id, true);
      toast.success('医嘱已激活');
      fetchOrders();
    } catch (error) {
      console.error('Activate failed:', error);
      toast.error('激活失败');
    }
  };

  // 打开编辑弹窗
  const openEditModal = (order: MedicalOrder) => {
    setCurrentOrder(order);
    setFormData({
      title: { value: order.title },
      description: { value: order.description || '' },
      end_date: { value: order.end_date ? new Date(order.end_date) : '' },
      frequency: { value: order.frequency || '' },
      reminder_times: { value: order.reminder_times || [] },
    });
    setEditModalVisible(true);
  };

  // 打开详情弹窗
  const openDetailModal = (order: MedicalOrder) => {
    setCurrentOrder(order);
    setDetailModalVisible(true);
  };

  // 更新表单字段
  const updateFormField = (name: string, value: string | Date | string[] | boolean) => {
    setFormData(prev => ({
      ...prev,
      [name]: { value },
    }));
  };

  // 渲染医嘱类型标签
  const renderOrderTypeBadge = (type: string) => {
    const config = ORDER_TYPE_CONFIG[type] || ORDER_TYPE_CONFIG.medication;
    return (
      <Badge variant={config.variant} className="gap-1">
        {config.icon}
        {config.label}
      </Badge>
    );
  };

  // 渲染状态标签
  const renderStatusBadge = (status: string) => {
    const config = STATUS_CONFIG[status] || STATUS_CONFIG.draft;
    return <Badge variant={config.variant}>{config.label}</Badge>;
  };

  // 今日任务概览卡片
  const renderTodayOverview = () => {
    if (!todayTasks) return null;
    const { summary } = todayTasks;
    const percent = Math.round(summary.rate * 100);

    const stats = [
      {
        title: '今日任务',
        value: `${summary.total}`,
        unit: `/ ${summary.completed + summary.overdue}`,
        icon: <Clock className="h-5 w-5" />,
        variant: 'primary' as const,
      },
      {
        title: '完成率',
        value: percent,
        unit: '%',
        icon: null,
        variant: percent >= 80 ? 'success' as const : percent >= 50 ? 'warning' as const : 'danger' as const,
      },
      {
        title: '待完成',
        value: summary.pending,
        icon: null,
        variant: 'primary' as const,
      },
      {
        title: '已超时',
        value: summary.overdue,
        icon: <AlertCircle className="h-5 w-5" />,
        variant: summary.overdue > 0 ? 'danger' as const : 'success' as const,
      },
    ];

    return <StatCardGrid items={stats} cols={4} gap="gap-4" />;
  };

  // 渲染医嘱列表
  const renderOrdersList = () => (
    <Card>
      <CardContent className="p-0">
        <div className="overflow-x-auto">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead className="w-16">ID</TableHead>
                <TableHead className="w-24">类型</TableHead>
                <TableHead>标题</TableHead>
                <TableHead className="w-20">调度</TableHead>
                <TableHead className="w-28">提醒时间</TableHead>
                <TableHead className="w-24">状态</TableHead>
                <TableHead className="w-28">开始日期</TableHead>
                <TableHead className="w-32">操作</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {loading ? (
                <TableRow>
                  <TableCell colSpan={8} className="h-32 text-center text-foreground-secondary">
                    加载中...
                  </TableCell>
                </TableRow>
              ) : orders.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={8} className="h-32 text-center text-foreground-secondary">
                    暂无数据
                  </TableCell>
                </TableRow>
              ) : (
                orders.map((order) => (
                  <TableRow key={order.id}>
                    <TableCell className="text-sm">{order.id}</TableCell>
                    <TableCell>{renderOrderTypeBadge(order.order_type)}</TableCell>
                    <TableCell className="max-w-xs truncate">{order.title}</TableCell>
                    <TableCell className="text-sm text-foreground-secondary">
                      {SCHEDULE_TYPE_MAP[order.schedule_type] || order.schedule_type}
                    </TableCell>
                    <TableCell className="text-sm">
                      {order.reminder_times?.join(', ') || '-'}
                    </TableCell>
                    <TableCell>
                      <div className="flex flex-col gap-1">
                        {renderStatusBadge(order.status)}
                        {order.ai_generated && (
                          <Badge variant="info" className="gap-1 w-fit">
                            <Bot className="h-3 w-3" />
                            AI生成
                          </Badge>
                        )}
                      </div>
                    </TableCell>
                    <TableCell className="text-sm">{order.start_date}</TableCell>
                    <TableCell>
                      <div className="flex items-center gap-1">
                        <Tooltip content="查看详情">
                          <Button
                            variant="ghost"
                            size="icon"
                            className="h-8 w-8"
                            onClick={() => openDetailModal(order)}
                          >
                            <Eye className="h-4 w-4" />
                          </Button>
                        </Tooltip>
                        {order.status === 'draft' && (
                          <>
                            <Tooltip content="编辑">
                              <Button
                                variant="ghost"
                                size="icon"
                                className="h-8 w-8"
                                onClick={() => openEditModal(order)}
                              >
                                <Edit className="h-4 w-4" />
                              </Button>
                            </Tooltip>
                            <Tooltip content="激活医嘱">
                              <Button
                                variant="ghost"
                                size="icon"
                                className="h-8 w-8 text-success hover:text-success"
                                onClick={() => handleActivate(order.id)}
                              >
                                <CheckCircle className="h-4 w-4" />
                              </Button>
                            </Tooltip>
                          </>
                        )}
                        {order.status === 'active' && (
                          <Tooltip content="停用">
                            <Button
                              variant="ghost"
                              size="icon"
                              className="h-8 w-8 text-danger hover:text-danger"
                              onClick={() => toast.info('停用功能开发中')}
                            >
                              <Ban className="h-4 w-4" />
                            </Button>
                          </Tooltip>
                        )}
                      </div>
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </div>
      </CardContent>
    </Card>
  );

  // 渲染任务列表
  const renderTaskList = (tasks: TaskInstance[], title: string, variant: 'default' | 'success' | 'danger') => (
    <Card className="h-full">
      <CardHeader className="py-3 px-4">
        <CardTitle className="text-sm font-medium">
          <Badge variant={variant} className="mb-2">
            {title} ({tasks.length})
          </Badge>
        </CardTitle>
      </CardHeader>
      <CardContent className="p-0">
        <div className="divide-y divide-border">
          {tasks.length === 0 ? (
            <div className="p-4 text-center text-sm text-foreground-secondary">
              无任务
            </div>
          ) : (
            tasks.map((task) => (
              <div key={task.id} className="p-3 hover:bg-surface-alt/50 transition-colors">
                <div className="flex items-start justify-between gap-2">
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium truncate">{task.order_title || '未命名任务'}</p>
                    <p className="text-xs text-foreground-secondary">
                      {task.order_type && ORDER_TYPE_CONFIG[task.order_type]?.label}
                    </p>
                  </div>
                  <span className="text-xs text-foreground-secondary">{task.scheduled_time}</span>
                </div>
              </div>
            ))
          )}
        </div>
      </CardContent>
    </Card>
  );

  // 渲染今日任务
  const renderTodayTasks = () => (
    <>
      {renderTodayOverview()}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Clock className="h-5 w-5" />
            <span>{dayjs().format('YYYY年MM月DD日')} 任务清单</span>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
            {renderTaskList(todayTasks?.pending || [], '待完成', 'default')}
            {renderTaskList(todayTasks?.completed || [], '已完成', 'success')}
            {renderTaskList(todayTasks?.overdue || [], '已超时', 'danger')}
          </div>
        </CardContent>
      </Card>
    </>
  );

  // 表单对话框
  const renderFormDialog = (
    isOpen: boolean,
    onClose: () => void,
    title: string,
    onSubmit: () => void,
    fields: Array<{ key: string; label: string; type: 'text' | 'select' | 'textarea' | 'date' | 'tags'; options?: Array<{ value: string; label: string }> }>,
    submitText: string
  ) => (
    <Dialog open={isOpen} onOpenChange={(open) => !open && onClose()}>
      <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Plus className="h-5 w-5" />
            {title}
          </DialogTitle>
        </DialogHeader>
        <div className="space-y-4 py-4">
          <div className="grid grid-cols-2 gap-4">
            {fields.map((field) => (
              <div key={field.key} className={field.type === 'textarea' || field.type === 'tags' ? 'col-span-2' : ''}>
                <label className="block text-sm font-medium mb-1.5">{field.label}</label>
                {field.type === 'text' && (
                  <Input
                    value={(formData[field.key]?.value as string) || ''}
                    onChange={(e) => updateFormField(field.key, e.target.value)}
                    placeholder={`请输入${field.label}`}
                  />
                )}
                {field.type === 'textarea' && (
                  <Textarea
                    value={(formData[field.key]?.value as string) || ''}
                    onChange={(e) => updateFormField(field.key, e.target.value)}
                    placeholder={`请输入${field.label}`}
                    rows={3}
                  />
                )}
                {field.type === 'select' && (
                  <Select
                    value={(formData[field.key]?.value as string) || ''}
                    onValueChange={(value) => updateFormField(field.key, value)}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder={`请选择${field.label}`} />
                    </SelectTrigger>
                    <SelectContent>
                      {field.options?.map((option) => (
                        <SelectItem key={option.value} value={option.value}>
                          {option.label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                )}
                {field.type === 'date' && (
                  <DatePicker
                    value={(formData[field.key]?.value as Date) || null}
                    onChange={(date) => updateFormField(field.key, date || '')}
                  />
                )}
                {field.type === 'tags' && (
                  <Input
                    value={Array.isArray(formData[field.key]?.value)
                      ? (formData[field.key]?.value as string[]).join(', ')
                      : (formData[field.key]?.value as string) || ''
                    }
                    onChange={(e) => updateFormField(field.key, e.target.value.split(',').map(s => s.trim()).filter(Boolean))}
                    placeholder="输入多个值，用逗号分隔"
                  />
                )}
              </div>
            ))}
          </div>
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={onClose}>
            取消
          </Button>
          <Button onClick={onSubmit}>
            {submitText}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );

  // 医嘱详情
  const renderDetailDialog = () => (
    <Dialog open={detailModalVisible} onOpenChange={(open) => !open && setDetailModalVisible(false)}>
      <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Eye className="h-5 w-5" />
            医嘱详情
          </DialogTitle>
        </DialogHeader>
        {currentOrder && (
          <div className="space-y-4 py-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-1">
                <p className="text-sm text-foreground-secondary">医嘱ID</p>
                <p className="text-sm font-medium">{currentOrder.id}</p>
              </div>
              <div className="space-y-1">
                <p className="text-sm text-foreground-secondary">类型</p>
                {renderOrderTypeBadge(currentOrder.order_type)}
              </div>
              <div className="space-y-1">
                <p className="text-sm text-foreground-secondary">状态</p>
                {renderStatusBadge(currentOrder.status)}
              </div>
              <div className="space-y-1">
                <p className="text-sm text-foreground-secondary">调度类型</p>
                <p className="text-sm font-medium">{SCHEDULE_TYPE_MAP[currentOrder.schedule_type]}</p>
              </div>
              <div className="space-y-1">
                <p className="text-sm text-foreground-secondary">频次</p>
                <p className="text-sm font-medium">{currentOrder.frequency || '-'}</p>
              </div>
              <div className="space-y-1">
                <p className="text-sm text-foreground-secondary">开始日期</p>
                <p className="text-sm font-medium">{currentOrder.start_date}</p>
              </div>
              <div className="space-y-1">
                <p className="text-sm text-foreground-secondary">结束日期</p>
                <p className="text-sm font-medium">{currentOrder.end_date || '未设置'}</p>
              </div>
              <div className="space-y-1 col-span-2">
                <p className="text-sm text-foreground-secondary">提醒时间</p>
                <p className="text-sm font-medium">{currentOrder.reminder_times?.join(', ') || '-'}</p>
              </div>
              <div className="space-y-1 col-span-2">
                <p className="text-sm text-foreground-secondary">标题</p>
                <p className="text-sm font-medium">{currentOrder.title}</p>
              </div>
              <div className="space-y-1 col-span-2">
                <p className="text-sm text-foreground-secondary">详细说明</p>
                <p className="text-sm">{currentOrder.description || '-'}</p>
              </div>
              <div className="space-y-1 col-span-2">
                <p className="text-sm text-foreground-secondary">AI 生成</p>
                {currentOrder.ai_generated ? (
                  <Badge variant="info" className="gap-1">
                    <Bot className="h-3 w-3" />
                    AI 生成
                  </Badge>
                ) : (
                  <Badge variant="secondary">手动创建</Badge>
                )}
              </div>
              <div className="space-y-1">
                <p className="text-sm text-foreground-secondary">创建时间</p>
                <p className="text-sm">{dayjs(currentOrder.created_at).format('YYYY-MM-DD HH:mm')}</p>
              </div>
              <div className="space-y-1">
                <p className="text-sm text-foreground-secondary">更新时间</p>
                <p className="text-sm">{dayjs(currentOrder.updated_at).format('YYYY-MM-DD HH:mm')}</p>
              </div>
            </div>
          </div>
        )}
        <DialogFooter>
          <Button variant="outline" onClick={() => setDetailModalVisible(false)}>
            关闭
          </Button>
          {currentOrder?.status === 'draft' && (
            <Button
              onClick={() => {
                if (currentOrder) {
                  handleActivate(currentOrder.id);
                  setDetailModalVisible(false);
                }
              }}
            >
              <CheckCircle className="h-4 w-4 mr-2" />
              激活医嘱
            </Button>
          )}
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );

  // 创建医嘱表单字段
  const createFormFields = [
    { key: 'order_type', label: '医嘱类型', type: 'select' as const, options: [
      { value: 'medication', label: '用药' },
      { value: 'monitoring', label: '监测' },
      { value: 'behavior', label: '行为' },
      { value: 'followup', label: '复诊' },
    ]},
    { key: 'schedule_type', label: '调度类型', type: 'select' as const, options: [
      { value: 'once', label: '一次性' },
      { value: 'daily', label: '每日' },
      { value: 'weekly', label: '每周' },
      { value: 'custom', label: '自定义' },
    ]},
    { key: 'title', label: '医嘱标题', type: 'text' as const },
    { key: 'description', label: '详细说明', type: 'textarea' as const },
    { key: 'start_date', label: '开始日期', type: 'date' as const },
    { key: 'end_date', label: '结束日期', type: 'date' as const },
    { key: 'frequency', label: '频次', type: 'text' as const },
    { key: 'reminder_times', label: '提醒时间（逗号分隔）', type: 'tags' as const },
    { key: 'ai_generated', label: 'AI 生成', type: 'select' as const, options: [
      { value: 'false', label: '手动创建' },
      { value: 'true', label: 'AI 生成' },
    ]},
  ];

  // 编辑医嘱表单字段
  const editFormFields = [
    { key: 'title', label: '医嘱标题', type: 'text' as const },
    { key: 'description', label: '详细说明', type: 'textarea' as const },
    { key: 'end_date', label: '结束日期', type: 'date' as const },
    { key: 'frequency', label: '频次', type: 'text' as const },
    { key: 'reminder_times', label: '提醒时间（逗号分隔）', type: 'tags' as const },
  ];

  return (
    <div className="space-y-6">
      {/* 页面头部 */}
      <PageHeader
        title="医嘱执行监督"
        description="管理患者医嘱、查看执行情况和任务列表"
        actions={
          <div className="flex items-center gap-2">
            <Select
              value={statusFilter}
              onValueChange={setStatusFilter}
            >
              <SelectTrigger className="w-[120px]">
                <SelectValue placeholder="筛选状态" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="">全部</SelectItem>
                <SelectItem value="draft">草稿</SelectItem>
                <SelectItem value="active">进行中</SelectItem>
                <SelectItem value="completed">已完成</SelectItem>
                <SelectItem value="stopped">已停用</SelectItem>
              </SelectContent>
            </Select>
            <Button onClick={() => setCreateModalVisible(true)}>
              <Plus className="h-4 w-4 mr-2" />
              新建医嘱
            </Button>
          </div>
        }
      />

      {/* Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab} defaultValue="orders">
        <TabsList>
          <TabsTrigger value="orders">
            医嘱列表 ({orders.length})
          </TabsTrigger>
          <TabsTrigger value="tasks">
            今日任务
          </TabsTrigger>
        </TabsList>

        <TabsContent value="orders" className="mt-4">
          {renderOrdersList()}
        </TabsContent>

        <TabsContent value="tasks" className="mt-4">
          {renderTodayTasks()}
        </TabsContent>
      </Tabs>

      {/* 创建医嘱弹窗 */}
      {renderFormDialog(
        createModalVisible,
        () => setCreateModalVisible(false),
        '新建医嘱',
        handleCreate,
        createFormFields,
        '创建'
      )}

      {/* 编辑医嘱弹窗 */}
      {renderFormDialog(
        editModalVisible,
        () => {
          setEditModalVisible(false);
          setCurrentOrder(null);
        },
        '编辑医嘱',
        handleUpdate,
        editFormFields,
        '保存'
      )}

      {/* 医嘱详情弹窗 */}
      {renderDetailDialog()}
    </div>
  );
};

export default MedicalOrders;
